# Wstęp
Niniejszy dokumnet zawiera wynik przeprowadzonych testów, mających na celu ustalenie poprwaności działania oraz bezpieczeństwa protokołu. Testy zostały podzielone na trzy odrębne kategorie, sprawdzające różne aspekty działania. W celu ich przeprowadzenia została użyta aplikacja `WireShark` do analizy przesyłanych pakietów oraz w niekótych przypadkach zmodyfikowany kod aplikacji w celu wymuszenia niepoprawnego działania. Zmiany te nie zostaną upublicznione w finalnej wersji.

# Wyniki testów
## Funkcjonalność
### Weryfikacja, czy Client A może utworzyć sesję wysyłając `INIT` i otrzymując poprawne `session_id` + token JWT.
Zainicjonowanie nowej sesji poprzez wybranie opcji `1`.

#### Logi
**Server**
```bash
[('127.0.0.1', 55554)] Otrzymano: msg_id='msg_001' timestamp=1780671281 type='INIT'
[INIT OK] Utworzona sesja sess_c4ea1d5d7fa1 dla ('127.0.0.1', 55554)
```

**Client A**
```bash
OK Sesja utworzona: sess_c4ea1d5d7fa1

Przekaz session_id drugiemu uzytkownikowi: sess_c4ea1d5d7fa1
[Test] Token po INIT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI
```
#### Wnioski
- Serwer otrzymał `INIT` oraz wysłał poprawnie `session_id` oraz `token JWT`. 
- Klient poprawnie odebrał wiadomość zwrotną.

### Sprawdzenie, czy Client B poprawnie dołącza po wysłaniu `JOIN` z ważnym `session_id`.
Dołączenie do sesji poprzez wybranie opcji `2` oraz podanie `session_id` z poprzedniego testu (*sess_c4ea1d5d7fa1*).

#### Logi
**Server**
```bash
[('127.0.0.1', 53328)] Otrzymano: msg_id='msg_002' timestamp=1780671288 session_id='sess_c4ea1d5d7fa1' type='JOIN'
[JOIN OK] ('127.0.0.1', 53328) dolaczyl do sesji sess_c4ea1d5d7fa1
[SYSTEM] Powiadamiam pierwszego klienta w sesji sess_c4ea1d5d7fa1
```

**Client A**
```bash
[Test] Otrzymana odpowiedz: msg_id='notification' timestamp=1780672216 session_id='sess_c4ea1d5d7fa1' type='JOIN_OK' token=None payload=StatusPayload(status='OK')
[SYSTEM] Drugi uzytkownik dolaczyl do sesji.
```

**Client B**
```bash
OK Dolaczono do sesji: sess_c4ea1d5d7fa1
[Test] Token po JOIN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiNWM5MTFmYjE5MjU5NDUxMWJlMGZjZjQxNzdkZDFhZGEiLCJpYXQiOjE3ODA2NzEyODgsImV4cCI6MTc4MDc1NzY4OH0.3iJum2VEdDZPmxO1eqQ2hPe2GIfotUxhvbqokHHk4yY
```

#### Wnioski
- Serwer otrzymał `JOIN` wraz z poprawnym `session_id`. Wysłał potwierdzenie dołączenia do sesji przez *Client B*.
- Klient B otrzymał potwierdzenie dołączenia do sesji oraz unikalny `token JWT`.
- Klient A otrzymał powiadomienie o dołączeniu Klienta B do sesji.

### Weryfikacja poprawnego przebiegu `KEY_EXCHANGE`.
Test został przeprowadzony w ramach poprzednio utworzonej sesji (*sess_c4ea1d5d7fa1*).

#### Logi
**Server**
```bash
# Client A
[('127.0.0.1', 55554)] Otrzymano: msg_id='kex_8f3c4eb84f8c' timestamp=1780671288 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='KEY_EXCHANGE' payload=KeyExchangePayload(public_key='UOlEJSR0kqR+C6MOoBBQwKi68XNxzG9FFgI0teWEeU4=')
[KEY_EXCHANGE RELAY] ('127.0.0.1', 55554) -> session sess_c4ea1d5d7fa1

# Client B
[('127.0.0.1', 53328)] Otrzymano: msg_id='kex_8ea014d7d440' timestamp=1780671288 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiNWM5MTFmYjE5MjU5NDUxMWJlMGZjZjQxNzdkZDFhZGEiLCJpYXQiOjE3ODA2NzEyODgsImV4cCI6MTc4MDc1NzY4OH0.3iJum2VEdDZPmxO1eqQ2hPe2GIfotUxhvbqokHHk4yY' type='KEY_EXCHANGE' payload=KeyExchangePayload(public_key='MXo43/w5KLlXZLmTJjUtStCjlRnusKJv3REyNK4udW0=')
[KEY_EXCHANGE RELAY] ('127.0.0.1', 53328) -> session sess_c4ea1d5d7fa1
```

**Client A**
```bash
# Wymiana kluczy
[Test] Wysłano klucz publiczny: UOlEJSR0kqR+C6MOoBBQwKi68XNxzG9FFgI0teWEeU4=
[Test] Otrzymana odpowiedz: msg_id='kex_8ea014d7d440' timestamp=1780671288 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiNWM5MTFmYjE5MjU5NDUxMWJlMGZjZjQxNzdkZDFhZGEiLCJpYXQiOjE3ODA2NzEyODgsImV4cCI6MTc4MDc1NzY4OH0.3iJum2VEdDZPmxO1eqQ2hPe2GIfotUxhvbqokHHk4yY' type='KEY_EXCHANGE' payload=KeyExchangePayload(public_key='MXo43/w5KLlXZLmTJjUtStCjlRnusKJv3REyNK4udW0=')
[Test] Otrzymano klucz publiczny: MXo43/w5KLlXZLmTJjUtStCjlRnusKJv3REyNK4udW0=
[SYSTEM] Wymiana kluczy zakonczona. Mozna rozmawiac (E2EE).
```

**Client B**
```bash
# Wymiana kluczy
[SYSTEM] Rozpoczynam wymiane kluczy...
[Test] Wysłano klucz publiczny: MXo43/w5KLlXZLmTJjUtStCjlRnusKJv3REyNK4udW0=
[Test] Otrzymana odpowiedz: msg_id='kex_8f3c4eb84f8c' timestamp=1780671288 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='KEY_EXCHANGE' payload=KeyExchangePayload(public_key='UOlEJSR0kqR+C6MOoBBQwKi68XNxzG9FFgI0teWEeU4=')
[Test] Otrzymano klucz publiczny: UOlEJSR0kqR+C6MOoBBQwKi68XNxzG9FFgI0teWEeU4=
[SYSTEM] Wymiana kluczy zakonczona. Mozna rozmawiac (E2EE).
```

#### Wnioski
- Obja klienci poprawnie wysłali oraz odebrali klucze publicznie.
- Obydwa kluzce są unikalne.
- Serwer porawnie przekierował wiadomości.

### Weryfikacja poprawnego wysłania wiadomości `MSG` oraz potwierdzenia odbioru `ACK`.
Test został przeprowadzony w ramach poprzednio utworzonej sesji (*sess_c4ea1d5d7fa1*). Wiadomość została wysłana przez *clienta A*

#### Logi
**Server**
```bash
# Wiadomość A -> B
[('127.0.0.1', 55554)] Otrzymano: msg_id='msg_61442f20d881' timestamp=1780671331 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='MSG' payload=CiphertextPayload(ciphertext='LSWoZviQkJPVhEM0V/OHTA9fe5937POFel3zctwj2IvIvu6V1ZQjNRihmQ4aB/xv9Q==')
[MSG RELAY] ('127.0.0.1', 55554) -> session sess_c4ea1d5d7fa1

# Potwierdzenie odbioru B -> A
[('127.0.0.1', 53328)] Otrzymano: msg_id='ack_cfc13383bb9e' timestamp=1780671331 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiNWM5MTFmYjE5MjU5NDUxMWJlMGZjZjQxNzdkZDFhZGEiLCJpYXQiOjE3ODA2NzEyODgsImV4cCI6MTc4MDc1NzY4OH0.3iJum2VEdDZPmxO1eqQ2hPe2GIfotUxhvbqokHHk4yY' type='ACK' payload=AckPayload(acked_msg_id='msg_61442f20d881')
[ACK RELAY] ('127.0.0.1', 53328) -> session sess_c4ea1d5d7fa1
```

**Client A**
```bash
# Wysłanie wiadomości
Ty: Wiadomosc od Client A
[Test] Ramka wysłana w ramach wiadomości o id msg_61442f20d881: msg_id='msg_61442f20d881' timestamp=1780671331 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='MSG' payload=CiphertextPayload(ciphertext='LSWoZviQkJPVhEM0V/OHTA9fe5937POFel3zctwj2IvIvu6V1ZQjNRihmQ4aB/xv9Q==')

# Otrzymanie potwierdzenie odebrania wiadomości
Ty: [Test] Otrzymana odpowiedz: msg_id='ack_cfc13383bb9e' timestamp=1780671331 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiNWM5MTFmYjE5MjU5NDUxMWJlMGZjZjQxNzdkZDFhZGEiLCJpYXQiOjE3ODA2NzEyODgsImV4cCI6MTc4MDc1NzY4OH0.3iJum2VEdDZPmxO1eqQ2hPe2GIfotUxhvbqokHHk4yY' type='ACK' payload=AckPayload(acked_msg_id='msg_61442f20d881')
[SYSTEM] Otrzymano potwierdzenie dla msg_61442f20d881
```

**Client B**
```bash
# Otrzymianie wiadomości
[Test] Otrzymana odpowiedz: msg_id='msg_61442f20d881' timestamp=1780671331 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='MSG' payload=CiphertextPayload(ciphertext='LSWoZviQkJPVhEM0V/OHTA9fe5937POFel3zctwj2IvIvu6V1ZQjNRihmQ4aB/xv9Q==')
[MSG] Wiadomosc od Client A

# Wysłanie potwierdzenie otrzymiania wiadomości
[Test] Ramka wysłana w ramach potwierdzenie dla id msg_61442f20d881: msg_id='ack_cfc13383bb9e' timestamp=1780671331 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiNWM5MTFmYjE5MjU5NDUxMWJlMGZjZjQxNzdkZDFhZGEiLCJpYXQiOjE3ODA2NzEyODgsImV4cCI6MTc4MDc1NzY4OH0.3iJum2VEdDZPmxO1eqQ2hPe2GIfotUxhvbqokHHk4yY' type='ACK' payload=AckPayload(acked_msg_id='msg_61442f20d881')
```

#### Wnioski
- Client A poprawnie wysłał wiadomość oraz odebrał powtierdzenie.
- Client B poprawnie odebrał wiadomość, rozkodował jej zawartość oraz wysłał potwierdzenie.
- Serwer poprawnie przekierował wiadomość jak i potwierdzenie jej odebrania.

### Poprawne obsłużenie `CLOSE` i wyrejestrowanie sesji.
Zamknięcie poprzednio utworzonej sesji (*sess_c4ea1d5d7fa1*) zainicjowane przez *clienta A*.

#### Logi
**Server**
```bash
# Otrzymania 'CLOSE' od CLient A
[('127.0.0.1', 55554)] Otrzymano: msg_id='close_80c4338b3d7c' timestamp=1780671349 session_id='sess_c4ea1d5d7fa1' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='CLOSE'
[CLOSE OK] Zamknieto sesje sess_c4ea1d5d7fa1
```

**Client A**
```bash
# Komenda zamykająca sesje
exit

# Potwierdzenie od serwera
[Test] Otrzymana odpowiedz: msg_id='close_80c4338b3d7c' timestamp=1780671349 session_id='sess_c4ea1d5d7fa1' type='CLOSE_NOTICE' payload=StatusPayload(status='SESSION_CLOSED')
[CLOSE] Sesja sess_c4ea1d5d7fa1 zostala zamknieta
[SYSTEM] Petla odbiornika zakonczona.
```

**Client B**
```bash
[Test] Otrzymana odpowiedz: msg_id='close_80c4338b3d7c' timestamp=1780671349 session_id='sess_c4ea1d5d7fa1' type='CLOSE_NOTICE' payload=StatusPayload(status='SESSION_CLOSED')
[CLOSE] Sesja sess_c4ea1d5d7fa1 zostala zamknieta
[SYSTEM] Petla odbiornika zakonczona.
```

#### Wnioski
- Client A poprawnie wysłał wiadomość, `CLOSE` do serwera.
- Serwer poprawnie rozgłosił zamknięcie sesji.
- Client A oraz B odebrali `CLOSE_NOTICE` o zamknięciu sesji.

## Bezpieczeństwo

### Przechwycenie ruchu na serwerze — upewnienie się, że `ciphertext` jest nieczytelny bez kluczy prywatnych klientów.
Posługująć sie logami z poprzedniego testu, możemy zobaczyć zawartość wiadomości w ramach `MSG` oraz klucze nadesłane przez obu klientów.

#### Logi
**Zawartość `MSG`**
```bash
# Klucz Client A
(... type='KEY_EXCHANGE' payload=KeyExchangePayload(public_key='UOlEJSR0kqR+C6MOoBBQwKi68XNxzG9FFgI0teWEeU4=')

# Klucz Client B
(... type='KEY_EXCHANGE' payload=KeyExchangePayload(public_key='MXo43/w5KLlXZLmTJjUtStCjlRnusKJv3REyNK4udW0=')

# Wiadomość
(... type='MSG' payload=CiphertextPayload(ciphertext='LSWoZviQkJPVhEM0V/OHTA9fe5937POFel3zctwj2IvIvu6V1ZQjNRihmQ4aB/xv9Q==')
```

#### Wnioski
- Zawartość wiadomości trafia na serwer w zaszyforwanej formie.
- Podaczas komunikacji nie są przesyłane klucze umożliwiające odczytanie zawartości.

### Weryfikacja wymuszenia TLS na warstwie transportowej.
Do weryfikacji protokołu na warstwie transportowej wykorzystany został `WireShark`.

![Logi WireShark](./images/wireshark_logs.png)

![Logi Nmap](./images/nmap.jpg)

![Logi Nmap2](./images/nmap2.jpg)



#### Wnioski
- TLS jest wykorzystywane w warstwie transportowej.

## Obsługa błędów
### Wysłanie niepoprawnego JSON lub brak wymaganych pól — sprawdzenie błędu.
*Client B* próbuje wysłać `KEY_EXCHANGE` bez zawartości.

#### Logi
**Server**
```bash
[('127.0.0.1', 54404)] Blad: Otrzymano niepoprawny JSON
```

**Client B**
```bash
[ERROR] Niepoprawny format wiadomosci JSON
```

#### Wnisoki
- Nie jest możliwe kontynuowanie komunikacji po przesłaniu niepoprawnego JSON-a.

### Wysłanie `MSG` z nieprawidłowym lub wygasłym tokenem JWT — sprawdzenie odrzucenia.
*Client B* przy próbie wysłania wiadomości używa tokenu z innej sesji.

#### Logi
**Server**
```bash
# Wysłanie wiadomości przez Clienta A
[('127.0.0.1', 39088)] Otrzymano: msg_id='msg_ffe8f2a5d01c' timestamp=1780676838 session_id='sess_c92fd59eecd5' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M5MmZkNTllZWNkNSIsInBjIjoiMGE5YTZkNjhlZGRlNDBjM2I1YmM0MzljZWVjOGE3ZGUiLCJpYXQiOjE3ODA2NzY4MTIsImV4cCI6MTc4MDc2MzIxMn0.LI67osVXr5ycfgVtBR9jr2WgtPMWd_7gyBwB3aLESn0' type='MSG' payload=CiphertextPayload(ciphertext='ya24PCBT/VPBuJJzSSrYU6YCwNjG5VXhUMZFAIIXZ3PxVKtj5ym0aMre')
[MSG RELAY] ('127.0.0.1', 39088) -> session sess_c92fd59eecd5

# Potwierdzenie otrzymiania wiadomości przez Clienta B
[('127.0.0.1', 57488)] Otrzymano: msg_id='ack_921132f5ecbb' timestamp=1780676838 session_id='sess_c92fd59eecd5' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M5MmZkNTllZWNkNSIsInBjIjoiOTExMzQ0ZDZjMTYxNDRmZGE2NzlkNzBkY2IyN2JjOTgiLCJpYXQiOjE3ODA2NzY4MjQsImV4cCI6MTc4MDc2MzIyNH0.QYc5MLU9ywwnKnFDZ5ckdLYyut_r6cpISjKNeQZ5_eY' type='ACK' payload=AckPayload(acked_msg_id='msg_ffe8f2a5d01c')
[ACK RELAY] ('127.0.0.1', 57488) -> session sess_c92fd59eecd5

# Wysłanie wiadomości przez Clienta B z niepoprawnym tokenem
[('127.0.0.1', 57488)] Otrzymano: msg_id='msg_215d8f47d7a7' timestamp=1780676851 session_id='sess_c92fd59eecd5' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='MSG' payload=CiphertextPayload(ciphertext='U70VdQ2EoOxsRh4gidMO9+ypFskAFEv11d0Tldz3HWBuWx8C0aIb18+Y')
```

**Client A**
```bash
# Otrzymianie potwierdzenia
[Test] Otrzymana odpowiedz: msg_id='ack_921132f5ecbb' timestamp=1780676838 session_id='sess_c92fd59eecd5' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M5MmZkNTllZWNkNSIsInBjIjoiOTExMzQ0ZDZjMTYxNDRmZGE2NzlkNzBkY2IyN2JjOTgiLCJpYXQiOjE3ODA2NzY4MjQsImV4cCI6MTc4MDc2MzIyNH0.QYc5MLU9ywwnKnFDZ5ckdLYyut_r6cpISjKNeQZ5_eY' type='ACK' payload=AckPayload(acked_msg_id='msg_ffe8f2a5d01c')

# Odrzucenie wiadomości z niepoprawnym tokenem
[SYSTEM] Otrzymano potwierdzenie dla msg_ffe8f2a5d01c
```

**Client B**
```bash
# Potwierdzenie otrzymiania wiadomości od Clienta A
[Test] Ramka wysłana w ramach potwierdzenie dla id msg_ffe8f2a5d01c: msg_id='ack_921132f5ecbb' timestamp=1780676838 session_id='sess_c92fd59eecd5' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M5MmZkNTllZWNkNSIsInBjIjoiOTExMzQ0ZDZjMTYxNDRmZGE2NzlkNzBkY2IyN2JjOTgiLCJpYXQiOjE3ODA2NzY4MjQsImV4cCI6MTc4MDc2MzIyNH0.QYc5MLU9ywwnKnFDZ5ckdLYyut_r6cpISjKNeQZ5_eY' type='ACK' payload=AckPayload(acked_msg_id='msg_ffe8f2a5d01c')

# Próba wysłania wiadomości z niepoprawnym tokenem
Wiadomosc od B
[Test] Ramka wysłana w ramach wiadomości o id msg_215d8f47d7a7: msg_id='msg_215d8f47d7a7' timestamp=1780676851 session_id='sess_c92fd59eecd5' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJzZXNzX2M0ZWExZDVkN2ZhMSIsInBjIjoiZTA5Njc5YzkxYmE4NDlmYTk3YTkzZDk1ZTgzYWM1MWYiLCJpYXQiOjE3ODA2NzEyODEsImV4cCI6MTc4MDc1NzY4MX0.XA0VbB8_Ot9kKMrXNa6tTbPtt4Jn-2q_Cad-sUVQOBI' type='MSG' payload=CiphertextPayload(ciphertext='U70VdQ2EoOxsRh4gidMO9+ypFskAFEv11d0Tldz3HWBuWx8C0aIb18+Y')

# Odrzucenie wiadomości
[Test] Otrzymana odpowiedz: type='ERROR' error_code='ERROR_INVALID_TOKEN' details='Token nie pasuje do session_id w wiadomosci'
[ERROR] Token nie pasuje do session_id w wiadomosci
[SYSTEM] Nie otrzymano potwierdzenia dla wiadomosci msg_215d8f47d7a7
```

#### Wnioski
- Próba wysłania wiadomości z niepoprawnym tokenem jest możliwa ale drugi klient ją odrzuca.

### Obsługa timeout i utraty połączenia.
*Client B* zostaje wyłączony po dołączeniu do sesji.

#### Logi
**Server**
```bash
[ROZLACZONO] ('127.0.0.1', 55520)
```

**Client A**
```bash
[Test] Otrzymana odpowiedz: type='ERROR' error_code='ERROR_DISCONNECTED' details='Drugi uczestnik utracil polaczenie.'
[ERROR] Drugi uczestnik utracil polaczenie.
```

#### Wnioski
- Utrata połączenia jest wyłapywana przez system.
