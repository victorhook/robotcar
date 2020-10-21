import hashlib
import os
import socket
import struct
import sys
sys.path.append('/home/victor/coding/python/robotcar/tools/')
from utils import FlashProtocol      # noqa


ip = '127.0.0.1'
port = 1996
INT_SIZE = struct.calcsize('I')
MD5SUM_LEN = 16


class Flasher:

    TIMEOUT = .1
    BUFF_SIZE = 1024

    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._sock = None
        self._con = None
        self._callback = None
        self._connected = False

    def start(self, callback):
        self._callback = callback
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self._ip, self._port))
        self._sock.listen(0)
        self._sock.settimeout(self.TIMEOUT)

    def is_connected(self):
        return self._connected

    def poll(self):
        try:
            self._con = self._sock.accept()[0]
            self._connected = True
            command = self._read_byte()
            if command == FlashProtocol.FLASH_START:
                self._start_flash()
            elif command == FlashProtocol.LIST_FILES_START:
                self._list_files()
        except OSError:
            pass         # Timeout

    def close(self):
        try:
            self._sock.close()
            self._connected = False
        except OSError:
            self._callback('Failed when closing socket')

    def _list_files(self):
        files = [stat[0] for stat in os.ilistdir()
                 if stat[0] != '.' and stat[0] != '..']
        con = self._con
        for f in files:
            self._send_byte(FlashProtocol.NEW_FILE_NAME)
            con.write(struct.pack('I', len(f)))
            con.write(f.encode('utf-8'))

        self._send_byte(FlashProtocol.LIST_FILES_EXIT)

    def _start_flash(self):
        flashing = self._read_byte() == FlashProtocol.FLASH_NEW_FILE
        print(flashing)
        while flashing:
            self._flash_one_file()
            flashing = self._read_byte() == FlashProtocol.FLASH_NEW_FILE

    def _read_byte(self):
        return struct.unpack('B', self._con.read(1))[0]

    def _send_byte(self, data):
        self._con.write(struct.pack('B', data))

    def _flash_one_file(self):
        con = self._con

        # Read file-name-size and file-size
        file_name_len = con.recv(INT_SIZE)
        file_len = con.recv(INT_SIZE)
        # Convert to ints
        file_name_len = struct.unpack('I', file_name_len)[0]
        file_len = struct.unpack('I', file_len)[0]
        # Read file-name
        file_name = con.recv(file_name_len).decode('utf-8')
        tmp_file_name = 'tmp' + file_name

        # Read md5sum of file
        compsum = con.recv(MD5SUM_LEN)

        # Create temporary file and prepare md5 count
        buff_size = self.BUFF_SIZE
        tmp_file = open(tmp_file_name, 'wb')
        count = 0
        md5 = hashlib.md5()

        # Read in entire content from strema and write it to the temp file
        while count < file_len:
            data = con.recv(buff_size)
            tmp_file.write(data)
            md5.update(data)
            count += buff_size

        tmp_file.close()
        md5sum = md5.digest()

        if compsum == md5sum:
            self._send_byte(FlashProtocol.FILE_OK)
        else:
            # Inform sender there's something wrong with the file and
            # emit calback
            self._send_byte(FlashProtocol.FILE_NOT_OK)
            self._callback(FlashProtocol.FILE_NOT_OK)
            return

        # Write to new file
        tmp_file = open(tmp_file_name, 'rb')
        with open(file_name, 'wb') as f:
            tmp_file.seek(0)
            data = True
            while data:
                data = tmp_file.read(buff_size)
                f.write(data)

        os.remove(tmp_file_name)
        self._callback(FlashProtocol.FILE_OK)


flasher = Flasher(ip, port)
flasher.start(lambda msg: print(msg))
while not flasher.is_connected():
    flasher.poll()

flasher.close()
