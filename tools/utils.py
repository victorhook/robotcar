class FlashProtocol:
    FILE_OK = 0x01
    FILE_NOT_OK = 0x02
    FLASH_START = 0x03
    FLASH_EXIT = 0x04
    FLASH_NEW_FILE = 0x05
    LIST_FILES_START = 0x06
    LIST_FILES_EXIT = 0x08
    NEW_FILE_NAME = 0x07

    CODES = {
        FILE_OK: 'File OK',
        FILE_NOT_OK: 'File not OK!',
        FLASH_START: 'Flash start',
        FLASH_EXIT: 'Flash exit',
        }
