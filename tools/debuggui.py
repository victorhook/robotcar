import re
import tkinter as tk
import threading
import serial
import queue


INIT = [
    'import gc',
    'gc.collect()',
    'from nrf24l01 import NRF24L01',
    'nrf = NRF24L01(ce=2, csn=14)'
]

DE_INIT = [
    'nrf.close()'
]


class MainWindow(tk.Tk):

    def __init__(self, mcu):
        tk.Tk.__init__(self)
        self.frame = tk.Frame(self)
        self.mcu = mcu

        self.reg_frame = tk.Frame(self.frame)

        self.regs = self.get_regs(self.reg_frame)
        self.consol = self.Consol(self.mcu, self.frame, self)
        self.buttons = self.Connector(self.mcu, self.frame)
        self.fileholder = self.FileHolder(self.mcu, self.frame)

        self.queue = queue.Queue()

        self.reg_frame.pack()
        self.frame.pack()
        self.task_running = False

    def get_regs(self, frame):
        regs = []
        for reg in range(0x17):
            regs.append(self.Register(reg, frame))
        return regs

    def read_regs(self):
        self._new_task(self._read_regs)

    def read_files(self):
        self._new_task(self.fileholder.read_files)

    def _task_done(self):
        if not self.queue.empty():
            self.queue.get().start()
        else:
            self.task_running = False

    def _new_task(self, function):
        task = threading.Thread(target=function, args=(self._task_done, ))
        if self.queue.empty() and not self.task_running:
            self.task_running = True
            task.start()
        else:
            self.queue.put(task)

    def _read_regs(self, cb):
        for reg in self.regs:
            value = self.mcu.write('nrf._read_reg(%s)' % reg.reg)
            reg.set_val(int(value))
        cb()

    from bitstring import BitArray
    BitArray(length=8)

    class Connector:

        def __init__(self, mcu, frame):
            self.frame = tk.Frame(frame)
            self.connect = tk.Button(self.frame, text="Connect", command=self._connect)
            self.disconnect = tk.Button(self.frame, text="Disconnect", command=self._disconnect)
            self.reset = tk.Button(self.frame, text="Reset", command=self._reset)
            self.ping = tk.Button(self.frame, text="Ping", command=self._ping)

            self.connect.grid(row=0, column=0)
            self.disconnect.grid(row=0, column=1)
            self.reset.grid(row=0, column=2)
            self.ping.grid(row=0, column=3)
            self.frame.pack()

        def _connect(self):
            pass
        def _disconnect(self):
            pass
        def _reset(self):
            pass
        def _ping(self):
            pass

    class FileHolder:

        def __init__(self, mcu, frame):
            self.mcu = mcu
            self.frame = tk.Frame(frame)
            self.title = tk.Label(self.frame, text='Files')
            self.title.pack()
            self.frame.pack(side='left')

        def read_files(self, cb):
            self.files = []
            self.mcu.write('import os')
            dirs = self.mcu.write('os.listdir()')
            dirs = dirs[1:-1].split(',')
            for file_ in dirs:
                label = tk.Label(self.frame, text=file_.replace("'", ''))
                label.pack()
                self.files.append(label)
            cb()

    class Consol:

        def __init__(self, mcu, frame, root):
            self.mcu = mcu
            self.frame = tk.Frame(frame)
            self.c = tk.Entry(self.frame, width=60)
            self.btn = tk.Button(self.frame, text="Send", command=self._send)

            self.output = tk.Text(self.frame, width=80, height=10)

            self.c.grid(row=0, column=0)
            self.btn.grid(row=0, column=1)
            self.output.grid(row=1, columnspan=2)
            self.frame.pack()

            self.c.bind('<Control-KeyRelease-a>', self._mark)
            self.c.bind('<Return>', self._send)
            self.c.focus_set()

        def _mark(self, event):
            # select text
            event.widget.select_range(0, 'end')
            # move cursor to the end
            event.widget.icursor('end')

        def _send(self, *e):
            command = self._parse_cmd(self.c.get())
            if command == 'clear':
                self.output.delete('1.0', 'end')
            else:
                res = self.mcu.write(command)
                self.output.insert('end', '\n' + res)
            self.c.delete(0, 'end')

        def _parse_cmd(self, data):
            return data


    class Register():

        def __init__(self, reg, frame):
            self.reg = reg
            self.frame = tk.Frame(frame)
            self.label = tk.Label(self.frame, text='Reg %s' % hex(reg), width=10)
            self.int = tk.Label(self.frame, width=10)
            self.entry = tk.Entry(self.frame, width=20)

            self.label.grid(column=0, row=0)
            self.int.grid(column=1, row=0)
            self.entry.grid(column=2, row=0)
            self.frame.pack()

        def set_val(self, value):
            self.entry.delete(0, 'end')
            formated = str(bin(value))[2:].zfill(8)
            self.entry.insert('end', formated)
            self.int.config(text=str(value))


class NodeMcu:

    def __init__(self, port='/dev/ttyUSB0', baud=115200, timeout=.1):
        # Open instantly. Not doing so fails on my Ubuntu version (18.04)
        self.serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=.1)
        print('Connected')

        for line in INIT:
            self.write(line)

    def write(self, data):
        data = f'{data}\r\n'.encode()
        self.serial.write(data)
        response = self.serial.read_until('\r\n')
        response = response[len(data):].decode('utf-8')
        response = re.sub('>>>|\s*|\r\n|\n', '', response)
        return response

    def __enter__(self):
        return self

    def __exit__(self, *args):
        for line in DE_INIT:
            self.write(line)
        self.serial.close()
        for arg in args:
            if arg:
                print(arg)


if __name__ == "__main__":

    with NodeMcu() as mcu:
        window = MainWindow(mcu)
        window.read_files()
        window.read_regs()

        window.mainloop()
