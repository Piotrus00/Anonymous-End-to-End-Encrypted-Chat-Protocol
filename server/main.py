import socket
import threading
import json
import uuid

# Słownik sesji: session_id -> lista klientów
sessions = {}
sessions_lock = threading.Lock()

def handle_client(conn, addr):
    print(f"[NOWE POŁĄCZENIE] Połączono z {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break # Klient się rozłączył

                # 1. Odkodowanie wiadomości i parsowanie JSON
                message_str = data.decode('utf-8')
                message_json = json.loads(message_str)
                print(f"[{addr}] Otrzymano: {message_json}")

                # 2. Przygotowanie odpowiedzi w formacie JSON
                # Obsługa INIT - tworzymy nową sesję
                if message_json.get('type') == 'INIT':
                    session_id = f"sess_{uuid.uuid4().hex[:12]}"

                    with sessions_lock:
                        sessions[session_id] = [addr]

                    response = {
                        "type": "INIT",
                        "session_id": session_id,
                        "msg_id": message_json.get("msg_id"),
                        "timestamp": message_json.get("timestamp"),
                        "payload": {
                            "status": "OK"
                        }
                    }

                    print(f"[INIT OK] Utworzona sesja {session_id} dla {addr}")
                else:
                    response = {
                        "status": "OK",
                        "info": "Wiadomość odebrana przez serwer"
                    }

                # 3. Zakodowanie JSON do wysłania
                conn.sendall(json.dumps(response).encode('utf-8'))

            except json.JSONDecodeError:
                print(f"[{addr}] Błąd: Otrzymano niepoprawny JSON")
                break
            except ConnectionResetError:
                break

    print(f"[ROZŁĄCZONO] Koniec połączenia z {addr}")

def main():
    host = '127.0.0.1'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[START] Serwer nasłuchuje na {host}:{port}")

        while True:
            # Serwer czeka na klienta
            conn, addr = s.accept()

            # Gdy klient się połączy, tworzymy nowy wątek dla niego
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[AKTYWNE POŁĄCZENIA] Wątki: {threading.active_count() - 1}")

if __name__ == '__main__':
    main()