import socket
import threading

# Cấu hình server để kết nối
HOST = '127.0.0.1'
PORT = 55555

# Nhập nickname
nickname = input("Chọn nickname của bạn: ")

# Khởi tạo socket và kết nối
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive():
    """Nhận tin nhắn từ server"""
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            else:
                print(message)
        except:
            # Ngắt kết nối và thoát
            print("Đã xảy ra lỗi!")
            client.close()
            break

def write():
    """Gửi tin nhắn đến server"""
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('utf-8'))

# Tạo hai luồng: một để nhận và một để gửi
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()