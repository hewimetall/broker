import os

import aio_pika
QNAME = 'ping_pong'


def get_queue_name(queue=None):
    return queue or os.getenv('RABBITMQ_QUEUE', QNAME)


def get_connection_kwargs():
    return {
        'host': os.getenv('RABBITMQ_HOST', 'localhost'),
        'port': int(os.getenv('RABBITMQ_PORT', '5672')),
        'login': os.getenv('RABBITMQ_USERNAME', 'user'),
        'password': os.getenv('RABBITMQ_PASSWORD', 'passwd'),
    }


async def connect():
    return await aio_pika.connect(**get_connection_kwargs())


async def sender(queue=None, body=b"Hello World!"):
    """ Занимается отправкое сообщения (Producing) """
    queue_name = get_queue_name(queue)
    message_body = body.encode() if isinstance(body, str) else body
    # connect принимает строку url:"amqp://guest:guest@localhost/"
    # connect по умолчанию  без параметров подключается к локалхосту с дефолтным  настройками.
    async with await connect() as conn:
        # Перед выходом из программы нам нужно убедиться, что сетевые буферы очищены и наше сообщение действительно доставлено в RabbitMQ
        # Мы можем сделать это, аккуратно закрыв соединение.
        # В этом примере использовался асинхронный менеджер контекста
        # Но можно вызвать метод close() для подключения.
        channel = await conn.channel()
        # Декларируем очередь
        queue = await channel.declare_queue(queue_name)
        await channel.default_exchange.publish(
            message=aio_pika.Message(message_body),
            routing_key=queue.name,
        )

        print(f" [x] Sent {message_body!r}")
        return message_body


async def receiver_simple(no_ack=True, queue=None):
    queue_name = get_queue_name(queue)
    async with await connect() as conn:
        channel = await conn.channel()
        # Декларируем очередь
        queue = await channel.declare_queue(queue_name)
        # Параметр no_ack отвечает за удаления сообщения из очереди.
        # no_ack = True удаляет
        # no_ack = False нет
        try:
            message = await queue.get(no_ack=no_ack)
        except aio_pika.exceptions.QueueEmpty:
            # Возникает в случае если очередь пуста.
            print("Query is Empty")
            return None
        else:
            print(message.body)
            return message

async def callback_async(message: aio_pika.abc.AbstractIncomingMessage):
    print("async", message.body)

def callback_sync(message: aio_pika.abc.AbstractIncomingMessage):
    print("sync", message.body)

async def receiver_callback(callback=callback_sync, queue=None):
    queue_name = get_queue_name(queue)
    async with await connect() as conn:
        channel = await conn.channel()
        # Декларируем очередь
        queue = await channel.declare_queue(queue_name)
        # регистрация получателя также удаления сообщения из очереди.
        consumer_tag = await queue.consume(callback=callback, no_ack=True)
        return consumer_tag
