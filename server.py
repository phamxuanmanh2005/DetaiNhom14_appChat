import socket
import threading

# Lưu user: username -> (password, nickname)
users = {}

# Lưu client đang online: username -> (conn, addr)
online_clients = {}

lock = threading.Lock()

def broadcast_user_list():
    """Gửi danh sách bạn bè (nickname) cho tất cả client đang online"""
    with lock:
        user_list = "USERLIST " + " ".join(
            [f"{u}:{users[u][1]}" for u in online_clients]
        )
        for conn, _ in online_clients.values():
            try:
                conn.sendall(user_list.encode())
            except:
                pass

def handle_client(conn, addr):
    print(f"Client {addr} connected.")
    username = None
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            parts = data.split()
            cmd = parts[0]

            if cmd == "REGISTER" and len(parts) == 4:
                u, p, n = parts[1], parts[2], parts[3]
                with lock:
                    if u in users:
                        conn.sendall("Tên tài khoản đã tồn tại".encode())
                    else:
                        users[u] = (p, n)
                        conn.sendall("Đăng ký thành công".encode())

            elif cmd == "LOGIN" and len(parts) == 3:
                u, p = parts[1], parts[2]
                with lock:
                    if u in users and users[u][0] == p:
                        username = u
                        online_clients[u] = (conn, addr)
                        conn.sendall(f"OK Chào {users[u][1]}".encode())
                        broadcast_user_list()
                    else:
                        conn.sendall("Sai tài khoản hoặc mật khẩu".encode())

            elif cmd == "MSG" and len(parts) >= 3:
                # Gửi tin nhắn riêng: MSG <to_username> <nội dung>
                to_user = parts[1]
                message = " ".join(parts[2:])
                if to_user in online_clients:
                    to_conn, _ = online_clients[to_user]
                    try:
                        to_conn.sendall(f"MSG {username} {message}".encode())
                    except:
                        conn.sendall("Không gửi được tin nhắn".encode())
                else:
                    conn.sendall("Người này không online".encode())

            else:
                conn.sendall("Lệnh không hợp lệ".encode())

    except Exception as e:
        print("Lỗi:", e)

    finally:
        if username:
            with lock:
                if username in online_clients:
                    del online_clients[username]
                broadcast_user_list()
        conn.close()
        print(f"Client {addr} disconnected.")

def start_server():
    HOST = "127.0.0.1"
    PORT = 12345
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print("Server đang chạy tại", HOST, PORT)

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
