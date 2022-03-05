import threading
import time
from unittest import TestCase
import json
import struct

import consts
import packet
import client
import server
import fast_reliable_udp
from consts import MsgKeys, MsgTypes


class TestPackets(TestCase):

    def test_json_packet(self):
        d = {MsgKeys.TYPE: MsgTypes.CONNECT, MsgKeys.USERNAME: "Bob"}
        p = packet.pack_json(d)

        self.assertEqual(p[4:], json.dumps(d).encode())
        self.assertEqual(len(json.dumps(d)), struct.unpack("I", p[:4])[0])

    def test_data_packet(self):
        p = packet.DataPacket(0, b"Test", 1)
        b = p.pack()
        self.assertEqual(struct.pack("IIII", 0, packet.calc_checksum(p.data), len(p.data), 1), b[:16])
        self.assertEqual(p.data, b[16:])

    def test_info_packet(self):
        p = packet.InfoPacket(0, packet.InfoPacket.TYPE_ACK)
        b = p.pack()
        self.assertEqual(struct.pack("II", 0, 1), b)
        self.assertEqual(8, len(b))

    def test_file_sender(self):
        s = fast_reliable_udp.Sender(56789)
        s.create_packets(b"ABCDEFGH"*10000)
        size = 8*10000 / consts.MAX_PACKET_DATA_SIZE
        if 8*10000 % consts.MAX_PACKET_DATA_SIZE != 0:
            size = size + 1

        self.assertEqual(len(s.packets), size)
        self.assertFalse(s.is_running)
        self.assertFalse(s.is_stop)
        self.assertFalse(s.is_pause)

    def test_file_receiver(self):
        r = fast_reliable_udp.Receiver("localhost", 56789, r"C:\temp\tempfile")
        self.assertFalse(r.is_downloading)
        self.assertEqual("localhost", r.address)


# class TestChat(TestCase):
#     def setUp(self):
#         self.s = server.Server(55500)
#         threading.Thread(target=self.s.run).start()
#         self.c = client.Client()
#         time.sleep(1)
#         self.c.connect("Bob", "localhost", 55500)
#
#     def test_send_msg(self):
#         self.c.send_msg("This is msg")
#
#     def tearDown(self):
#         self.c.disconnect()
#         time.sleep(1)
#         self.s.is_running = False
