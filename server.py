import socket
import threading
from data_store import users, lock, save_user

HOST = "127.0.0.1"
PORT = 12345

clients = {}    # username -> socket

def handle_client(conn, addr):
    username = None
    buf = ""
    try:
        while True:
            data = conn.recv(4096).decode()
            if not data:
                break
            buf += data
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if not line.strip():
                    continue
                parts = line.strip().split()
                cmd = parts[0].upper()

                # REGISTER
                if cmd == "REGISTER" and len(parts) == 4:
                    u, p, n = parts[1], parts[2], parts[3]
                    with lock:
                        if u in users:
                            conn.sendall("ERR Username exists\n".encode())
                        else:
                            users[u] = {"password": p, "nickname": n, "friends": set(), "pending": set()}
                            save_user(u, p, n)
                            conn.sendall("REGISTER_OK\n".encode())

                # LOGIN
                elif cmd == "LOGIN" and len(parts) == 3:
                    u, p = parts[1], parts[2]
                    with lock:
                        if u not in users or users[u]["password"] != p:
                            conn.sendall("ERR Invalid login\n".encode())
                        else:
                            username = u
                            clients[username] = conn
                            conn.sendall(f"LOGIN_OK {users[u]['nickname']}\n".encode())
                            
                            # Gửi các lời mời kết bạn đang chờ
                            for pending_user in users[username]["pending"]:
                                if pending_user in users:
                                    conn.sendall(f"FRIEND_REQ {pending_user} {users[pending_user]['nickname']}\n".encode())
                            
                            # gửi danh sách bạn bè online
                            friend_list = []
                            for f in users[username]["friends"]:
                                if f in users:
                                    friend_list.append(f"{f}:{users[f]['nickname']}")
                            conn.sendall(("USERLIST " + " ".join(friend_list) + "\n").encode())

                # MSG
                elif cmd == "MSG" and len(parts) >= 3:
                    if not username:
                        continue
                    to_user = parts[1]
                    msg_text = " ".join(parts[2:])
                    if to_user in clients:
                        clients[to_user].sendall(f"MSG {username} {msg_text}\n".encode())
                    else:
                        conn.sendall(f"ERR {to_user} not online\n".encode())

                # SEARCH
                elif cmd == "SEARCH" and len(parts) >= 2:
                    if not username:
                        continue
                    query = parts[1].lower()
                    found = False
                    with lock:
                        for u, info in users.items():
                            if query in u.lower() or query in info["nickname"].lower():
                                friend_flag = "YES" if u in users[username]["friends"] else "NO"
                                conn.sendall(f"SEARCH_OK {u} {info['nickname']} friend={friend_flag}\n".encode())
                                found = True
                    if not found:
                        conn.sendall("SEARCH_NOT_FOUND\n".encode())

                # FRIEND_REQUEST
                elif cmd == "FRIEND_REQUEST" and len(parts) == 2:
                    target = parts[1]
                    with lock:
                        if target in users:
                            if target in clients:
                                clients[target].sendall(f"FRIEND_REQ {username} {users[username]['nickname']}\n".encode())
                                conn.sendall(f"FRIEND_REQUEST_SENT {target}\n".encode())
                            else:
                                users[target]["pending"].add(username)
                                conn.sendall(f"FRIEND_REQUEST_STORED {target}\n".encode())

                # FRIEND_ACCEPT
                elif cmd == "FRIEND_ACCEPT" and len(parts) == 2:
                    from_user = parts[1]
                    with lock:
                        # Xóa khỏi pending list
                        if from_user in users[username]["pending"]:
                            users[username]["pending"].remove(from_user)
                        
                        # Thêm vào danh sách bạn bè của cả hai
                        users[username]["friends"].add(from_user)
                        users[from_user]["friends"].add(username)

                        # Gửi thông báo FRIEND_ACCEPTED cho người gửi lời mời
                        if from_user in clients:
                            clients[from_user].sendall(
                                f"FRIEND_ACCEPTED {username} {users[username]['nickname']}\n".encode()
                            )
                            # Cập nhật danh sách bạn bè online cho người gửi lời mời
                            friend_list_to_sender = [
                                f"{f}:{users[f]['nickname']}" for f in users[from_user]["friends"] if f in users
                            ]
                            clients[from_user].sendall(
                                ("USERLIST " + " ".join(friend_list_to_sender) + "\n").encode()
                            )

                        # Cập nhật danh sách bạn bè online cho người vừa accept
                        friend_list_to_acceptor = [
                            f"{f}:{users[f]['nickname']}" for f in users[username]["friends"] if f in users
                        ]
                        if username in clients:
                            clients[username].sendall(
                                ("USERLIST " + " ".join(friend_list_to_acceptor) + "\n").encode()
                            )

                # FRIEND_REJECT
                elif cmd == "FRIEND_REJECT" and len(parts) == 2:
                    from_user = parts[1]
                    with lock:
                        # Xóa khỏi pending list
                        if from_user in users[username]["pending"]:
                            users[username]["pending"].remove(from_user)
                    if from_user in clients:
                        clients[from_user].sendall(f"FRIEND_REJECTED {username}\n".encode())

                else:
                    conn.sendall("ERR Invalid command\n".encode())

    except Exception as e:
        print(f"Lỗi từ client {addr}: {e}")
    finally:
        if username and username in clients:
            del clients[username]
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server đang chạy tại {HOST}:{PORT} ...")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
