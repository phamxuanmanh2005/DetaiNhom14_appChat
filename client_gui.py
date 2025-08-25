# client_gui.py
import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("App Chat")

        # connect ngay
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
        self.friend_windows = {}  # nếu muốn mở cửa sổ chat riêng
        self.user_nick_map = {}  # username -> nickname

        # start listener thread ngay
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # build login UI
        self.login_frame = ttk.Frame(master, padding=20)
        self.login_frame.pack()

        title_label = ttk.Label(self.login_frame, text="App Chat", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0,15))

        ttk.Label(self.login_frame, text="Username:").grid(row=1, column=0, sticky="w")
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=1, column=1)

        ttk.Label(self.login_frame, text="Password:").grid(row=2, column=0, sticky="w")
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=2, column=1)

        ttk.Label(self.login_frame, text="Nickname:").grid(row=3, column=0, sticky="w")
        self.nickname_entry = ttk.Entry(self.login_frame)
        self.nickname_entry.grid(row=3, column=1)

        self.btn_login = ttk.Button(self.login_frame, text="Đăng nhập", command=self.login)
        self.btn_login.grid(row=4, column=0, pady=10)

        self.btn_register = ttk.Button(self.login_frame, text="Đăng ký", command=self.register)
        self.btn_register.grid(row=4, column=1, pady=10)

    def send_line(self, text):
        try:
            self.sock.sendall((text + "\n").encode())
        except:
            messagebox.showerror("Lỗi", "Mất kết nối tới server")

    # --- các hành động từ UI ---
    def register(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        n = self.nickname_entry.get().strip()
        if not u or not p or not n:
            messagebox.showwarning("Thiếu thông tin", "Nhập đủ Username, Password, Nickname")
            return
        self.send_line(f"REGISTER {u} {p} {n}")

    def login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        if not u or not p:
            messagebox.showwarning("Thiếu thông tin", "Nhập Username và Password")
            return
        self.username = u
        self.send_line(f"LOGIN {u} {p}")

    # --- sau khi login thành công: xây dựng UI chính ---
    def build_main_ui(self):
        # xóa login_frame
        self.login_frame.destroy()

        self.chat_frame = ttk.Frame(self.master, padding=10)
        self.chat_frame.pack(fill="both", expand=True)

        # Hiển thị tên chào mừng
        top_label = ttk.Label(self.chat_frame, text=f"Xin chào {self.nickname}", font=("Arial", 14, "bold"))
        top_label.pack(anchor="center", pady=(0,10))

        left_frame = ttk.Frame(self.chat_frame, width=220)
        left_frame.pack(side="left", fill="y", padx=(0,10))
        right_frame = ttk.Frame(self.chat_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        # Search
        ttk.Label(left_frame, text="Tìm kiếm:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,5))
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill="x", pady=(0,5))

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.do_search())

        search_btn = ttk.Button(search_frame, text="Tìm", command=self.do_search)
        search_btn.pack(side="left", padx=5)

        self.search_result_frame = ttk.Frame(left_frame)
        self.search_result_frame.pack(fill="x", pady=(0,10))

        # Friend list
        ttk.Label(left_frame, text="Bạn bè / Online:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.friend_listbox = tk.Listbox(left_frame, height=18)
        self.friend_listbox.pack(fill="both", expand=True, pady=(5,0))
        self.friend_listbox.bind("<<ListboxSelect>>", self.select_friend)
        self.friend_listbox.bind("<Double-1>", self.open_private_window)

        # RIGHT: chat area for selected friend
        self.chat_label = ttk.Label(right_frame, text="Chưa chọn bạn bè", font=("Arial", 12, "bold"))
        self.chat_label.pack(anchor="center", pady=(0,5))

        self.text_area = tk.Text(right_frame, state="disabled", wrap="word")
        self.text_area.pack(padx=5, pady=5, fill="both", expand=True)

        entry_frame = ttk.Frame(right_frame)
        entry_frame.pack(fill="x")

        self.msg_entry = ttk.Entry(entry_frame)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.msg_entry.bind("<Return>", lambda e: self.send_msg())

        self.send_button = ttk.Button(entry_frame, text="Gửi", command=self.send_msg)
        self.send_button.pack(side="right", padx=5, pady=5)

    # --- search ---
    def do_search(self):
        query = self.search_entry.get().strip()
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        if not query:
            return
        self.send_line(f"SEARCH {query}")

    # --- chọn bạn bè ---
    def select_friend(self, event):
        sel = self.friend_listbox.curselection()
        if not sel:
            return
        item = self.friend_listbox.get(sel[0])
        uname = item.split(":", 1)[0] if ":" in item else item
        self.current_friend = uname
        self.chat_label.config(text=f"Đang chat với {self.user_nick_map.get(uname, uname)}")
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, f"Bắt đầu chat với {self.user_nick_map.get(uname, uname)}...\n")
        self.text_area.config(state="disabled")

    # --- private chat window ---
    def open_private_window(self, event):
        sel = self.friend_listbox.curselection()
        if not sel:
            return
        item = self.friend_listbox.get(sel[0])
        uname = item.split(":", 1)[0] if ":" in item else item
        if uname in self.friend_windows:
            self.friend_windows[uname][2].lift()
            return
        win = tk.Toplevel(self.master)
        win.title(f"Chat với {self.user_nick_map.get(uname, uname)}")
        text_area = tk.Text(win, state="disabled", width=50, height=15)
        text_area.pack()
        entry = ttk.Entry(win, width=40)
        entry.pack(side="left", padx=5, pady=5)
        send_btn = ttk.Button(win, text="Gửi", command=lambda: self.send_private_message(uname, entry, text_area))
        send_btn.pack(side="left", pady=5)
        self.friend_windows[uname] = (text_area, entry, win)

    def send_private_message(self, to_user, entry_widget, text_area):
        text = entry_widget.get().strip()
        if not text:
            return
        self.send_line(f"MSG {to_user} {text}")
        entry_widget.delete(0, tk.END)
        self.append_text(text_area, f"Tôi: {text}\n")

    def send_msg(self):
        if not self.current_friend:
            messagebox.showwarning("Chưa chọn bạn bè", "Hãy chọn một người để chat")
            return
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.send_line(f"MSG {self.current_friend} {text}")
        self.msg_entry.delete(0, tk.END)
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, f"Tôi: {text}\n")
        self.text_area.config(state="disabled")
        self.text_area.see(tk.END)

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

    def process_server_line(self, line):
        def ui(fn, *a, **kw):
            self.master.after(0, fn, *a, **kw)

        if line.startswith("REGISTER_OK"):
            ui(messagebox.showinfo, "Đăng ký", "Đăng ký thành công. Bạn có thể đăng nhập.")
        elif line.startswith("ERR"):
            reason = line[4:] if len(line) > 4 else line
            ui(messagebox.showerror, "Lỗi", reason)
        elif line.startswith("LOGIN_OK") or line.startswith("OK"):  # thêm xử lý OK
            parts = line.split(" ", 1)
            nick = parts[1] if len(parts) > 1 else self.username
            self.nickname = nick
            ui(self.build_main_ui)
        elif line.startswith("USERLIST"):
            parts = line.split(" ")[1:]
            ui(self.update_friend_list_ui, parts)
        elif line.startswith("SEARCH_OK"):
            tokens = line.split()
            if len(tokens) >= 4:
                uname = tokens[1]
                nick = tokens[2]
                friend_flag = tokens[3].split("=",1)[1] if "=" in tokens[3] else "NO"
                ui(self.show_search_result, uname, nick, friend_flag)
            else:
                ui(messagebox.showinfo, "Tìm kiếm", "Kết quả không rõ")
        elif line.startswith("SEARCH_NOT_FOUND"):
            ui(self.show_search_not_found)
        elif line.startswith("FRIEND_REQ"):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                from_user = parts[1]
                from_nick = parts[2]
                ui(self.show_incoming_friend_request, from_user, from_nick)
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
                ui(self.display_incoming_message, frm, msg)
        else:
            ui(messagebox.showinfo, "Phản hồi server", line)

    def update_friend_list_ui(self, entries):
        self.friend_listbox.delete(0, tk.END)
        self.user_nick_map.clear()
        for ent in entries:
            if ":" in ent:
                uname, nick = ent.split(":", 1)
            else:
                uname, nick = ent, ent
            self.user_nick_map[uname] = nick
            if uname == self.username:
                continue
            self.friend_listbox.insert(tk.END, f"{uname}:{nick}")

    def show_search_result(self, uname, nick, friend_flag):
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        ttk.Label(self.search_result_frame, text=f"{uname} : {nick}").pack(anchor="w")
        if uname == self.username:
            ttk.Label(self.search_result_frame, text="Đây là bạn (chính bạn)").pack(anchor="w")
            return
        if friend_flag == "YES":
            ttk.Label(self.search_result_frame, text="Đã là bạn bè").pack(anchor="w")
            return
        btn = ttk.Button(self.search_result_frame, text="Kết bạn", command=lambda: self.send_line(f"FRIEND_REQUEST {uname}"))
        btn.pack(anchor="w", pady=5)

    def show_search_not_found(self):
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        ttk.Label(self.search_result_frame, text="Không tìm thấy tài khoản").pack(anchor="w")

    def show_incoming_friend_request(self, from_user, from_nick):
        win = tk.Toplevel(self.master)
        win.title("Lời mời kết bạn")
        ttk.Label(win, text=f"{from_nick} ({from_user}) muốn kết bạn").pack(padx=10, pady=10)
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Đồng ý", command=lambda: self._respond_friend_request(win, from_user, True)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Xóa", command=lambda: self._respond_friend_request(win, from_user, False)).pack(side="left", padx=5)

    def _respond_friend_request(self, win, from_user, accept):
        if accept:
            self.send_line(f"FRIEND_ACCEPT {from_user}")
        else:
            self.send_line(f"FRIEND_REJECT {from_user}")
        win.destroy()

    def display_incoming_message(self, from_user, msg):
        if self.current_friend == from_user:
            self.text_area.config(state="normal")
            self.text_area.insert(tk.END, f"{self.user_nick_map.get(from_user, from_user)}: {msg}\n")
            self.text_area.config(state="disabled")
            self.text_area.see(tk.END)
            return
        if from_user in self.friend_windows:
            ta, _, win = self.friend_windows[from_user]
            self.append_text(ta, f"{self.user_nick_map.get(from_user, from_user)}: {msg}\n")
            return
        win = tk.Toplevel(self.master)
        win.title(f"Tin nhắn từ {self.user_nick_map.get(from_user, from_user)}")
        ta = tk.Text(win, state="disabled", width=50, height=10)
        ta.pack()
        ta.config(state="normal")
        ta.insert(tk.END, f"{self.user_nick_map.get(from_user, from_user)}: {msg}\n")
        ta.config(state="disabled")
        entry = ttk.Entry(win, width=40)
        entry.pack(side="left", padx=5, pady=5)
        send_btn = ttk.Button(win, text="Gửi", command=lambda: self.send_private_message(from_user, entry, ta))
        send_btn.pack(side="left", pady=5)
        self.friend_windows[from_user] = (ta, entry, win)

    def append_text(self, ta, text):
        ta.config(state="normal")
        ta.insert(tk.END, text)
        ta.config(state="disabled")
        ta.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
