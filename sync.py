import pika

QNAME = 'ping_pong'


def sender(queue=QNAME, auto_delete=False):
    """ Занимается отправкое сообщения (Producing) """
    # создаем подключения
    # Для подключения по url pika.URLParameters('url')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost', credentials=pika.PlainCredentials(username='user',
                                                                                 password='passwd')))
    # Создаем подключения.
    # Для того чтобы точно всё ушло нужно его закрыть.
    with connection.channel() as channel:
        # Если не исполовать менеджер, то нужно вызвать метод close у объекта channel.
        # Для того чтобы все данные точно отправились сразу а не валялись в кеши.
        # Проверяем на существования очередь. Если нет, то она создаться.
        #  * exclusive - Связывает очередь с одним потребителем. Если он уходит то очередь удаляется со всеми данными.
        #  * auto-delete - Пока существуют потребители существует очередь. Как только последний потребитель отписался очерередь удаляется.
        channel.queue_declare(queue=queue, auto_delete=False)
        # Отправка данных в очередь.
        # routing_key = ключ для отправки
        # Параметр exchange -- имя обменика.
        # Пустая строка обозначает обмен по умолчанию или безымянный
        # Тоесть сообщения направляются в очередь с именем, указанным в routing_key , если оно существует.
        channel.basic_publish(exchange='',
                              body="ping",
                              routing_key=queue)
        print(" [x] Sent 'Hello World!'")

    # Перед выходом из программы нам нужно убедиться, что сетевые буферы очищены и наше сообщение действительно доставлено в RabbitMQ
    # Мы можем сделать это, аккуратно закрыв соединение
    # Если не вызвать, то во первых не все данные могут уйти.
    # Во вторых. Тк для соедениния по умолчанию исползуется один и тоже значения сокета.
    # Что приведет к невозможности создания повторного соединения.
    connection.close()


def receiver_no_declarate_queue(auto_ack=True, queue=QNAME):
    # Пример получения данных из очереди без декларации.
    # В случае если очереди нет то:
    # message = (None, None, None). Как и в случаи с пустой очередью.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost', credentials=pika.PlainCredentials(username='user',
                                                                                 password='passwd')))
    # Открываем соединения.
    with connection.channel() as channel:
        mesage: tuple = channel.basic_get(queue=queue, auto_ack=auto_ack)
        get_info, properties, body = mesage
        print(f" [x] Received {body} status message is {getattr(get_info, 'NAME', None)}")
    connection.close()


def receiver_simple(auto_ack=True):
    """ Получает сообщения из очереди c помощью вызова get"""
    # создаем подключения
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost', credentials=pika.PlainCredentials(username='user',
                                                                                 password='passwd')))
    # Открываем соединения.
    with connection.channel() as channel:
        # Проверяем на существования очередь. Если нет, то она создаться.
        channel.queue_declare(queue=QNAME)
        # Базовый способ получить сообщения.
        # у него есть параметр auto_ack отвечающий нужно ли подверждать получения.
        # При auto_ack=False сообщения не удалиться из очереди.
        mesage: tuple = channel.basic_get(queue=QNAME, auto_ack=auto_ack)
        # message состоит из 3 параметров
        # 1. Используемый метод для получения данных  pika.spec.Basic.[GetOk, GetEmpty] |None
        # 2. Имформация о доставки pika.BasicProperties |None
        # 3. Сообщения типа bytes | None
        get_info, properties, body = mesage
        print(f" [x] Received {body} status message is {getattr(get_info, 'NAME', None)}")
    connection.close()


def callback(ch, method, properties, body):
    print(f" [x] Received {body} status message is {getattr(method, 'NAME', None)}")
    # Тк это синхронный режим то нужно закрыть канал для того чтобы всё было ок
    # Без вызова будет работать бесконечно
    ch.stop_consuming()


def receiver_callback(auto_ack=True):
    """ Получает сообщения из очереди c помощью dsp get"""
    # создаем подключения
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost', credentials=pika.PlainCredentials(username='user',
                                                                                 password='passwd')))
    # Открываем соединения.
    with connection.channel() as channel:
        # Проверяем на существования очередь. Если нет, то она создаться.
        channel.queue_declare(queue=QNAME)
        # Устанвливаем связь между очередью и функцией обработки
        # На одну очередь один обработчик.
        channel.basic_consume(queue=QNAME, on_message_callback=callback)
        # Запуск цыкла сбора
        # Будет работать пока не будет вызван channel.stop_consuming. Блокирует весь поток выполнения.
        # Остановить можно вызвав stop_consuming в calback функциях.
        channel.start_consuming()
    connection.close()
