from enum import Enum


class MsgKeys(Enum):
    TYPE = "Type"
    MSG = "msg"
    TO = "to"


class MsgTypes(Enum):
    CONNECT = 1
    DISCONNECT = 2
    SEND_MSG = 3
    GET_ALL_CLIENTS = 4
    GET_ALL_FILES = 5
    FILE_DOWNLOAD = 6


