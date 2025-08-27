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
        self.master.title("APP CHAT")
        self.master.geometry("650x400")
        self.master.configure(bg="#0d47a1")

        # Kết nối server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kết nối server: {e}")
            master.destroy()
            return

        # Biến lưu trữ
        self.username = None
        self.nickname = None
        self.current_friend = None
        self.friend_windows = {}     # {username: (text_area, entry, win)}
        self.user_nick_map = {}      # {username: nickname}

        # Thread nhận tin nhắn
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # UI ban đầu
        self.build_login_ui()

    # ===================== LOGIN UI =====================
    def build_login_ui(self):
        self.login_frame = tk.Frame(self.master, bg="#0d47a1")
        self.login_frame.pack(fill="both", expand=True)

        # Khung trái
        left_frame = tk.Frame(self.login_frame, bg="#1565c0", width=300)
        left_frame.pack(side="left", fill="both")
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="APP CHAT", fg="white", bg="#1565c0",
                 font=("Arial", 20, "bold")).pack(pady=(30, 10))
        tk.Label(left_frame, text="Hello, welcome!", fg="white", bg="#1565c0",
                 font=("Arial", 20, "bold")).pack(pady=(20, 10))
        tk.Label(left_frame, text="Ứng dụng chat Client - Server\nPython + Tkinter",
                 fg="white", bg="#1565c0", font=("Arial", 8)).pack(pady=8)

        # Khung phải
        right_frame = tk.Frame(self.login_frame, bg="white", width=350)
        right_frame.pack(side="right", fill="both", expand=True)
        right_frame.pack_propagate(False)


        form = tk.Frame(right_frame, bg="white")
        form.pack(pady=10)

        tk.Label(form, text="Username:", bg="white").grid(row=0, column=0, sticky="w")
        self.username_entry = ttk.Entry(form, width=25)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Password:", bg="white").grid(row=1, column=0, sticky="w")
        self.password_entry = ttk.Entry(form, show="*", width=25)
        self.password_entry.grid(row=1, column=1, pady=5)

        tk.Label(form, text="Nickname:", bg="white").grid(row=2, column=0, sticky="w")
        self.nickname_entry = ttk.Entry(form, width=25)
        self.nickname_entry.grid(row=2, column=1, pady=5)

        btn_frame = tk.Frame(right_frame, bg="white")
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Đăng nhập", command=self.login).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Đăng ký", command=self.register).grid(row=0, column=1, padx=10)

    # ===================== MAIN CHAT UI =====================
    def build_main_ui(self):
        self.login_frame.destroy()   # Xóa màn hình login

        self.chat_frame = ttk.Frame(self.master, padding=10)
        self.chat_frame.pack(fill="both", expand=True)

        top_label = ttk.Label(self.chat_frame, text=f"Xin chào {self.nickname}",
                              font=("Arial", 14, "bold"))
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

        ttk.Button(search_frame, text="Tìm", command=self.do_search).pack(side="left", padx=5)

        self.search_result_frame = ttk.Frame(left_frame)
        self.search_result_frame.pack(fill="x", pady=(0,10))

        # Friend list
        ttk.Label(left_frame, text="Bạn bè / Online:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.friend_listbox = tk.Listbox(left_frame, height=18)
        self.friend_listbox.pack(fill="both", expand=True, pady=(5,0))
        self.friend_listbox.bind("<<ListboxSelect>>", self.select_friend)
        self.friend_listbox.bind("<Double-1>", self.open_private_window)

        # Chat area
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

    # ===================== HÀM GỬI / NHẬN =====================
    def send_line(self, text):
        try:
            self.sock.sendall((text + "\n").encode())
        except:
            messagebox.showerror("Lỗi", "Mất kết nối tới server")

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
                    if line:
                        self.process_server_line(line.strip())
        except Exception as e:
            print("Lỗi nhận:", e)
            try:
                self.sock.close()
            except:
                pass

    # ===================== XỬ LÝ SERVER RESPONSE =====================
    def process_server_line(self, line):
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
            users = line.split(" ")[1:]
            ui(self.update_friend_list_ui, users)
        elif line.startswith("MSG"):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                frm, msg = parts[1], parts[2]
                ui(self.display_incoming_message, frm, msg)
        else:
            ui(lambda: messagebox.showinfo("Server", line))

    # ===================== FRIEND LIST =====================
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

    def select_friend(self, event):
        sel = self.friend_listbox.curselection()
        if not sel: return
        item = self.friend_listbox.get(sel[0])
        uname = item.split(":", 1)[0]
        self.current_friend = uname
        self.chat_label.config(text=f"Đang chat với {self.user_nick_map.get(uname, uname)}")
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, f"Bắt đầu chat với {self.user_nick_map.get(uname, uname)}...\n")
        self.text_area.config(state="disabled")

    # ===================== CHAT =====================
    def send_msg(self):
        if not self.current_friend:
            messagebox.showwarning("Chưa chọn bạn bè", "Hãy chọn một người để chat")
            return
        text = self.msg_entry.get().strip()
        if not text: return
        self.send_line(f"MSG {self.current_friend} {text}")
        self.msg_entry.delete(0, tk.END)
        self.append_text(self.text_area, f"Tôi: {text}\n")

    def display_incoming_message(self, from_user, msg):
        if from_user == self.current_friend:
            self.append_text(self.text_area, f"{self.user_nick_map.get(from_user, from_user)}: {msg}\n")
        else:
            messagebox.showinfo("Tin nhắn mới", f"{self.user_nick_map.get(from_user, from_user)}: {msg}")

    def append_text(self, widget, msg):
        widget.config(state="normal")
        widget.insert(tk.END, msg)
        widget.config(state="disabled")
        widget.see(tk.END)

    # ===================== SEARCH =====================
    def do_search(self):
        query = self.search_entry.get().strip()
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        if query:
            self.send_line(f"SEARCH {query}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()

