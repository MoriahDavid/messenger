import json
import socket
from consts import MsgTypes, MsgKeys
import consts


class Server:

    def __init__(self, listen_port):
        self.client_sock = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', listen_port))
        self.sock.listen()
        self.is_running = True

    def _listen_to_new_clients(self):
        while self.is_running:
            client_socket, client_addr = self.sock.accept()  # client_addr = (ip,port)
            client_msg = client_socket.recv(consts.BUFF_SIZE)
            d = json.loads(client_msg)
            if d.get(MsgKeys.TYPE) == MsgTypes.CONNECT:
                username = d.get(MsgKeys.USERNAME)
                if len(username) <= consts.USERNAME_LEN:
                    # if the username good, put this client in the clients-socket dict
                    self.client_sock[username] = client_socket
                    d = {MsgKeys.TYPE: MsgTypes.SEND_MSG_SUCCESS}
                    client_socket.send(b"" + json.dumps(d))
                    print("client connected")

    def _listen_to_clients_req(self):
        pass


def main():
    server = Server(consts.SERVER_PORT)
    server._listen_to_new_clients()


if __name__ == "__main__":
    main()

