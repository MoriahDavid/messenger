import random
import select
import socket
import struct
import threading
import time

import consts
import packet


class Sender:
    def __init__(self, port):
        self.packets = {}  # seq_num : packet obj
        self.port = port
        self.sock = None
        self.is_running = False
        self.is_pause = False
        self.is_stop = False

    def create_packets(self, data: bytes):
        data_len = len(data)
        packets_amount = int(data_len/consts.MAX_PACKET_DATA_SIZE)
        if data_len % consts.MAX_PACKET_DATA_SIZE != 0:
            packets_amount = packets_amount + 1
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
        self.sock.bind(("", self.port))  # relates this socket to all networks and port

        # start the HANDSHAKE with the receiver
        # the handshake give 10 times for packet lost. else --> stop the running.
        # sender: server wait for syn message and then for ack message.
        # if there is packet loss (no-response from the receiver), server sends again the prev msg.
        counter = 0
        wait_for = "syn"
        address = None
        while counter < 10:
            inputs, outputs, err = select.select([self.sock], [], [], 5)
            ########## simulate packets fails ############
            if consts.SIMULATE_PACKETS_LOST:
                rand_number = random.randint(0, 10)
                if inputs and rand_number % 3 == 0:  # miss the packet
                    self.sock.recvfrom(consts.UDP_BUFF_SIZE)
                    print("Drop handshake packet")
                    inputs = []
            #############################################
            if not inputs:
                counter = counter + 1
                if wait_for == "syn":
                    continue
                elif wait_for == "ack":
                    data = packet.InfoPacket(0, packet.InfoPacket.TYPE_SYN_ACK).pack()  # create synack packet
                    self.sock.sendto(data, address)  # send the packet
            else:
                received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # receive the message (syn/ack)
                seq_num, response_type = struct.unpack(packet.InfoPacket.PACKET_FORMAT, received_bytes)  # unpack the packet
                if response_type == packet.InfoPacket.TYPE_SYN and wait_for == "syn":  # like except
                    data = packet.InfoPacket(0, packet.InfoPacket.TYPE_SYN_ACK).pack()  # create synack packet
                    self.sock.sendto(data, address)  # send the packet
                    wait_for = "ack"
                elif response_type == packet.InfoPacket.TYPE_ACK and wait_for == "ack":
                    break

        if counter == 10:
            return

        thread = threading.Thread(target=self._recv_acks)
        thread.start()

        while self.is_running:

            if window_start_packet >= len(self.packets):
                self.is_running = False
                print("All packets sent successfully")
                # close the socket
                thread.join()  # wait for the thread finish
                self.sock.close()
                break

            if self.is_stop:  # the client stop the download
                self.is_running = False
                print("Stop")
                # close the socket
                thread.join()  # wait for the thread finish
                self.sock.close()
                break

            if self.is_pause:  # the client pause the download
                continue

            lost_flag = False  # in order to know if we have lost packets
            count_success_in_window = 0
            count_in_window = 0
            for packet_seq in range(window_start_packet, window_start_packet + window_size):
                if self.packets.get(packet_seq) is None:
                    break

                count_in_window = count_in_window + 1

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
                    self.packets[packet_seq].nack = False
                    print(f"packet ({packet_seq}) sent again.")

            if lost_flag:  # cut the window
                if window_size != 1:
                    window_size = int(window_size/2)
                    print(f"decrease window size to {window_size}")
                if self.packets[window_start_packet].is_finish:
                    window_start_packet = window_start_packet + 1
            elif count_success_in_window == count_in_window:  # finish all packets in window-> move & make the window bigger
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
            inputs, o, e = select.select([self.sock], [], [], 0)  # return if we have something to read when receive()
            if inputs:
                try:
                    msg, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)
                except ConnectionResetError:
                    continue

                seq_num, response_type = struct.unpack(packet.InfoPacket.PACKET_FORMAT, msg)  # format, msg

                if response_type == packet.InfoPacket.TYPE_PAUSE:
                    print("Pause sending")
                    self.is_pause = True

                elif response_type == packet.InfoPacket.TYPE_CONTINUE:
                    print("Continue sending")
                    self.is_pause = False

                elif response_type == packet.InfoPacket.TYPE_STOP:
                    print("Stop sending")
                    self.is_stop = True

                else:
                    curr_packet = self.packets.get(seq_num)
                    if curr_packet:
                        if response_type == packet.InfoPacket.TYPE_ACK:
                            curr_packet.is_finish = True
                        elif response_type == packet.InfoPacket.TYPE_NACK:
                            curr_packet.nack = True


class Receiver:
    def __init__(self, address, port, file_name):
        self.is_downloading = False
        self.address = address
        self.port = port
        self.file_name = file_name
        self.sock = None
        self.total_packets = 0
        self.last_recv_packet = 0

    def ask_for_pause(self):
        data = packet.InfoPacket(0, packet.InfoPacket.TYPE_PAUSE).pack()  # create pause-packet
        self.sock.sendto(data, (self.address, self.port))  # send the packet

    def ask_for_continue(self):
        data = packet.InfoPacket(0, packet.InfoPacket.TYPE_CONTINUE).pack()  # create continue-packet
        self.sock.sendto(data, (self.address, self.port))  # send the packet

    def ask_for_stop(self):
        data = packet.InfoPacket(0, packet.InfoPacket.TYPE_STOP).pack()  # create stop-packet
        self.sock.sendto(data, (self.address, self.port))  # send the packet
        self.is_downloading = False

    def receive(self):
        self.is_downloading = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create udp socket for send to the server
        # Make handshake with the server (SYN SYNACK ACK)
        data = packet.InfoPacket(0, packet.InfoPacket.TYPE_SYN).pack()  # create syn-packet
        self.sock.sendto(data, (self.address, self.port))  # send the packet
        counter = 0
        wait_for = "synack"
        address = None
        first_data_packet_bytes = None
        while counter < 10:
            inputs, outputs, err = select.select([self.sock], [], [], 5)
            ########## simulate packets fails ############
            if consts.SIMULATE_PACKETS_LOST:
                rand_number = random.randint(0, 10)
                if inputs and rand_number % 3 == 0:  # miss the packet
                    self.sock.recvfrom(consts.UDP_BUFF_SIZE)
                    print("Drop handshake packet")
                    inputs = []
            #############################################
            if not inputs:
                counter = counter + 1
                if wait_for == "synack":
                    data = packet.InfoPacket(0, packet.InfoPacket.TYPE_SYN).pack()  # create syn-packet
                    self.sock.sendto(data, (self.address, self.port))  # send the packet
                elif wait_for == "data":
                    data = packet.InfoPacket(0, packet.InfoPacket.TYPE_ACK).pack()  # create ack packet
                    self.sock.sendto(data, address)  # send the packet
            else:
                received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # receive the message (synack/data)
                if len(received_bytes) > 8 and wait_for == "data":  # got data packet(good) --> end of handshake
                    first_data_packet_bytes = received_bytes
                    break
                seq_num, response_type = struct.unpack(packet.InfoPacket.PACKET_FORMAT,received_bytes)  # unpack the packet
                if response_type == packet.InfoPacket.TYPE_SYN_ACK and wait_for == "synack":  # like except
                    data = packet.InfoPacket(0, packet.InfoPacket.TYPE_ACK).pack()  # create ack packet
                    self.sock.sendto(data, address)  # send the packet
                    wait_for = "data"

        self.last_recv_packet = -1  # seq_num of last packet that arrived
        recv_jump_packets = {}  # packets with seq number that not follows the last seq_num (seq_num : data)
        self.total_packets = 1
        f = open(self.file_name, "wb")  # write binary data
        last_4_bytes = ""

        while self.last_recv_packet + 1 < self.total_packets and self.is_downloading:
            inputs, o, e = select.select([self.sock], [], [], 1)  # return if we have something to read when receive()
            if not inputs and first_data_packet_bytes is None:
                continue
            if first_data_packet_bytes is None:
                received_bytes, address = self.sock.recvfrom(consts.UDP_BUFF_SIZE)  # receive the data packet
            else:
                received_bytes = first_data_packet_bytes
                first_data_packet_bytes = None
            seq_num, checksum, length, self.total_packets = struct.unpack(packet.DataPacket.PACKET_FORMAT, received_bytes[0:16])
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
                ack_pkt_data = packet.InfoPacket(seq_num, packet.InfoPacket.TYPE_NACK).pack()
                self.sock.sendto(ack_pkt_data, (self.address, self.port))

            # checksum correct:
            else:
                # seq_num is continuous
                if seq_num == self.last_recv_packet+1:  # all good
                    ack_pkt_data = packet.InfoPacket(seq_num, packet.InfoPacket.TYPE_ACK).pack()
                    self.sock.sendto(ack_pkt_data, (self.address, self.port))
                    f.write(data)
                    last_4_bytes = data[-4:]
                    self.last_recv_packet = seq_num

                    while recv_jump_packets.get(self.last_recv_packet+1) is not None:
                        data = recv_jump_packets.pop(self.last_recv_packet+1)
                        f.write(data)
                        last_4_bytes = data[-4:]
                        self.last_recv_packet = self.last_recv_packet + 1
                else:
                    # add this to the dict
                    recv_jump_packets[seq_num] = data
                    ack_pkt_data = packet.InfoPacket(seq_num, packet.InfoPacket.TYPE_ACK).pack()
                    self.sock.sendto(ack_pkt_data, (self.address, self.port))

                    # send nack for all packets from last_recv_packet+1 to seq_num-1
                    for s in range(self.last_recv_packet+1, seq_num):
                        ack_pkt_data = packet.InfoPacket(s, packet.InfoPacket.TYPE_NACK).pack()
                        self.sock.sendto(ack_pkt_data, (self.address, self.port))

        f.close()  # close the file
        self.sock.close()  # close the socket
        if self.last_recv_packet + 1 == self.total_packets:
            print("All packets received successfully")

        print(f"last 4 received bytes ({last_4_bytes})")
        return last_4_bytes


