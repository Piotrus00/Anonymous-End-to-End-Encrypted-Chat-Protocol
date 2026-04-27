import socket

def main():
    host = '127.0.0.1'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Serwer nasłuchuje na {host}:{port}")
        conn, addr = s.accept()
        with conn:
            print(f"Połączono z {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Klient: {data.decode()}")
                conn.sendall(b'Wiadomosc otrzymana')

if __name__ == '__main__':
    main()
