import socket
import threading

# Cấu hình server
HOST = '127.0.0.1'  # Địa chỉ IP của server (localhost)
PORT = 55555        # Cổng kết nối

# Khởi tạo socket và bind địa chỉ
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
nicknames = []

def broadcast(message):
    """Gửi tin nhắn đến tất cả các client"""
    for client in clients:
        client.send(message)

def handle_client(client):
    """Xử lý kết nối từ một client cụ thể"""
    while True:
        try:
            # Nhận tin nhắn từ client
            message = client.recv(1024)
            print(message.decode('utf-8')) # In tin nhắn ra console server
            broadcast(message)
        except:
            # Xóa client khi mất kết nối
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f'{nickname} đã rời khỏi phòng chat!'.encode('utf-8'))
            nicknames.remove(nickname)
            break

def receive():
    """Chấp nhận các kết nối mới"""
    while True:
        client, address = server.accept()
        print(f"Đã kết nối với {str(address)}")

        # Yêu cầu client nhập nickname
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname của client là: {nickname}')
        broadcast(f'{nickname} đã tham gia phòng chat!'.encode('utf-8'))
        client.send('Đã kết nối tới server!'.encode('utf-8'))

        # Tạo luồng mới để xử lý client
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

print("Server đang chạy và chờ kết nối...")
receive()