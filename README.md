# Тестирования брокера сообщений в разных режимах работы python.
    * sync `pika`
    * async `aio_pika`

# при создании очередей в rebitmq
 * exclusive - Связывает очередь с одним потребителем. Если он уходит то очередь удаляется со всеми данными.
 * auto-delete - Пока существуют потребители существует очередь. Как только последний потребитель отписался очерередь удаляется.
