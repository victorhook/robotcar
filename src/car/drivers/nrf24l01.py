import binascii
from machine import Pin, SoftSPI
from micropython import const
import time

# PINS
SCK = 5
MOSI = 4
MISO = 0
CE = 2
CSN = 14

R_REGISTER = 0x00
W_REGISTER = 0x20
R_RX_PAYLOAD = 0x61
W_TX_PAYLOAD = 0xA0
FLUSH_TX = 0xE1
FLUSH_RX = 0xE2
NOP = 0xFF

## REGISTERS
CONFIG = 0X00
EN_AA = 0X01
EN_RXADDR = 0X02
SETUP_AW = 0X03
SETUP_RETR = 0X04
RF_CH = 0X05
RF_SETUP = 0X06
STATUS = 0X07
OBSERVE_TX = 0X08
CD = 0X09
TX_ADDR = 0X10
RX_PW_P0 = 0X11
FIFO_STATUS = 0X17

RX_ADDR_P0 = 0X0A
ENAA_P0 = 0x01
ERX_P0 = 0x01

FIVE_BYTE_ADDRESS = 0b11
DATA_RATE_1MBPS = 0x00
DATA_RATE_2MBPS = 0x08
PWR_0dBm = 0b11
PWR_MINUS_6dBm = 0b10
PWR_MINUS_12dBm = 0b01
PWR_MINUS_18dBm = 0b00

CRC_ENA = 0x08
CRC = 0x04

# Status flags
RX_DR = 0x40
TX_DS = 0x20
MAX_RT = 0x20
MAX_P_NO = 0x0E
TX_FULL = 0x01

PWR_UP = 0x02
PRIM_RX = 0x01


class NRF24L01:

    SCK = 5
    MOSI = 4
    MISO = 0

    def __init__(self, ce, csn, spi=None, baudrate=400000, payload_size=16):
        self._csn = Pin(csn) if type(csn) == int else csn
        self._ce = Pin(ce) if type(ce) == int else ce
        self._payload_size = payload_size
        self._spi = spi

        self._init_spi(baudrate)

        self._ce.init(Pin.OUT, value=0)
        self._csn.init(Pin.OUT, value=1)

        self._buf = bytearray(1)
        self._write_reg(SETUP_AW, FIVE_BYTE_ADDRESS)
        if self._read_reg(SETUP_AW) != FIVE_BYTE_ADDRESS:
            print('Failed to set address width!')

        self._flush_tx()
        self._flush_rx()

    def _write_reg(self, reg, data):
        self._csn(0)
        self._spi.readinto(self._buf, 0x20 | reg)
        ret = self._buf[0]
        self._spi.readinto(self._buf, data)
        self._csn(1)
        return ret

    def _write_reg_bytes(self, reg, data):
        self._csn(0)
        self._spi.readinto(self._buf, 0x20 | reg)
        self._spi.write(data)
        self._csn(1)
        return self._buf[0]

    def _read_reg(self, reg):
        self._csn(0)
        self._spi.readinto(self._buf, 0x00 | reg)
        self._spi.readinto(self._buf)
        self._csn(1)
        return self._buf[0]

    def read_reg(self, reg):
        return bin(self._read_reg(reg))

    def _init_spi(self, baudrate):
        if self._spi is None:
            self._spi = SoftSPI(baudrate=baudrate, polarity=0, phase=0,
                                sck=Pin(self.SCK), mosi=Pin(self.MOSI),
                                miso=Pin(self.MISO))
        self._spi.init(baudrate=baudrate)

    def _flush_rx(self):
        self._csn(0)
        self._spi.readinto(self._buf, FLUSH_RX)
        self._csn(1)

    def _flush_tx(self):
        self._csn(0)
        self._spi.readinto(self._buf, FLUSH_TX)
        self._csn(1)

    def set_channel(self, channel):
        self._write_reg(RF_CH, channel)

    def set_speed(self, speed):
        self._write_reg(RF_SETUP, self._read_reg(RF_SETUP) | speed)

    def set_power(self, power):
        self._write_reg(RF_SETUP, self._read_reg(RF_SETUP) | power)

    def _get_address(self, address):
        # Ensure that address is in byte-format
        if type(address) == list:
            address = bytes(address)
        elif type(address) == str:
            address = binascii.unhexlify(address)
        return address

    # Set both RX and TX address to the given value.
    # Default pipe used is PIPE 0
    def open_tx_pipe(self, address):
        address = self._get_address(address)

        self._write_reg_bytes(RX_ADDR_P0, address)
        self._write_reg_bytes(TX_ADDR, address)
        # Must enable RX pipe by writing data-length to it (CAN'T be 0)
        self._write_reg(RX_PW_P0, self._payload_size)
        self._ce(0)


    # Default pipe is PIPE 0
    def open_rx_pipe(self, address):
        address = self._get_address(address)
        # Set RX address
        self._write_reg_bytes(RX_ADDR_P0, address)
        # Nbr of bytes in RX payload
        self._write_reg(RX_PW_P0, self._payload_size)
        # Enable RX
        self._write_reg(EN_RXADDR, self._read_reg(EN_RXADDR) | ERX_P0)

        self._write_reg(EN_AA, self._read_reg(EN_AA) & ~ENAA_P0)

    def enable_auto_ack(self):
        self._write_reg(EN_AA, self._read_reg(EN_AA) | ENAA_P0)

    # The parameter crc is the ammount of bytes to be used.
    # Only 1 or 2 is accepted.
    def set_crc(self, crc):
        # read config reg (wihtout the current CRC value)
        config = self._read_reg(CONFIG) & ~CRC
        if crc == 1:
            config |= CRC_ENA
        elif crc == 2:
            config |= CRC_ENA | CRC
        self._write_reg(CONFIG, config)

    def start_listening(self):
        # Power-up and enable RX
        self._write_reg(CONFIG, self._read_reg(CONFIG) | PWR_UP | PRIM_RX)
        self._write_reg(STATUS,
                        self._read_reg(STATUS) | RX_DR | TX_DS | MAX_RT)

        # Flush fifos and set CE HIGH to start listening.
        self._flush_rx()
        self._flush_tx()
        self._ce(1)

    def stop_listening(self):
        self._ce(0)
        self._flush_rx()
        self._flush_tx()

    def read(self):
        # Read the data from the payload reg
        self._ce(0)
        self._csn(0)            # R_RX_PAYLOAD = 0x61
        self._spi.readinto(self._buf, 0x61)
        data = self._spi.read(self._payload_size)

        # Must toggle CE here as well, to disable receiver temporarly
        self._ce(1)
        self._csn(1)

        # Clear RX ready flag when done
        self._write_reg(STATUS, self._read_reg(STATUS) | RX_DR)
        return data

    def send(self, buf, timeout=500):
        self._send_start(buf)
        start = time.ticks_ms()
        result = None
        while (result is None and
               time.ticks_diff(time.ticks_ms(), start) < timeout):
            result = self._send_done()

        print('result: %s' % result)

    def _send_done(self):
        status = self._read_reg(STATUS)
        if not (status & (TX_DS | MAX_RT)):
            # Haven't finished yet
            return None

        # Transmission is over, clear the interrupt bits in the status-reg
        self._write_reg(STATUS, status | RX_DR | TX_DS | MAX_RT)

        if status & TX_DS:
            # Successfull send
            return 1
        else:
            # MAX attempts have passed, return 2 to indicate failure
            return 2

    def _send_start(self, buf):
        # Power-up and enable TX
        self._write_reg(CONFIG, (self._read_reg(CONFIG) | PWR_UP) & ~PRIM_RX)
        time.sleep_us(200)

        # Send the data
        self._csn(0)             # W_TX_PAYLOAD = 0xA0
        self._spi.readinto(self._buf, 0xA0)
        self._spi.write(buf)
        # Need to pad the rest of the packet if data ist too small.
        if len(buf) < self._payload_size:
            self._spi.write(b'\x00' * (self._payload_size - len(buf)))

        self._csn(1)

        # Toggle the ce-signal to send that data
        self._ce(1)
        time.sleep_us(15)   # MINIMUM 10 us according to datasheet
        self._ce(0)

    def close(self):
        self._spi.deinit()
