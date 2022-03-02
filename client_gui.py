from tkinter import *
from tkinter import _setit

import client
import consts


class Gui:
    def __init__(self, client):
        self.root = Tk()
        self.root.wm_title("Messenger")
        self.root.geometry("670x600")  # set windows size
        self.root.resizable(False, False)  # disable windows change size
        self.connected_clients = ["Everyone"]
        self.send_to = StringVar(self.root)

        self.files_to_down = ["Files"]
        self.to_download = StringVar(self.root)

        self.create_window()

        self.client = client
        self.client.set_gui_new_msg_function(self.show_msg_to_screen)


    def create_window(self):
        # msg screen
        f = Frame(self.root)
        f.place(x=50, y=80)
        scrollbar = Scrollbar(f)
        self._msg_screen = Text(f, height=24, width=70, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self._msg_screen.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self._msg_screen.pack(side=LEFT)
        self._msg_screen.config(state=DISABLED)

        # text box
        self._text_msg = Entry(self.root, width=60)
        self._text_msg.pack(side=LEFT)
        self._text_msg.place(x=210, y=480)
        self._text_msg.bind('<Return>', self.send_msg_enter)

        # sending button
        b = Button(self.root, text='send', command=self.send_msg)
        b.pack(side=LEFT)
        b.place(x=580, y=477)

        # choose user to send message
        self.send_to.set(self.connected_clients[0])
        self._drop = OptionMenu(self.root, self.send_to, *self.connected_clients)
        self._drop.config(width=15)
        self._drop.pack()
        self._drop.place(x=70, y=477)

        refresh = Button(self.root, text=u"\U0001F5D8", command=self.update_login_clients)
        refresh.pack(side=LEFT)
        refresh.config(width=2)
        refresh.place(x=50, y=480)

        # login username text box
        lbl = Label(self.root, text="Username:", font=("Arial", 10))
        lbl.pack(side=LEFT)
        lbl.place(x=50, y=15)
        self._username = Entry(self.root, width=20)
        self._username.pack(side=LEFT)
        self._username.place(x=50, y=40)

        # login address text box
        lbl = Label(self.root, text="Address:", font=("Arial", 10))
        lbl.pack(side=LEFT)
        lbl.place(x=200, y=15)
        self._address = Entry(self.root, width=34)
        self._address.pack(side=LEFT)
        self._address.place(x=200, y=40)

        # login button
        self._login_btn = Button(self.root, text='Login', command=self.login)
        self._login_btn.pack(side=LEFT)
        self._login_btn.place(x=415, y=37)

        # files

        # files button
        # choose file to download
        self.to_download.set(self.files_to_down[0])
        self._drop_files = OptionMenu(self.root, self.to_download, *self.files_to_down)
        self._drop_files.config(width=15)
        self._drop_files.pack()
        self._drop_files.place(x=70, y=521)

        refresh = Button(self.root, text=u"\U0001F5D8", command=self.update_files)
        refresh.pack(side=LEFT)
        refresh.config(width=2)
        refresh.place(x=50, y=524)

        # save file path box
        self._save_file_path = Entry(self.root, width=40)
        self._save_file_path.pack(side=LEFT)
        self._save_file_path.place(x=210, y=524)

        # download button
        b = Button(self.root, text='Download', command=self.download_file)
        b.pack(side=LEFT)
        b.place(x=465, y=524)

        pause = Button(self.root, text=u"\u23F8", command=self.pause_play_download)
        pause.pack(side=LEFT)
        pause.config(width=2)
        pause.place(x=540, y=524)
        # u"\u25B6" play symb

    def update_files(self):
        pass

    def download_file(self):
        pass

    def pause_play_download(self):
        pass

    def update_login_clients(self):
        if not self.client.is_connected:
            return

        all_c = self.client.get_all_clients()
        self.connected_clients = ["Everyone"]
        self.connected_clients.extend(all_c)
        self._drop["menu"].delete(0, "end")

        for c in self.connected_clients:
            if c == self._username.get():
                continue
            self._drop["menu"].add_command(label=c, command=_setit(self.send_to, c))

    def login(self):
        if not self.client.is_connected:
            username = self._username.get()
            address = self._address.get()
            if self.client.connect(username, address, consts.SERVER_PORT):
                self._username.config(state=DISABLED)
                self._address.config(state=DISABLED)
                self._login_btn.config(text="Logout")
        else:
            self.client.disconnect()
            self._username.config(state=NORMAL)
            self._address.config(state=NORMAL)
            self._login_btn.config(text="Login")

    def send_msg(self):
        if not self.client.is_connected:
            return

        to = self.send_to.get()
        text = self._text_msg.get()

        if not text:
            return

        if to == "Everyone":
            to = None

        self.client.send_msg(text, to)
        self._text_msg.delete(0, "end")
        self.show_msg_to_screen("~me~", text)

    def send_msg_enter(self, e):
        self.send_msg()

    def show_msg_to_screen(self, sender_name, msg):
        text = f"\n{sender_name}: {msg}"
        self._msg_screen.config(state=NORMAL)
        self._msg_screen.insert(END, text)
        self._msg_screen.config(state=DISABLED)


    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    c = client.Client()
    g = Gui(c)
    g.run()
