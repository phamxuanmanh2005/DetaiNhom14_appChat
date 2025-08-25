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

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_HOST, SERVER_PORT))

        # --- Frame login ---
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

        self.current_friend = None

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        nickname = self.nickname_entry.get().strip()
        if not username or not password or not nickname:
            messagebox.showerror("Lỗi", "Vui lòng nhập đủ thông tin")
            return
        msg = f"REGISTER {username} {password} {nickname}\n"
        self.sock.sendall(msg.encode())
        resp = self.sock.recv(1024).decode()
        messagebox.showinfo("Phản hồi", resp)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Lỗi", "Nhập Username và Password")
            return
        msg = f"LOGIN {username} {password}\n"
        self.sock.sendall(msg.encode())
        resp = self.sock.recv(1024).decode()
        if resp.startswith("OK"):
            self.open_chat_window()
        else:
            messagebox.showerror("Đăng nhập thất bại", resp)

    def open_chat_window(self):
        self.login_frame.destroy()
        self.chat_frame = ttk.Frame(self.master, padding=10)
        self.chat_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(self.chat_frame, width=200)
        left_frame.pack(side="left", fill="y", padx=(0,10))
        right_frame = ttk.Frame(self.chat_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        ttk.Label(left_frame, text="Tìm kiếm:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,5))
        self.search_entry = ttk.Entry(left_frame)
        self.search_entry.pack(fill="x", pady=(0,10))

        ttk.Label(left_frame, text="Bạn bè:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.friend_listbox = tk.Listbox(left_frame, height=20)
        self.friend_listbox.pack(fill="both", expand=True, pady=(5,0))

        # demo bạn bè
        demo_friends = ["Alice", "Bob", "Charlie", "David"]
        for f in demo_friends:
            self.friend_listbox.insert(tk.END, f)

        self.friend_listbox.bind("<<ListboxSelect>>", self.select_friend)

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

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def select_friend(self, event):
        selection = self.friend_listbox.curselection()
        if selection:
            self.current_friend = self.friend_listbox.get(selection[0])
            self.chat_label.config(text=f"Đang chat với {self.current_friend}")
            self.text_area.config(state="normal")
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, f"Bắt đầu chat với {self.current_friend}...\n")
            self.text_area.config(state="disabled")

    def send_msg(self):
        msg = self.msg_entry.get().strip()
        if msg and self.current_friend:
            full_msg = f"TO {self.current_friend} {msg}\n"
            self.sock.sendall(full_msg.encode())
            self.msg_entry.delete(0, tk.END)
            self.text_area.config(state="normal")
            self.text_area.insert(tk.END, f"Tôi: {msg}\n")
            self.text_area.config(state="disabled")
            self.text_area.see(tk.END)
        elif not self.current_friend:
            messagebox.showwarning("Chưa chọn bạn bè", "Hãy chọn 1 người để chat!")

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                if not data:
                    break
                self.text_area.config(state="normal")
                self.text_area.insert(tk.END, data + "\n")
                self.text_area.config(state="disabled")
                self.text_area.see(tk.END)
            except:
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
