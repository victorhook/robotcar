import hashlib
import os
import socket
import struct

from utils import FlashProtocol

INT_SIZE = struct.calcsize('I')


class Flasher:

    TIMEOUT = .1
    BUFF_SIZE = 1024

    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._sock = None
        self._callback = None

    def start(self, callback):
        self._callback = callback
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._ip, self._port))

    def _send_byte(self, data):
        self._sock.send(struct.pack('B', data))

    def _read_byte(self):
        return struct.unpack('B', self._sock.recv(1))[0]

    # Wrapper for flashing multiple files
    def flash_multiple_files(self, files):
        self._send_byte(FlashProtocol.FLASH_START)
        results = {}
        for file_name in files:
            res = self._flash_one_file(file_name)
            results[file_name] = res
        return results

    # Wrapper to send a single file
    def flash_one_file(self, file_name):
        self._send_byte(FlashProtocol.FLASH_START)
        return self._flash_one_file(file_name)

    def _flash_one_file(self, file_name):
        self._send_byte(FlashProtocol.FLASH_NEW_FILE)

        con = self._sock.makefile('wb')
        size = os.stat(file_name)[6]

        con.write(struct.pack('I', len(file_name)))
        con.write(struct.pack('I', size))
        con.write(file_name.encode('utf-8'))

        with open(file_name, 'rb') as f:
            data = f.read()
            md5 = hashlib.md5(data)
            md5sum = md5.digest()
            con.write(md5sum)
            con.write(data)
            con.flush()

        result = self._read_byte()
        return result
        return ''

    def list_files(self):
        self._send_byte(FlashProtocol.LIST_FILES_START)
        command = self._read_byte()

        files = []
        while command != FlashProtocol.LIST_FILES_EXIT:
            name_len = struct.unpack('I', self._sock.recv(INT_SIZE))[0]
            filename = self._sock.recv(name_len)
            files.append(filename.decode('utf-8'))
            command = self._read_byte()

        print(files)

    def close(self):
        try:
            self._send_byte(FlashProtocol.FLASH_EXIT)
            self._sock.close()
        except OSError:
            self._callback('Failed when closing socket')



if __name__ == '__main__':

    ip = '127.0.0.1'
    port = 1996

    file_name = 'coolfile.txt'

    flasher = Flasher(ip, port)
    flasher.start(lambda msg: print(msg))
    res = flasher.flash_multiple_files([file_name, 'tmpf'])
    #flasher.list_files()
    flasher.close()



