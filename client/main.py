import socket
import json
import time

def main():
    host = '127.0.0.1'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print("Połączono z serwerem! Wpisz 'exit', aby zakończyć test.")

        while True:
            # Klient czeka na wpisanie tekstu, utrzymując w tym czasie połączenie
            wpisany_tekst = input("\nWpisz wiadomość (lub 'exit'): ")

            if wpisany_tekst.lower() == 'exit':
                print("Zamykanie klienta...")
                break

            # Tworzymy wiadomość jako słownik z podstawowymi polami
            message_data = {
                "type": "MSG",
                "session_id": "testowa_sesja",
                "msg_id": "1",
                "timestamp": int(time.time()), # Zawsze aktualny timestamp
                "payload": {
                    "ciphertext": wpisany_tekst
                }
            }

            # Zamieniamy słownik na format JSON i kodujemy na bajty
            json_string = json.dumps(message_data)
            s.sendall(json_string.encode('utf-8'))

            # Oczekujemy na odpowiedź serwera
            data = s.recv(1024)
            if data:
                response_data = json.loads(data.decode('utf-8'))
                print(f"Odpowiedź z serwera: {response_data}")

if __name__ == '__main__':
    main()