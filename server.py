import json
import threading
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

    def run(self):
        """
        Create the main treads for listen to new clients and listen to clients requests.
        """
        thread_new_clients = threading.Thread(target=self._listen_to_new_clients)
        thread_new_clients.start()
        thread_clients_req = threading.Thread(target=self._listen_to_clients_req)
        thread_clients_req.start()

    def _listen_to_new_clients(self):
        """
        listen to new clients connect requests
        """
        while self.is_running:
            client_socket, client_addr = self.sock.accept()  # client_addr = (ip,port)
            client_msg = client_socket.recv(consts.BUFF_SIZE)
            d = json.loads(client_msg)
            if d.get(MsgKeys.TYPE) == MsgTypes.CONNECT:
                username = d.get(MsgKeys.USERNAME)
                #  check if the username already exist
                if self.client_sock.get(username) is not None:
                    d = {MsgKeys.TYPE: MsgTypes.CONNECT_RESPONSE, MsgKeys.STATUS: False,
                         MsgKeys.MSG: "username already exist"}
                    client_socket.send(json.dumps(d).encode())
                    client_socket.close()
                #  check the username length
                elif len(username) <= consts.USERNAME_LEN:
                    # if the username good, put this client in the clients-socket dict
                    d = {MsgKeys.TYPE: MsgTypes.CONNECT_RESPONSE, MsgKeys.STATUS: True}
                    client_socket.send(json.dumps(d).encode())
                    self.client_sock[username] = client_socket
                    print(f"{username} connected")

    def _listen_to_clients_req(self):
        pass


def main():
    server = Server(consts.SERVER_PORT)
    server.run()


if __name__ == "__main__":
    main()

