# client_core.py

import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from client_ui import LoginUI, MainUI

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("App Chat")

        # socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kết nối server: {e}")
            master.destroy()
            return

        self.username = None
        self.nickname = None
        self.current_friend = None
        self.friend_windows = {}
        self.user_nick_map = {}

        # start listener thread
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # build login UI
        self.login_ui = LoginUI(self)

    # gửi dữ liệu tới server
    def send_line(self, text):
        try:
            self.sock.sendall((text + "\n").encode())
        except:
            messagebox.showerror("Lỗi", "Mất kết nối tới server")

    # các hàm gọi từ UI
    def register(self, u, p, n):
        if not u or not p or not n:
            messagebox.showwarning("Thiếu thông tin", "Nhập đủ Username, Password, Nickname")
            return
        self.send_line(f"REGISTER {u} {p} {n}")

    def login(self, u, p):
        if not u or not p:
            messagebox.showwarning("Thiếu thông tin", "Nhập Username và Password")
            return
        self.username = u
        self.send_line(f"LOGIN {u} {p}")

    # sau khi login thành công: build main UI
    def build_main_ui(self):
        # remove login UI and create main UI
        try:
            self.login_ui.destroy()
        except:
            pass
        self.main_ui = MainUI(self)

    # helper: gọi method trên main_ui một cách an toàn (thử lại nếu main_ui chưa tồn tại)
    def _call_main_ui(self, method_name, *args, **kwargs):
        if hasattr(self, "main_ui") and self.main_ui:
            try:
                getattr(self.main_ui, method_name)(*args, **kwargs)
            except Exception as e:
                # nếu có lỗi khi gọi method, in log để debug
                print(f"Error calling main_ui.{method_name}: {e}")
        else:
            # thử lại sau 50ms nếu main_ui chưa được tạo
            self.master.after(50, lambda: self._call_main_ui(method_name, *args, **kwargs))

    # --- receive thread ---
    def receive_messages(self):
        buf = ""
        try:
            while True:
                data = self.sock.recv(4096).decode()
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if not line:
                        continue
                    self.process_server_line(line.strip())
        except Exception as e:
            print("Lỗi nhận:", e)
            try:
                self.sock.close()
            except:
                pass

    # --- xử lý server response ---
    def process_server_line(self, line):
        # helper để chạy callback trên main thread
        def ui(fn, *a, **kw):
            self.master.after(0, fn, *a, **kw)

        if line.startswith("REGISTER_OK"):
            ui(messagebox.showinfo, "Đăng ký", "Đăng ký thành công. Bạn có thể đăng nhập.")
        elif line.startswith("ERR"):
            reason = line[4:] if len(line) > 4 else line
            ui(messagebox.showerror, "Lỗi", reason)
        elif line.startswith("LOGIN_OK") or line.startswith("OK"):
            parts = line.split(" ", 1)
            nick = parts[1] if len(parts) > 1 else self.username
            self.nickname = nick
            ui(self.build_main_ui)
        elif line.startswith("USERLIST"):
            parts = line.split(" ")[1:]
            # gọi an toàn tới main_ui.update_friend_list_ui
            ui(lambda p=parts: self._call_main_ui("update_friend_list_ui", p))
        elif line.startswith("SEARCH_OK"):
            tokens = line.split()
            if len(tokens) >= 4:
                uname = tokens[1]
                nick = tokens[2]
                friend_flag = tokens[3].split("=",1)[1] if "=" in tokens[3] else "NO"
                ui(lambda u=uname, n=nick, f=friend_flag: self._call_main_ui("show_search_result", u, n, f))
            else:
                ui(messagebox.showinfo, "Tìm kiếm", "Kết quả không rõ")
        elif line.startswith("SEARCH_NOT_FOUND"):
            ui(lambda: self._call_main_ui("show_search_not_found"))
        elif line.startswith("FRIEND_REQ"):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                from_user = parts[1]
                from_nick = parts[2]
                ui(lambda fu=from_user, fn=from_nick: self._call_main_ui("show_incoming_friend_request", fu, fn))
        elif line.startswith("FRIEND_REQUEST_SENT"):
            parts = line.split(" ",1)
            to_user = parts[1] if len(parts)>1 else ""
            ui(messagebox.showinfo, "Kết bạn", f"Đã gửi lời mời đến {to_user}")
        elif line.startswith("FRIEND_REQUEST_STORED"):
            parts = line.split(" ",1)
            to_user = parts[1] if len(parts)>1 else ""
            ui(messagebox.showinfo, "Kết bạn", f"Lời mời được lưu, {to_user} chưa online")
        elif line.startswith("FRIEND_ACCEPTED"):
            parts = line.split(" ",2)
            if len(parts)>=3:
                who = parts[1]
                nick = parts[2]
                ui(messagebox.showinfo, "Kết bạn", f"{nick} ({who}) đã chấp nhận lời mời")
            else:
                ui(messagebox.showinfo, "Kết bạn", "Đã chấp nhận lời mời")
        elif line.startswith("FRIEND_REJECTED"):
            parts = line.split(" ",1)
            who = parts[1] if len(parts)>1 else ""
            ui(messagebox.showinfo, "Kết bạn", f"{who} đã từ chối lời mời")
        elif line.startswith("MSG"):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                frm = parts[1]
                msg = parts[2]
                ui(lambda f=frm, m=msg: self._call_main_ui("display_incoming_message", f, m))
        else:
            ui(messagebox.showinfo, "Phản hồi server", line)