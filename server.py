import socket
import threading

clients = []

def broadcast(message, sender_socket):
    for client in clients:
        try:
            client.send(message)
        except:
            client.close()
            clients.remove(client)

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            broadcast(message, client_socket)
        except:
            client_socket.close()
            clients.remove(client_socket)
            break

def start_server():
    host = '0.0.0.0'
    port = 8888

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"[+] Server đang chạy tại {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"[+] Client kết nối từ {addr}")
        clients.append(client_socket)
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_server()
