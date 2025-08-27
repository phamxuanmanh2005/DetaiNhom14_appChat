#File này chuyên trách giao diện.
#Chia nhỏ class UI:
    #LoginUI → màn hình đăng nhập/đăng ký.
    #MainUI → giao diện chính (chat, danh sách bạn bè).
    
# client_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
import re

class LoginUI:
    def __init__(self, app):
        self.app = app
        
        # Tạo frame chính với background màu xanh dương nhạt
        self.frame = tk.Frame(app.master, bg='#e3f2fd', padx=40, pady=30)
        self.frame.pack(fill='both', expand=True)
        
        # Container cho nội dung đăng nhập
        login_container = tk.Frame(self.frame, bg='white', relief='raised', bd=2, padx=30, pady=30)
        login_container.pack(expand=True)

        # Tiêu đề
        title_label = tk.Label(login_container, text="💬 App Chat", font=("Arial", 20, "bold"), 
                              bg='white', fg='#1976d2')
        title_label.pack(pady=(0, 20))

        # Username
        tk.Label(login_container, text="👤 Username:", font=("Arial", 10), 
                bg='white', fg='#424242').pack(anchor="w", pady=(5, 0))
        self.username_entry = ttk.Entry(login_container, font=("Arial", 10), width=25)
        self.username_entry.pack(pady=(2, 10))

        # Password
        tk.Label(login_container, text="🔒 Password:", font=("Arial", 10), 
                bg='white', fg='#424242').pack(anchor="w", pady=(5, 0))
        self.password_entry = ttk.Entry(login_container, show="*", font=("Arial", 10), width=25)
        self.password_entry.pack(pady=(2, 10))

        # Nickname
        tk.Label(login_container, text="🏷️ Nickname:", font=("Arial", 10), 
                bg='white', fg='#424242').pack(anchor="w", pady=(5, 0))
        self.nickname_entry = ttk.Entry(login_container, font=("Arial", 10), width=25)
        self.nickname_entry.pack(pady=(2, 20))

        # Frame cho nút
        button_frame = tk.Frame(login_container, bg='white')
        button_frame.pack()

        # Nút đăng nhập
        self.btn_login = tk.Button(button_frame, text="Đăng nhập", font=("Arial", 10, "bold"),
                                  bg='#1976d2', fg='white', relief='flat', padx=20, pady=8,
                                  command=lambda: app.login(self.username_entry.get(), self.password_entry.get()))
        self.btn_login.pack(side="left", padx=10)

        # Nút đăng ký
        self.btn_register = tk.Button(button_frame, text="Đăng ký", font=("Arial", 10, "bold"),
                                     bg='#43a047', fg='white', relief='flat', padx=20, pady=8,
                                     command=lambda: app.register(self.username_entry.get(), self.password_entry.get(), self.nickname_entry.get()))
        self.btn_register.pack(side="left", padx=10)

        # Hiệu ứng hover cho nút
        def on_enter(e, button, color):
            button['background'] = color

        def on_leave(e, button, color):
            button['background'] = color

        self.btn_login.bind("<Enter>", lambda e: on_enter(e, self.btn_login, '#1565c0'))
        self.btn_login.bind("<Leave>", lambda e: on_leave(e, self.btn_login, '#1976d2'))
        self.btn_register.bind("<Enter>", lambda e: on_enter(e, self.btn_register, '#388e3c'))
        self.btn_register.bind("<Leave>", lambda e: on_leave(e, self.btn_register, '#43a047'))

    def destroy(self):
        self.frame.destroy()


class MainUI:
    def __init__(self, app):
        self.app = app
        
        # Tạo frame chính với background màu xám nhạt
        self.frame = tk.Frame(app.master, bg='#f5f5f5')
        self.frame.pack(fill="both", expand=True)

        # Header với thông tin người dùng
        header_frame = tk.Frame(self.frame, bg='#1976d2', height=60)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"👋 Xin chào {app.nickname}", 
                font=("Arial", 14, "bold"), bg='#1976d2', fg='white').pack(side="left", padx=20)
        
        # LEFT + RIGHT layout
        main_container = tk.Frame(self.frame, bg='#f5f5f5')
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT PANEL
        left_panel = tk.Frame(main_container, bg='white', width=250, relief='raised', bd=1)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Search section
        search_frame = tk.Frame(left_panel, bg='white', padx=10, pady=10)
        search_frame.pack(fill="x", pady=(10, 5))
        
        tk.Label(search_frame, text="🔍 Tìm kiếm", font=("Arial", 11, "bold"), 
                bg='white', fg='#424242').pack(anchor="w")
        
        search_input_frame = tk.Frame(search_frame, bg='white')
        search_input_frame.pack(fill="x", pady=(5, 0))
        
        self.search_entry = ttk.Entry(search_input_frame, font=("Arial", 9))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.do_search())

        search_btn = tk.Button(search_input_frame, text="Tìm", font=("Arial", 9),
                              bg='#1976d2', fg='white', relief='flat', padx=10,
                              command=self.do_search)
        search_btn.pack(side="right")

        self.search_result_frame = tk.Frame(left_panel, bg='white')
        self.search_result_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Friend requests section
        tk.Label(left_panel, text="📩 Yêu cầu kết bạn", font=("Arial", 11, "bold"), 
                bg='white', fg='#424242', padx=10).pack(anchor="w", pady=(10, 5))
        
        self.friend_request_frame = tk.Frame(left_panel, bg='white')
        self.friend_request_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Friend list section
        tk.Label(left_panel, text="👥 Bạn bè online", font=("Arial", 11, "bold"), 
                bg='white', fg='#424242', padx=10).pack(anchor="w", pady=(10, 5))
        
        # Frame cho listbox với scrollbar
        listbox_frame = tk.Frame(left_panel, bg='white')
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.friend_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                                        font=("Arial", 9), bg='#fafafa', relief='flat',
                                        selectbackground='#e3f2fd')
        self.friend_listbox.pack(fill="both", expand=True)
        self.friend_listbox.bind("<<ListboxSelect>>", self.select_friend)
        scrollbar.config(command=self.friend_listbox.yview)

        # RIGHT PANEL - Chat area
        right_panel = tk.Frame(main_container, bg='white', relief='raised', bd=1)
        right_panel.pack(side="right", fill="both", expand=True)

        # Chat header
        chat_header = tk.Frame(right_panel, bg='#e8f5e8', height=50)
        chat_header.pack(fill="x", side="top")
        chat_header.pack_propagate(False)
        
        self.chat_label = tk.Label(chat_header, text="💬 Chọn bạn bè để bắt đầu chat", 
                                  font=("Arial", 12, "bold"), bg='#e8f5e8', fg='#2e7d32')
        self.chat_label.pack(anchor="center", pady=15)

        # Text area for messages với scrollbar
        text_frame = tk.Frame(right_panel, bg='#f0f0f0')
        text_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Tạo canvas và frame để hỗ trợ scroll và căn chỉnh tin nhắn
        self.canvas = tk.Canvas(text_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#f0f0f0')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mousewheel to canvas
        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        # Message input area
        input_frame = tk.Frame(right_panel, bg='#f5f5f5', height=60)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)
        
        input_container = tk.Frame(input_frame, bg='#f5f5f5', padx=10, pady=10)
        input_container.pack(fill="both", expand=True)
        
        self.msg_entry = ttk.Entry(input_container, font=("Arial", 10))
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda e: self.send_msg())

        self.send_button = tk.Button(input_container, text="📤 Gửi", font=("Arial", 10, "bold"),
                                    bg='#1976d2', fg='white', relief='flat', padx=15,
                                    command=self.send_msg)
        self.send_button.pack(side="right")

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # --- các hàm phụ ---
    def do_search(self):
        query = self.search_entry.get().strip()
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        if not query:
            return
        self.app.send_line(f"SEARCH {query}")

    def select_friend(self, event):
        sel = self.friend_listbox.curselection()
        if not sel:
            return
        item = self.friend_listbox.get(sel[0])
        uname = item.split(":", 1)[0] if ":" in item else item
        self.app.current_friend = uname
        nick = self.app.user_nick_map.get(uname, uname)
        self.chat_label.config(text=f"💬 Đang chat với {nick}")
        
        # Xóa tin nhắn cũ khi chọn bạn mới
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def send_msg(self):
        if not self.app.current_friend:
            messagebox.showwarning("Chưa chọn bạn bè", "Hãy chọn một người để chat")
            return
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.app.send_line(f"MSG {self.app.current_friend} {text}")
        self.msg_entry.delete(0, tk.END)
        # Tin nhắn của mình - hiển thị bên phải
        self._display_message("Bạn", text, "right")

    # Hiển thị tin nhắn với căn chỉnh trái/phải
    def _display_message(self, sender, message, align="left"):
        # Tạo frame cho tin nhắn
        message_frame = tk.Frame(self.scrollable_frame, bg='#f0f0f0')
        message_frame.pack(fill="x", pady=2)
        
        # Container cho tin nhắn
        bubble_frame = tk.Frame(message_frame, bg='#f0f0f0')
        if align == "right":
            bubble_frame.pack(anchor="e", padx=10)
        else:
            bubble_frame.pack(anchor="w", padx=10)
        
        # Hiển thị tên người gửi (chỉ cho tin nhắn của người khác)
        if align == "left":
            sender_label = tk.Label(bubble_frame, text=sender, font=("Arial", 8), 
                                  bg='#f0f0f0', fg='#666')
            sender_label.pack(anchor="w")
        
        # Bubble tin nhắn
        if align == "right":
            # Tin nhắn của mình - màu xanh, bên phải
            bubble = tk.Frame(bubble_frame, bg='#dcf8c6', relief='raised', bd=1, padx=12, pady=8)
            bubble.pack(anchor="e")
            label = tk.Label(bubble, text=message, font=("Arial", 10), 
                           bg='#dcf8c6', fg='#000', justify='left', wraplength=300)
            label.pack()
            
        else:
            # Tin nhắn đối phương - màu trắng, bên trái
            bubble = tk.Frame(bubble_frame, bg='white', relief='raised', bd=1, padx=12, pady=8)
            bubble.pack(anchor="w")
            label = tk.Label(bubble, text=message, font=("Arial", 10), 
                           bg='white', fg='#000', justify='left', wraplength=300)
            label.pack()
        
        # Cuộn xuống dưới cùng
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # cập nhật danh sách bạn bè
    def update_friend_list_ui(self, entries):
        self.friend_listbox.delete(0, tk.END)
        self.app.user_nick_map.clear()
        for ent in entries:
            if ":" in ent:
                uname, nick = ent.split(":", 1)
            else:
                uname, nick = ent, ent
            self.app.user_nick_map[uname] = nick
            if uname == self.app.username:
                continue
            self.friend_listbox.insert(tk.END, f"{uname}:{nick}")

    # search UI
    def show_search_result(self, uname, nick, friend_flag):
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        
        result_frame = tk.Frame(self.search_result_frame, bg='#f0f8ff', relief='raised', bd=1, padx=10, pady=5)
        result_frame.pack(fill="x", pady=2)
        
        tk.Label(result_frame, text=f"👤 {nick} ({uname})", font=("Arial", 9), 
                bg='#f0f8ff').pack(anchor="w")
        
        if uname == self.app.username:
            tk.Label(result_frame, text="📍 Đây là tài khoản của bạn", font=("Arial", 8), 
                    bg='#f0f8ff', fg='#666').pack(anchor="w")
            return
        
        if friend_flag == "YES":
            tk.Label(result_frame, text="✅ Đã là bạn bè", font=("Arial", 8), 
                    bg='#f0f8ff', fg='#666').pack(anchor="w")
            return
        
        btn = tk.Button(result_frame, text="➕ Kết bạn", font=("Arial", 8),
                       bg='#ff9800', fg='white', relief='flat',
                       command=lambda: self.app.send_line(f"FRIEND_REQUEST {uname}"))
        btn.pack(anchor="w", pady=2)

    def show_search_not_found(self):
        for w in self.search_result_frame.winfo_children():
            w.destroy()
        tk.Label(self.search_result_frame, text="❌ Không tìm thấy tài khoản", 
                font=("Arial", 9), bg='white', fg='#d32f2f').pack(anchor="w")

    def display_incoming_message(self, from_user, msg):
        nick = self.app.user_nick_map.get(from_user, from_user)
        # Tin nhắn từ người khác - hiển thị bên trái
        self._display_message(nick, msg, "left")

    def show_incoming_friend_request(self, from_user, from_nick):
        # Hiển thị yêu cầu kết bạn trong frame
        request_frame = tk.Frame(self.friend_request_frame, bg='#fff3e0', relief='raised', bd=1, padx=10, pady=5)
        request_frame.pack(fill="x", pady=2)
        
        tk.Label(request_frame, text=f"👤 {from_nick} ({from_user})", 
                font=("Arial", 9), bg='#fff3e0').pack(anchor="w")
        
        btn_frame = tk.Frame(request_frame, bg='#fff3e0')
        btn_frame.pack(anchor="e", pady=2)
        
        tk.Button(btn_frame, text="✅", font=("Arial", 9), width=3,
                 bg='#4caf50', fg='white', relief='flat',
                 command=lambda: [self.app.send_line(f"FRIEND_ACCEPT {from_user}"), request_frame.destroy()]).pack(side="left", padx=2)
        
        tk.Button(btn_frame, text="❌", font=("Arial", 9), width=3,
                 bg='#f44336', fg='white', relief='flat',
                 command=lambda: [self.app.send_line(f"FRIEND_REJECT {from_user}"), request_frame.destroy()]).pack(side="left", padx=2)