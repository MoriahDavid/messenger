import json
import socket
from consts import MsgTypes, MsgKeys
import consts


class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, username, server_ip, server_port):
        """
        create connection to the server with username.
        :param username:
        :param server_ip:
        :param server_port:
        :return:
        """
        self.sock.connect((server_ip, server_port))  # connect to the server
        d = {MsgKeys.TYPE: MsgTypes.CONNECT, MsgKeys.USERNAME: username}  # create dict (JSON) to the msg
        self.sock.send(b""+json.dumps(d))  # send the msg by change the JSON to string
        m = self.sock.recv(consts.BUFF_SIZE)
        d = json.loads(m)
        if d.get(MsgKeys.TYPE) == MsgTypes.CONNECT_SUCCESS:
            print("connected")
            return True
        self.sock.close()
        return False

    def disconnect(self):
        d = {MsgKeys.TYPE: MsgTypes.DISCONNECT}
        self.sock.send(b"" + json.dumps(d))
        self.sock.close()

    def send_msg(self, msg, to=None):
        d = {MsgKeys.TYPE: MsgTypes.SEND_MSG, MsgKeys.MSG: msg}
        if to:
            d[MsgKeys.TO] = to
        self.sock.send(b"" + json.dumps(d))

    def get_all_clients(self):
        d = {MsgKeys.TYPE: MsgTypes.GET_ALL_CLIENTS}
        self.sock.send(b"" + json.dumps(d))

    def get_all_files(self):
        d = {MsgKeys.TYPE: MsgTypes.GET_ALL_FILES}
        self.sock.send(b"" + json.dumps(d))

    def _file_download_req(self):
        d = {MsgKeys.TYPE: MsgTypes.FILE_DOWNLOAD_REQ}
        self.sock.send(b"" + json.dumps(d))

    def file_download(self, file_name):
        d = {MsgKeys.TYPE: MsgTypes.FILE_DOWNLOAD}
        self.sock.send(b"" + json.dumps(d))


def main():
    client = Client()
    client.connect("moriah", "127.0.0.1", consts.SERVER_PORT)


if __name__ == "__main__":
    main()