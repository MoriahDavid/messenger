import struct
import binascii


def calc_checksum(data):
    return binascii.crc32(data)


class DataPacket:
    """
    The packets that sent from the sender
    """
    # The format for struct (seq_num, checksum, length, total_packets)
    PACKET_FORMAT = "IIII"

    def __init__(self, seq_num, data, total_packets):
        self.seq_num = seq_num
        self.data = data
        self.checksum = 0
        self.total_packets = total_packets
        self.send_time = 0
        self.is_finish = False
        self.nack = False

    def pack(self):
        length = len(self.data)
        checksum = calc_checksum(self.data)

        p = struct.pack(self.PACKET_FORMAT, self.seq_num, checksum, length, self.total_packets)
        p = p + self.data

        return p


class InfoPacket:
    """
    The packet that represents info about packets response.
    """
    PACKET_FORMAT = "II"  # (seq_num, response_type)

    TYPE_ACK = 1
    TYPE_NACK = 2
    TYPE_SYN = 3
    TYPE_SYN_ACK = 4
    TYPE_PAUSE = 5
    TYPE_CONTINUE = 6
    TYPE_STOP = 7

    def __init__(self, seq_num, response_type):
        self.seq_num = seq_num
        self.response_type = response_type

    def pack(self):
        return struct.pack(self.PACKET_FORMAT, self.seq_num, self.response_type)

