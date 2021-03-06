from enum import Enum

SERVER_PREFIX_MSG = ">>>"

BUFF_SIZE = 1024
UDP_BUFF_SIZE = 65535
USERNAME_LEN = 10
SERVER_PORT = 55000
RESPONSE_TIMEOUT = 4

MAX_PACKET_DATA_SIZE = 40000
UDP_SEND_FILE_TIMEOUT = 3  # seconds
LIMIT_WINDOW_SIZE = 16
SIMULATE_PACKETS_LOST = False

FILES_FOLDER_NAME = "files"


class MsgKeys(str, Enum):
    TYPE = "Type"
    USERNAME = "username"
    MSG = "msg"
    TO = "to"
    FROM = "from"
    STATUS = "status"


class MsgTypes(int, Enum):
    CONNECT = 1
    DISCONNECT = 2
    SEND_MSG = 3
    GET_ALL_CLIENTS = 4
    GET_ALL_FILES = 5
    FILE_DOWNLOAD = 6
    CONNECT_RESPONSE = 7
    DISCONNECT_RESPONSE = 8
    SEND_MSG_RESPONSE = 9
    GET_ALL_CLIENTS_RESPONSE = 10
    GET_ALL_FILES_RESPONSE = 11
    FILE_DOWNLOAD_RESPONSE = 12



