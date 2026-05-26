import socket
import json
import time

def main():
    host = '127.0.0.1'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print("Połączono z serwerem!")

        # Wysyłamy INIT - tworzymy nową sesję
        init_message = {
            "type": "INIT",
            "msg_id": "msg_001",
            "timestamp": int(time.time())
        }

        print("\n→ Wysyłam INIT...")
        s.sendall(json.dumps(init_message).encode('utf-8'))

        # Odbieramy odpowiedź (session_id)
        data = s.recv(1024)
        session_id = None
        if data:
            response_data = json.loads(data.decode('utf-8'))
            print(f"\n✓ Odpowiedź z serwera:")
            print(f"  Type: {response_data.get('type')}")
            session_id = response_data.get('session_id')
            print(f"  Session ID: {session_id}")
            print(f"  Status: {response_data.get('payload', {}).get('status')}")

        print("\nWpisz 'exit', aby zakończyć test, lub wysyłaj wiadomości.")

        while True:
            # Klient czeka na wpisanie tekstu, utrzymując w tym czasie połączenie
            wpisany_tekst = input("\nWpisz wiadomość (lub 'exit'): ")

            if wpisany_tekst.lower() == 'exit':
                print("Zamykanie klienta...")
                break

            # Tworzymy wiadomość jako słownik z podstawowymi polami
            message_data = {
                "type": "MSG",
                "session_id": session_id,
                "msg_id": f"msg_{int(time.time())}",
                "timestamp": int(time.time()),
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