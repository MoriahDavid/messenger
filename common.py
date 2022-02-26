import json
import struct


def pack_json(d):
    """
    convert the json dict to string and add its(string length) size to the start
    :param d:
    :return:
    """
    st = json.dumps(d).encode()
    size = len(st)
    return struct.pack("I", size)+st

