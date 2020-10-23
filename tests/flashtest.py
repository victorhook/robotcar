import os
import sys
import threading
import unittest
from urllib.request import urlopen
BASE = '/home/victor/coding/python/robotcar/'
sys.path.append(BASE + 'src/')
sys.path.append(BASE + 'tools/')
from flashhandler import FlashHandler   # noqa
from flasher import Flasher             # noqa
from utils import FlashProtocol         # noqa

IP = '127.0.0.1'
PORT = 1996


class FlashTest(unittest.TestCase):

    def setUp(self):

        self.server = FlashHandler(IP, PORT)
        self.client = Flasher(IP, PORT)
        self.server.start(lambda msg: print(msg))
        self.client.start(lambda msg: print(msg))

        # Create some default data
        base = 'tmp-test-dir/'
        self.file = base + 'test-file.txt'
        if not os.path.exists(base):
            os.mkdir(base)
        with urlopen('https://loremipsum.io/') as r:
            with open(self.file, 'wb') as f:
                f.write(r.read())

    def tearDown(self):
        self.server.close()
        self.client.close()

    def _server_serve(self):
        while not self.server.is_connected():
            self.server.poll()

    def test_flash_one_file(self):
        server_task = threading.Thread(target=self._server_serve)
        server_task.start()
        res = self.client.flash_one_file(self.file)
        self.client.close()
        server_task.join()

        self.assertEqual(res, FlashProtocol.FILE_OK)


if __name__ == '__main__':
    unittest.main()
