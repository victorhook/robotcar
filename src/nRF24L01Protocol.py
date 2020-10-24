R_REGISTER  # 000A AAAA , AAAAA = 0x00 to 0x17 | 1 to 5 LSByte first
W_REGISTER  # 001A AAAA , AAAAA = 0x00 to 0x17 | 1 to 5 LSByte first

R_RX_PAYLOAD  # 0110 0001 | 1 to 32 LSByte first
# Recieving packets = CE HIGH, must set CE low to disable de receiever and read data
# FIFO can hold 3 packets

# -- RX_RX_PAYLOAD --
# New packet -> RX_DR interrupt signal
# 1. Set CE low
# 2. Read data
# 3. Clear RX_DR interrupt
# 4. Set CE high

W_TX_PAYLOAD  # 1010 0000 | 1 to 32 LSByte first
# Transmit mode - CE LOW
# FIFO can hold 3 packets, before CE must be toggled to send data
# 1. Send 0xA0, then payload
# 2. Pull CE HIGH, for ~10us to sent
# 3. If packet sent, TX_DS interrupt will occur
#   --> If auto-ack enabled, TX_DS is only set if packet arrives OK
#       If no ack, it will attempt to send packets n number of times (set in the register SETUP_RETR)
#       and then assert MAX_RT interrupt if fail.

FLUSH_TX    # 1110 0001
FLUSH_RX    # 1110 0010

NOP         # 1111 1111


## REGISTERS
CONFIG      = 0X00
EN_AA       = 0X01
EN_RXADDR   = 0X02
SETUP_AW    = 0X03
SETUP_RETR  = 0X04
RF_CH       = 0X05
RF_SETUP    = 0X06
STATUS      = 0X07
OBSERVE_TX  = 0X08
CD          = 0X09
RX_ADDR_P0  = 0X0A
RX_ADDR_P1  = 0X0B
RX_ADDR_P2  = 0X0C
RX_ADDR_P3  = 0X0D
RX_ADDR_P4  = 0X0E
RX_ADDR_P5  = 0X0F
TX_ADDR     = 0X10
RX_Pw_P0    = 0X11 # 0X11-0X16 data payload widths for each pipe
FIFO_STATUS = 0X17

