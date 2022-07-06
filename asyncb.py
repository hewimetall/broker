import asyncio

import aio_pika
QNAME = 'ping_pong'


async def sender(queue=QNAME):
    """ Занимается отправкое сообщения (Producing) """
    # connect принимает строку url:"amqp://guest:guest@localhost/"
    # connect по умолчанию  без параметров подключается к локалхосту с дефолтным  настройками.
    async with await aio_pika.connect(password='passwd', login='user') as conn:
        # Перед выходом из программы нам нужно убедиться, что сетевые буферы очищены и наше сообщение действительно доставлено в RabbitMQ
        # Мы можем сделать это, аккуратно закрыв соединение.
        # В этом примере использовался асинхронный менеджер контекста
        # Но можно вызвать метод close() для подключения.
        channel = await conn.channel()
        # Декларируем очередь
        queue = await channel.declare_queue(queue)
        await channel.default_exchange.publish(
            message=aio_pika.Message(b"Hello World!"),
            routing_key=queue.name,
        )

        print(" [x] Sent 'Hello World!'")

async def receiver_simple(no_ack=True):
    async with await aio_pika.connect(password='passwd', login='user') as conn:
        channel = await conn.channel()
        # Декларируем очередь
        queue = await channel.declare_queue(QNAME)
        # Параметр no_ack отвечает за удаления сообщения из очереди.
        # no_ack = True удаляет
        # no_ack = False нет
        try:
            message = await queue.get(no_ack=no_ack)
        except asyncio.QueueEmpty:
            # Возникает в случае если очередь пуста.
            print("Query is Empty")
        else:
            print(message.body)

async def callback_async(message: aio_pika.abc.AbstractIncomingMessage):
    print("async",message.body)

def callback_sync(message: aio_pika.abc.AbstractIncomingMessage):
    print("sync", message.body)

async def receiver_callback(callback=callback_sync):
    async with await aio_pika.connect(password='passwd', login='user') as conn:
        channel = await conn.channel()
        # Декларируем очередь
        queue = await channel.declare_queue(QNAME)
        # регистрация получателя также удаления сообщения из очереди.
        await queue.consume(callback=callback, no_ack=True)
