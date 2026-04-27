import socket

def main():
    host = '127.0.0.1'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        message = "Czesc serwer!"
        s.sendall(message.encode())
        data = s.recv(1024)

    print(f"Serwer: {data.decode()}")

if __name__ == '__main__':
    main()
