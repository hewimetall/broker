import unittest
import sync
import asyncb
import asyncio

class SyncTest(unittest.TestCase):
    # def test_ping_pong(self):
    #     sync.sender()
    #     sync.receiver_simple(True)
    #
    # def test_ask(self):
    #     sync.sender()
    #     sync.receiver_simple(False)
    #     sync.receiver_simple(True)
    #
    # def test_consumer(self):
    #     sync.sender()
    #     sync.receiver_callback(False)
    #     sync.receiver_callback(True)

    def test_quure_auto_delete(self):
        sync.sender(auto_delete=False,queue="test12")
        sync.sender(auto_delete=False,queue="test12")
        sync.sender(auto_delete=False,queue="test12")
        sync.sender(auto_delete=False,queue="test12")
        sync.receiver_no_declarate_queue(auto_ack=True,queue='test12')
        sync.receiver_no_declarate_queue(auto_ack=True,queue='test12')

loop = asyncio.get_event_loop()

# class AsyncTest(unittest.TestCase):
#     def test_ping_pong(self):
#         print("Ping pong:")
#         loop.run_until_complete(asyncb.sender())
#         loop.run_until_complete(asyncb.receiver_simple())
#
#     def test_ask(self):
#         print("ASK:")
#         loop.run_until_complete(asyncb.sender())
#         # получает данные без ответа сервису.
#         # Данные не исчезают из очереди
#         loop.run_until_complete(asyncb.receiver_simple(False))
#         # получает данные с ответом сервису.
#         # Данные исчезают из очереди
#         loop.run_until_complete(asyncb.receiver_simple(True))
#         # Тк очередь пуста выбрасывается исключения QueryEmpty.
#         loop.run_until_complete(asyncb.receiver_simple(True))
#
#     def test_callback(self):
#         loop.run_until_complete(asyncb.sender())
#         loop.run_until_complete(asyncb.receiver_callback(asyncb.callback_async))
#         loop.run_until_complete(asyncb.sender())
#         loop.run_until_complete(asyncb.receiver_callback(asyncb.callback_sync))

if __name__ == '__main__':
    unittest.main()
