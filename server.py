import time
import json
import struct
import select
import socket
import threading

from consts import MsgTypes, MsgKeys
import consts
import common


class Server:

    def __init__(self, listen_port):
        self.clients_uname_sock = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', listen_port))
        self.sock.listen()
        self.is_running = True

    def run(self):
        """
        Create the main treads for listen to new clients and listen to clients requests.
        """
        thread_new_clients = threading.Thread(target=self._listen_to_new_clients)
        thread_new_clients.start()
        thread_clients_req = threading.Thread(target=self._listen_to_clients_req)
        thread_clients_req.start()

    # connect
    def _listen_to_new_clients(self):
        """
        listen to new clients connect requests
        """
        while self.is_running:
            client_socket, client_addr = self.sock.accept()  # client_addr = (ip,port)
            # read the int (represent the packet size) with unpack func.
            msg_size = struct.unpack("I", client_socket.recv(4))[0]
            client_msg = client_socket.recv(msg_size)
            d = json.loads(client_msg)
            if d.get(MsgKeys.TYPE) == MsgTypes.CONNECT:
                username = d.get(MsgKeys.USERNAME)
                #  check if the username already exist
                if self.clients_uname_sock.get(username) is not None:
                    d = {MsgKeys.TYPE: MsgTypes.CONNECT_RESPONSE, MsgKeys.STATUS: False,
                         MsgKeys.MSG: "username already exist"}
                    client_socket.send(common.pack_json(d))
                    client_socket.close()
                #  check the username length
                elif len(username) > consts.USERNAME_LEN:
                    d = {MsgKeys.TYPE: MsgTypes.CONNECT_RESPONSE, MsgKeys.STATUS: False,
                         MsgKeys.MSG: "username too long"}
                    client_socket.send(common.pack_json(d))
                    client_socket.close()
                else:
                    # if the username good, put this client in the clients-socket dict
                    d = {MsgKeys.TYPE: MsgTypes.CONNECT_RESPONSE, MsgKeys.STATUS: True}
                    client_socket.send(common.pack_json(d))
                    self.clients_uname_sock[username] = client_socket
                    print(f"{username} connected")
                    self.send_msg_to_all_clients(f"{username} connected")

    def _listen_to_clients_req(self):
        while self.is_running:
            client_socks = list(self.clients_uname_sock.values())
            if not client_socks:
                continue
            inputs, outputs, errors = select.select(client_socks, [], [], 1)
            if len(inputs) > 0:
                for client_sock in inputs:
                    #  catch exception if the client close without disconnect (The socket closed)
                    try:
                        # read the int (represent the packet size) with unpack func.
                        msg_size = struct.unpack("I", client_sock.recv(4))[0]
                        data = client_sock.recv(msg_size)
                    except ConnectionResetError:
                        self.disconnect_client(client_sock)
                        continue

                    d = json.loads(data)
                    r_type = d.get(MsgKeys.TYPE)
                    if r_type == MsgTypes.DISCONNECT:
                        self.disconnect_client(client_sock)
                    elif r_type == MsgTypes.SEND_MSG:
                        self.send_msg(d, client_sock)
                    elif r_type == MsgTypes.GET_ALL_CLIENTS:
                        self.get_all_clients(client_sock)
                    elif r_type == MsgTypes.FILE_DOWNLOAD_REQ:
                        pass
                    elif r_type == MsgTypes.FILE_DOWNLOAD:
                        pass
                    elif r_type == MsgTypes.GET_ALL_FILES:
                        pass

    # disconnect
    def disconnect_client(self, client_socket):
        disconnect_username = self.get_username_by_socket(client_socket)
        # delete this client from the dict
        self.clients_uname_sock.pop(disconnect_username)
        d = {MsgKeys.TYPE: MsgTypes.DISCONNECT_RESPONSE, MsgKeys.STATUS: True}
        try:
            client_socket.send(common.pack_json(d))
        except ConnectionResetError:
            pass
        client_socket.close()
        self.send_msg_to_all_clients(f"{disconnect_username} disconnected")

    def send_msg_to_all_clients(self, msg):
        d = {MsgKeys.TYPE: MsgTypes.SEND_MSG, MsgKeys.MSG: msg, MsgKeys.FROM: "Server"}
        socks = list(self.clients_uname_sock.values())  # all sockets of all clients

        for sock in socks:
            sock.send(common.pack_json(d))

    def send_msg(self, d, sender_socket):
        to = d.get(MsgKeys.TO)
        msg = d.get(MsgKeys.MSG)
        sender_name = self.get_username_by_socket(sender_socket)
        d = {MsgKeys.TYPE: MsgTypes.SEND_MSG, MsgKeys.MSG: msg, MsgKeys.FROM: sender_name}
        if to is not None:  # the user want to send msg to *one* client
            socks = [self.clients_uname_sock.get(to)]
        else:
            socks = list(self.clients_uname_sock.values())
            socks.remove(sender_socket)

        for sock in socks:
            sock.send(common.pack_json(d))

    def get_username_by_socket(self, value):
        for k in self.clients_uname_sock.keys():
            if self.clients_uname_sock.get(k) == value:
                return k

    def get_all_clients(self, sender_socket):
        all_clients = list(self.clients_uname_sock.keys())
        d = {MsgKeys.TYPE: MsgTypes.GET_ALL_CLIENTS_RESPONSE, MsgKeys.MSG: all_clients}
        sender_socket.send(common.pack_json(d))




def main():
    server = Server(consts.SERVER_PORT)
    server.run()


if __name__ == "__main__":
    main()

