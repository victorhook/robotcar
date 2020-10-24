from crazyradio import Crazyradio


if __name__ == "__main__":
    radio = Crazyradio()
    radio.set_channel(90)
    radio.set_data_rate(radio.DR_2MPS)
    radio.set_address(b'\xe7\xe7\xe7\xe7\xe7')
    radio.set_ack_enable(True)

    import time
    while True:
#        resp = radio.send_packet(bytes([0x01, 0x02]))
        res = radio.scan_channels(0, 125, bytes([0x01, ]))
        if res:
            print(res)





""" from machine import SoftSPI, Pin
from known import NRF24L01
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(4), miso=Pin(0))
NRF24L01(spi, Pin(2), Pin(14))
ce = 2
csn = 14
 """
