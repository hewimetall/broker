import os

import pika

QNAME = 'ping_pong'


def get_queue_name(queue=None):
    return queue or os.getenv('RABBITMQ_QUEUE', QNAME)


def get_connection_parameters():
    credentials = pika.PlainCredentials(
        username=os.getenv('RABBITMQ_USERNAME', 'user'),
        password=os.getenv('RABBITMQ_PASSWORD', 'passwd'),
    )
    return pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST', 'localhost'),
        port=int(os.getenv('RABBITMQ_PORT', '5672')),
        credentials=credentials,
    )


def create_connection():
    return pika.BlockingConnection(get_connection_parameters())


def sender(queue=None, auto_delete=False, body="ping"):
    """ Занимается отправкое сообщения (Producing) """
    queue_name = get_queue_name(queue)
    # создаем подключения
    # Для подключения по url pika.URLParameters('url')
    connection = create_connection()
    # Создаем подключения.
    # Для того чтобы точно всё ушло нужно его закрыть.
    try:
        with connection.channel() as channel:
            # Если не исполовать менеджер, то нужно вызвать метод close у объекта channel.
            # Для того чтобы все данные точно отправились сразу а не валялись в кеши.
            # Проверяем на существования очередь. Если нет, то она создаться.
            #  * exclusive - Связывает очередь с одним потребителем. Если он уходит то очередь удаляется со всеми данными.
            #  * auto-delete - Пока существуют потребители существует очередь. Как только последний потребитель отписался очерередь удаляется.
            channel.queue_declare(queue=queue_name, auto_delete=auto_delete)
            # Отправка данных в очередь.
            # routing_key = ключ для отправки
            # Параметр exchange -- имя обменика.
            # Пустая строка обозначает обмен по умолчанию или безымянный
            # Тоесть сообщения направляются в очередь с именем, указанным в routing_key , если оно существует.
            channel.basic_publish(exchange='',
                                  body=body,
                                  routing_key=queue_name)
            print(f" [x] Sent {body!r}")
            return body
    finally:
        # Перед выходом из программы нам нужно убедиться, что сетевые буферы очищены и наше сообщение действительно доставлено в RabbitMQ
        # Мы можем сделать это, аккуратно закрыв соединение
        # Если не вызвать, то во первых не все данные могут уйти.
        # Во вторых. Тк для соедениния по умолчанию исползуется один и тоже значения сокета.
        # Что приведет к невозможности создания повторного соединения.
        connection.close()


def receiver_no_declarate_queue(auto_ack=True, queue=None):
    # Пример получения данных из очереди без декларации.
    # В случае если очереди нет то:
    # message = (None, None, None). Как и в случаи с пустой очередью.
    queue_name = get_queue_name(queue)
    connection = create_connection()
    # Открываем соединения.
    try:
        with connection.channel() as channel:
            message: tuple = channel.basic_get(queue=queue_name, auto_ack=auto_ack)
            get_info, properties, body = message
            print(f" [x] Received {body} status message is {getattr(get_info, 'NAME', None)}")
            return message
    finally:
        connection.close()


def receiver_simple(auto_ack=True, queue=None):
    """ Получает сообщения из очереди c помощью вызова get"""
    queue_name = get_queue_name(queue)
    # создаем подключения
    connection = create_connection()
    # Открываем соединения.
    try:
        with connection.channel() as channel:
            # Проверяем на существования очередь. Если нет, то она создаться.
            channel.queue_declare(queue=queue_name)
            # Базовый способ получить сообщения.
            # у него есть параметр auto_ack отвечающий нужно ли подверждать получения.
            # При auto_ack=False сообщения не удалиться из очереди.
            message: tuple = channel.basic_get(queue=queue_name, auto_ack=auto_ack)
            # message состоит из 3 параметров
            # 1. Используемый метод для получения данных  pika.spec.Basic.[GetOk, GetEmpty] |None
            # 2. Имформация о доставки pika.BasicProperties |None
            # 3. Сообщения типа bytes | None
            get_info, properties, body = message
            print(f" [x] Received {body} status message is {getattr(get_info, 'NAME', None)}")
            return message
    finally:
        connection.close()


def callback(ch, method, properties, body):
    print(f" [x] Received {body} status message is {getattr(method, 'NAME', None)}")
    # Тк это синхронный режим то нужно закрыть канал для того чтобы всё было ок
    # Без вызова будет работать бесконечно
    ch.stop_consuming()


def receiver_callback(auto_ack=True, queue=None, on_message_callback=callback):
    """ Получает сообщения из очереди c помощью dsp get"""
    queue_name = get_queue_name(queue)
    # создаем подключения
    connection = create_connection()
    # Открываем соединения.
    try:
        with connection.channel() as channel:
            # Проверяем на существования очередь. Если нет, то она создаться.
            channel.queue_declare(queue=queue_name)
            # Устанвливаем связь между очередью и функцией обработки
            # На одну очередь один обработчик.
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message_callback,
                auto_ack=auto_ack,
            )
            # Запуск цыкла сбора
            # Будет работать пока не будет вызван channel.stop_consuming. Блокирует весь поток выполнения.
            # Остановить можно вызвав stop_consuming в calback функциях.
            channel.start_consuming()
    finally:
        connection.close()
