import json
import select
import struct
import threading
import socket
import time

from consts import MsgTypes, MsgKeys
from fast_reliable_udp import Receiver
import consts
import common


class Client:

    def __init__(self):
        self.sock = None
        self.is_connected = False
        self._all_clients = None
        self.server_ip = None
        self.new_msg_gui_function = None
        self._download_file_response = None
        self._all_files = None
        self.receiver = None

    def _listen_to_server_req(self):
        while self.is_connected:
            inputs, outputs, errors = select.select([self.sock], [], [], 0)
            if len(inputs) > 0:
                # read the int (represent the packet size) with unpack func.
                msg_size = struct.unpack("I", self.sock.recv(4))[0]
                data = self.sock.recv(msg_size)
                d = json.loads(data)
                r_type = d.get(MsgKeys.TYPE)
                if r_type == MsgTypes.SEND_MSG:
                    msg = d.get(MsgKeys.MSG)
                    sender_name = d.get(MsgKeys.FROM)
                    self.display_msg(sender_name, msg)
                elif r_type == MsgTypes.GET_ALL_CLIENTS_RESPONSE:
                    self._all_clients = d.get(MsgKeys.MSG)
                elif r_type == MsgTypes.GET_ALL_FILES_RESPONSE:
                    self._all_clients = d.get(MsgKeys.MSG)
                elif r_type == MsgTypes.FILE_DOWNLOAD_RESPONSE:
                    self._download_file_response = d

    def set_gui_new_msg_function(self, func):
        self.new_msg_gui_function = func

    def display_msg(self, sender_name, msg):
        print(f"{sender_name}: {msg}")

        if self.new_msg_gui_function:
            self.new_msg_gui_function(sender_name, msg)

    def connect(self, username, server_ip, server_port):
        """
        create connection to the server with username.
        :param username:
        :param server_ip:
        :param server_port:
        :return:
        """
        # try because the server could not running
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((server_ip, server_port))  # connect to the server
            self.server_ip = server_ip
        except ConnectionRefusedError:
            return False

        d = {MsgKeys.TYPE: MsgTypes.CONNECT, MsgKeys.USERNAME: username}  # create dict (JSON) to the msg
        self.sock.sendall(common.pack_json(d))  # send the msg by change the JSON to string
        # read the int (represent the packet size) with unpack func.
        msg_size = struct.unpack("I", self.sock.recv(4))[0]
        m = self.sock.recv(msg_size)
        d = json.loads(m)
        if d.get(MsgKeys.TYPE) == MsgTypes.CONNECT_RESPONSE:
            if d.get(MsgKeys.STATUS):
                print("connected")
                self.is_connected = True
                thread_new_msg = threading.Thread(target=self._listen_to_server_req)
                thread_new_msg.start()
                return True
            else:
                print(d.get(MsgKeys.MSG))
                self.sock.close()
                return False

    def disconnect(self):
        d = {MsgKeys.TYPE: MsgTypes.DISCONNECT}
        self.is_connected = False
        self.sock.sendall(common.pack_json(d))
        self.sock.close()

    def send_msg(self, msg, to=None):
        d = {MsgKeys.TYPE: MsgTypes.SEND_MSG, MsgKeys.MSG: msg}
        if to:
            d[MsgKeys.TO] = to
        self.sock.sendall(common.pack_json(d))

    def get_all_clients(self):
        """
        :return: the list of all connected clients or None in timeout
        """
        d = {MsgKeys.TYPE: MsgTypes.GET_ALL_CLIENTS}
        self.sock.sendall(common.pack_json(d))
        st = time.time()
        while self._all_clients is None and time.time() - st <= consts.RESPONSE_TIMEOUT:
            time.sleep(0.1)
        r = self._all_clients
        self._all_clients = None
        return r

    def get_all_files(self):
        d = {MsgKeys.TYPE: MsgTypes.GET_ALL_FILES}
        self.sock.sendall(common.pack_json(d))
        st = time.time()
        while self._all_files is None and time.time() - st <= consts.RESPONSE_TIMEOUT:
            time.sleep(0.1)
        r = self._all_files
        self._all_files = None
        return r

    def file_download(self, file_name, save_to):
        d = {MsgKeys.TYPE: MsgTypes.FILE_DOWNLOAD, MsgKeys.MSG: file_name}
        self.sock.sendall(common.pack_json(d))
        st = time.time()
        while self._download_file_response is None and time.time() - st <= consts.RESPONSE_TIMEOUT:
            time.sleep(0.1)
        r = self._download_file_response
        self._download_file_response = None
        if not r.get(MsgKeys.STATUS):
            pass  # TODO: cant download
        else:
            port = r.get(MsgKeys.MSG)
            self.receiver = Receiver(self.server_ip, port, save_to)
            self.receiver.receive()  # TODO: print return value to the screen

    def pause_download(self):
        if self.receiver:
            self.receiver.ask_for_pause()

    def continue_download(self):
        if self.receiver:
            self.receiver.ask_for_continue()

    def stop_download(self):
        if self.receiver:
            self.receiver.ask_for_stop()


def main():
    client = Client()
    client.connect("moriah", "127.0.0.1", consts.SERVER_PORT)
    client.send_msg("hey")
    print(client.get_all_clients())
    print(client.get_all_clients())



if __name__ == "__main__":
    main()

