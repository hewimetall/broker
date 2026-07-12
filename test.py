from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import asyncb
import sync


class FakeSyncChannel:
    def __init__(self, message=None):
        self.message = message or (SimpleNamespace(NAME="GetOk"), object(), b"payload")
        self.queue_declare = Mock()
        self.basic_publish = Mock()
        self.basic_get = Mock(return_value=self.message)
        self.basic_consume = Mock()
        self.start_consuming = Mock()
        self.stop_consuming = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeSyncConnection:
    def __init__(self, channel):
        self._channel = channel
        self.close = Mock()

    def channel(self):
        return self._channel


def install_sync_connection(monkeypatch, channel):
    connection = FakeSyncConnection(channel)
    monkeypatch.setattr(sync, "create_connection", Mock(return_value=connection))
    return connection


def test_sync_connection_parameters_use_environment(monkeypatch):
    monkeypatch.setenv("RABBITMQ_HOST", "rabbit.local")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("RABBITMQ_USERNAME", "guest")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "secret")

    parameters = sync.get_connection_parameters()

    assert parameters.host == "rabbit.local"
    assert parameters.port == 5673
    assert parameters.credentials.username == "guest"
    assert parameters.credentials.password == "secret"


def test_sync_sender_declares_and_publishes(monkeypatch):
    channel = FakeSyncChannel()
    connection = install_sync_connection(monkeypatch, channel)

    body = sync.sender(queue="jobs", auto_delete=True, body="work")

    assert body == "work"
    channel.queue_declare.assert_called_once_with(queue="jobs", auto_delete=True)
    channel.basic_publish.assert_called_once_with(
        exchange="",
        body="work",
        routing_key="jobs",
    )
    connection.close.assert_called_once_with()


def test_sync_receiver_without_declaration_reads_from_queue(monkeypatch):
    message = (None, None, None)
    channel = FakeSyncChannel(message=message)
    connection = install_sync_connection(monkeypatch, channel)

    result = sync.receiver_no_declarate_queue(auto_ack=False, queue="events")

    assert result == message
    channel.basic_get.assert_called_once_with(queue="events", auto_ack=False)
    channel.queue_declare.assert_not_called()
    connection.close.assert_called_once_with()


def test_sync_receiver_simple_declares_before_read(monkeypatch):
    channel = FakeSyncChannel()
    install_sync_connection(monkeypatch, channel)

    result = sync.receiver_simple(auto_ack=True, queue="events")

    assert result == channel.message
    channel.queue_declare.assert_called_once_with(queue="events")
    channel.basic_get.assert_called_once_with(queue="events", auto_ack=True)


def test_sync_receiver_callback_registers_consumer(monkeypatch):
    channel = FakeSyncChannel()
    install_sync_connection(monkeypatch, channel)
    callback = Mock()

    sync.receiver_callback(auto_ack=False, queue="callbacks", on_message_callback=callback)

    channel.queue_declare.assert_called_once_with(queue="callbacks")
    channel.basic_consume.assert_called_once_with(
        queue="callbacks",
        on_message_callback=callback,
        auto_ack=False,
    )
    channel.start_consuming.assert_called_once_with()


def test_sync_callback_stops_consuming(capsys):
    channel = FakeSyncChannel()
    method = SimpleNamespace(NAME="Deliver")

    sync.callback(channel, method, object(), b"payload")

    channel.stop_consuming.assert_called_once_with()
    assert "Deliver" in capsys.readouterr().out


class FakeAsyncExchange:
    def __init__(self):
        self.published = []

    async def publish(self, message, routing_key):
        self.published.append((message, routing_key))


class FakeAsyncQueue:
    def __init__(self, name="queue", message=None, raises_empty=False):
        self.name = name
        self.message = message or SimpleNamespace(body=b"payload")
        self.raises_empty = raises_empty
        self.get_calls = []
        self.consume_calls = []

    async def get(self, no_ack):
        self.get_calls.append(no_ack)
        if self.raises_empty:
            raise asyncb.aio_pika.exceptions.QueueEmpty
        return self.message

    async def consume(self, callback, no_ack):
        self.consume_calls.append((callback, no_ack))
        return "consumer-tag"


class FakeAsyncChannel:
    def __init__(self, queue):
        self.queue = queue
        self.default_exchange = FakeAsyncExchange()
        self.declared = []

    async def declare_queue(self, name):
        self.declared.append(name)
        self.queue.name = name
        return self.queue


class FakeAsyncConnection:
    def __init__(self, channel):
        self._channel = channel
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self.exited = True
        return False

    async def channel(self):
        return self._channel


def install_async_connection(monkeypatch, channel):
    connection = FakeAsyncConnection(channel)

    async def fake_connect():
        return connection

    monkeypatch.setattr(asyncb, "connect", fake_connect)
    return connection


def test_async_connection_kwargs_use_environment(monkeypatch):
    monkeypatch.setenv("RABBITMQ_HOST", "rabbit.local")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("RABBITMQ_USERNAME", "guest")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "secret")

    assert asyncb.get_connection_kwargs() == {
        "host": "rabbit.local",
        "port": 5673,
        "login": "guest",
        "password": "secret",
    }


@pytest.mark.asyncio
async def test_async_sender_declares_and_publishes(monkeypatch):
    queue = FakeAsyncQueue()
    channel = FakeAsyncChannel(queue)
    connection = install_async_connection(monkeypatch, channel)

    body = await asyncb.sender(queue="jobs", body="work")

    assert body == b"work"
    assert channel.declared == ["jobs"]
    assert channel.default_exchange.published[0][0].body == b"work"
    assert channel.default_exchange.published[0][1] == "jobs"
    assert connection.entered is True
    assert connection.exited is True


@pytest.mark.asyncio
async def test_async_receiver_simple_returns_message(monkeypatch):
    queue = FakeAsyncQueue(message=SimpleNamespace(body=b"payload"))
    channel = FakeAsyncChannel(queue)
    install_async_connection(monkeypatch, channel)

    result = await asyncb.receiver_simple(no_ack=False, queue="events")

    assert result.body == b"payload"
    assert channel.declared == ["events"]
    assert queue.get_calls == [False]


@pytest.mark.asyncio
async def test_async_receiver_simple_returns_none_for_empty_queue(monkeypatch, capsys):
    queue = FakeAsyncQueue(raises_empty=True)
    channel = FakeAsyncChannel(queue)
    install_async_connection(monkeypatch, channel)

    result = await asyncb.receiver_simple(no_ack=True, queue="events")

    assert result is None
    assert "Query is Empty" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_async_receiver_callback_registers_consumer(monkeypatch):
    queue = FakeAsyncQueue()
    channel = FakeAsyncChannel(queue)
    install_async_connection(monkeypatch, channel)
    callback = Mock()

    result = await asyncb.receiver_callback(callback=callback, queue="callbacks")

    assert result == "consumer-tag"
    assert queue.consume_calls == [(callback, True)]


@pytest.mark.asyncio
async def test_async_callbacks_print_message(capsys):
    message = SimpleNamespace(body=b"payload")

    await asyncb.callback_async(message)
    asyncb.callback_sync(message)

    output = capsys.readouterr().out
    assert "async b'payload'" in output
    assert "sync b'payload'" in output
