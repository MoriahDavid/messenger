from enum import Enum

BUFF_SIZE = 1024
USERNAME_LEN = 20
SERVER_PORT = 55000


class MsgKeys(str, Enum):
    TYPE = "Type"
    USERNAME = "username"
    MSG = "msg"
    TO = "to"
    STATUS = "status"


class MsgTypes(int, Enum):
    CONNECT = 1
    DISCONNECT = 2
    SEND_MSG = 3
    GET_ALL_CLIENTS = 4
    GET_ALL_FILES = 5
    FILE_DOWNLOAD_REQ = 6
    FILE_DOWNLOAD = 7
    CONNECT_RESPONSE = 8
    DISCONNECT_RESPONSE = 9
    SEND_MSG_RESPONSE = 10
    GET_ALL_CLIENTS_RESPONSE = 11
    GET_ALL_FILES_RESPONSE = 12
    FILE_DOWNLOAD_REQ_RESPONSE = 13
    FILE_DOWNLOAD_RESPONSE = 14



