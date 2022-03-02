import random
import select
import socket
import struct
import threading
import time

import consts
import packet


class Sender:
    def __init__(self, address, port):
        self.packets = {}  # seq_num : packet obj
        self.address = address
        self.port = port
        self.sock = None
        self.is_running = False

    def create_packets(self, data: bytes):
        data_len = len(data)
        packets_amount = int(data_len/consts.MAX_PACKET_DATA_SIZE)
        # creates the packets and put it in the packets dict
        for packet_seq in range(packets_amount):
            part_data = data[packet_seq*consts.MAX_PACKET_DATA_SIZE: (packet_seq+1)*consts.MAX_PACKET_DATA_SIZE]
            new_packet = packet.DataPacket(packet_seq, part_data, packets_amount)
            self.packets[packet_seq] = new_packet

        print(f"Total creates packets ({len(self.packets)})")

    def send(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create new ipv4 udp socket
        self.is_running = True
        window_size = 1
        window_start_packet = 0
        self.sock.bind(("", self.port))  # relates this socket  to all networks and port

        received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # wait for receive syn
        seq_num, response_type = struct.unpack(packet.AckPacket.PACKET_FORMAT, received_bytes)  # unpack the packet
        if response_type == packet.AckPacket.TYPE_SYN:  # like except
            data = packet.AckPacket(0, packet.AckPacket.TYPE_SYN_ACK).pack()  # create synack packet
            self.sock.sendto(data, address)  # send the packet
        else:
            return
        received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # wait for receive ack
        seq_num, response_type = struct.unpack(packet.AckPacket.PACKET_FORMAT, received_bytes)  # unpack the packet
        if not response_type == packet.AckPacket.TYPE_ACK:  # like except
            return

        thread = threading.Thread(target=self._recv_acks)
        thread.start()

        while self.is_running:

            lost_flag = False  # in order to know if we have lost packets
            count_success_in_window = 0
            for packet_seq in range(window_start_packet, window_start_packet + window_size):
                if self.packets.get(packet_seq) is None:
                    break

                if self.packets[packet_seq].is_finish:  # packet got ack
                    count_success_in_window = count_success_in_window + 1
                    continue

                #  packet doesnt sent
                elif self.packets[packet_seq].send_time == 0:
                    data_to_send = self.packets[packet_seq].pack()  # pack the data of packet for sending
                    self.sock.sendto(data_to_send, address)  # data, tuple(address(ip), port)
                    self.packets[packet_seq].send_time = time.time()  # save the current time
                    print(f"packet ({packet_seq}) sent.")

                # packet got NACK OR packet got timeout
                elif self.packets[packet_seq].nack or \
                        time.time() - self.packets[packet_seq].send_time >= consts.UDP_SEND_FILE_TIMEOUT:
                    lost_flag = True
                    data_to_send = self.packets[packet_seq].pack()  # pack the data of packet for sending
                    self.sock.sendto(data_to_send, address)  # data, tuple(address(ip), port)
                    self.packets[packet_seq].send_time = time.time()  # save the current time
                    print(f"packet ({packet_seq}) sent again.")

            if lost_flag:  # cut the window
                if window_size != 1:
                    window_size = int(window_size/2)
                    print(f"decrease window size to {window_size}")
                if self.packets[window_start_packet].is_finish:
                    window_start_packet = window_start_packet + 1
            elif count_success_in_window == window_size:  # finish all packets in window-> move & make the window bigger
                if window_start_packet + window_size >= len(self.packets):
                    self.is_running = False
                    print("All packets sent successfully")
                    # close the socket
                    thread.join()  # wait for the thread finish
                    self.sock.close()
                    break

                window_start_packet = window_start_packet + window_size
                if window_size < consts.LIMIT_WINDOW_SIZE:  # check that not cross the limit of window size
                    window_size = window_size * 2
                else:
                    window_size = window_size + 1
                print(f"increase window size to {window_size}")

            else:
                continue

    def _recv_acks(self):
        while self.is_running:
            inputs, o, e = select.select([self.sock], [], [], 0)
            if inputs:
                msg, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)
                seq_num, response_type = struct.unpack(packet.AckPacket.PACKET_FORMAT, msg)  # format, msg

                curr_packet = self.packets.get(seq_num)
                if curr_packet:
                    if response_type == packet.AckPacket.TYPE_ACK:
                        curr_packet.is_finish = True
                    elif response_type == packet.AckPacket.TYPE_NACK:
                        curr_packet.nack = True


class Receiver:
    def __init__(self, address, port, file_name):
        self.address = address
        self.port = port
        self.file_name = file_name
        self.sock = None

    def receive(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create udp socket for send to the server
        # Make handshake with the server (SYN SYNACK ACK)
        data = packet.AckPacket(0, packet.AckPacket.TYPE_SYN).pack()  # create syn-packet
        self.sock.sendto(data, (self.address, self.port))  # send the packet
        received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # wait for receive synack
        seq_num, response_type = struct.unpack(packet.AckPacket.PACKET_FORMAT, received_bytes)  # unpack the packet
        if response_type == packet.AckPacket.TYPE_SYN_ACK:  # like except
            data = packet.AckPacket(0, packet.AckPacket.TYPE_ACK).pack()  # create ack packet
            self.sock.sendto(data, (self.address, self.port))  # send the packet
        else:
            return False

        last_recv_packet = -1  # seq_num of last packet that arrived
        recv_jump_packets = {}  # packets with seq number that not follows the last seq_num (seq_num : data)
        total_packets = 1
        f = open(self.file_name, "wb")  # write binary data
        last_4_bytes = ""

        while last_recv_packet + 1 < total_packets:

            received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # receive the data packet
            seq_num, checksum, length, total_packets = struct.unpack(packet.DataPacket.PACKET_FORMAT, received_bytes[0:16])
            data = received_bytes[16:]  # takes the data part after the packet header

            ########## simulate packets fails ############
            if consts.SIMULATE_PACKETS_LOST:
                rand_number = random.randint(0, 10)
                if rand_number % 4 == 0:  # miss the packet
                    print(f"Drop packet ({seq_num})")
                    continue
                elif rand_number % 5 == 0:  # change the data so the checksum should fail the packet
                    print(f"Change data packet ({seq_num})")
                    data = b'0' + data + b'1'
            #############################################

            #  if the checksum incorrect
            if checksum != packet.calc_checksum(data):
                # need to send nack
                ack_pkt_data = packet.AckPacket(seq_num, packet.AckPacket.TYPE_NACK).pack()
                self.sock.sendto(ack_pkt_data, (self.address, self.port))

            # checksum correct:
            else:
                # seq_num is continuous
                if seq_num == last_recv_packet+1:  # all good
                    ack_pkt_data = packet.AckPacket(seq_num, packet.AckPacket.TYPE_ACK).pack()
                    self.sock.sendto(ack_pkt_data, (self.address, self.port))
                    f.write(data)
                    last_4_bytes = data[-4:]
                    last_recv_packet = seq_num

                    while recv_jump_packets.get(last_recv_packet+1) is not None:
                        data = recv_jump_packets.pop(last_recv_packet+1)
                        f.write(data)
                        last_4_bytes = data[-4:]
                        last_recv_packet = last_recv_packet + 1
                else:
                    # add this to the dict
                    recv_jump_packets[seq_num] = data
                    ack_pkt_data = packet.AckPacket(seq_num, packet.AckPacket.TYPE_ACK).pack()
                    self.sock.sendto(ack_pkt_data, (self.address, self.port))

                    # send nack for all packets from last_recv_packet+1 to seq_num-1
                    for s in range(last_recv_packet+1, seq_num):
                        ack_pkt_data = packet.AckPacket(s, packet.AckPacket.TYPE_NACK).pack()
                        self.sock.sendto(ack_pkt_data, (self.address, self.port))

        f.close()  # close the file
        self.sock.close()  # close the socket

        return last_4_bytes


