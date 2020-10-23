#from machine import Pin, SoftSPI
#import time

SCK = 1
MOSI = 2
MISO = 3
CE = 4      # Chip enable, activates RX or TX mode
CSN = 5     # SPI Chip select

GPIO = {
   #X: 1 TX
   #X: 3 RX
    0: 16,  # WAKEUP
    1: 5,
    2: 4,
    3: 0,
    4: 2,
    5: 14,
    6: 12,
    7: 13,
    8: 15
}


class NRF24L01:

    SCK = 5
    MOSI = 4
    MISO = 0

    def __init__(self, ce, csn, spi=None, baudrate=400000):
        self._ce = Pin(ce) if type(ce) == int else ce
        self._csn = Pin(csn) if type(csn) == int else csn
        self._spi = spi

        self._init_spi(baudrate)

        self._ce.init(Pin.OUT, value=0)
        self._csn.init(Pin.OUT, value=1)


    def _read_reg(self, address):
        self._csn(0)
        data = self._spi.read(address)
        self._csn(1)
        return data

    def _init_spi(self, baudrate):
        if self._spi is None:
            self._spi = SoftSPI(baudrate=baudrate, polarity=1, phase=0, sck=Pin(self.SCK),
                                mosi=Pin(self.MOSI), miso=Pin(self.MISO))
        self._spi.init(baudrate=baudrate)

    def close(self):
        self._spi.deinit()


# spi = SoftSPI(baudrate=100000, polarity=1, phase=0, sck=Pin(GPIO[SCK]),
#               mosi=Pin(GPIO[MOSI]), miso=Pin(GPIO[MISO]))
# spi.init(baudrate=200000)


nrf = NRF24L01(ce=GPIO[CE], csn=GPIO[CSN])
data = nrf._read_reg(0x01)
print(data)
nrf.close()
