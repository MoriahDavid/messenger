from enum import Enum

BUFF_SIZE = 1024
USERNAME_LEN = 20
SERVER_PORT = 55000


class MsgKeys(Enum):
    TYPE = "Type"
    USERNAME = "username"
    MSG = "msg"
    TO = "to"


class MsgTypes(Enum):
    CONNECT = 1
    DISCONNECT = 2
    SEND_MSG = 3
    GET_ALL_CLIENTS = 4
    GET_ALL_FILES = 5
    FILE_DOWNLOAD_REQ = 6
    FILE_DOWNLOAD = 7
    CONNECT_SUCCESS = 8
    DISCONNECT_SUCCESS = 9
    SEND_MSG_SUCCESS = 10
    GET_ALL_CLIENTS_SUCCESS = 11
    GET_ALL_FILES_SUCCESS = 12
    FILE_DOWNLOAD_REQ_SUCCESS = 13
    FILE_DOWNLOAD_SUCCESS = 14



