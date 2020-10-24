import gc
gc.collect()

SCK = 5
MOSI = 4
MISO = 0
CE = 2
CSN = 14

from nrf24l01 import NRF24L01

nrf = NRF24L01(ce=2, csn=14)

nrf.set_channel(90)
nrf.set_speed(0x08)
nrf.set_crc(2)
nrf.open_tx_pipe('e7e7e7e7e7')
nrf.send(bytes([0x01, 0x02]))
nrf.read_reg(0x07)
