# Anonymous-End-to-End-Encrypted-Chat-Protocol

<details open>
<summary><h2> Etap I</h2></summary>

## 1. Cel protokołu i zakres

### Do czego służy protokół?

Protokół służy do realizacji anonimowej, szyfrowanej komunikacji tekstowej pomiędzy dwoma użytkownikami za pośrednictwem serwera pośredniczącego.

Treść wiadomości pozostaje niedostępna dla serwera dzięki szyfrowaniu end-to-end realizowanemu po stronie klienta.

### Jakie problemy rozwiązuje?

- anonimowość dla użytkowników,
- brak trwałych danych użytkownika — użytkownik identyfikowany jest wyłącznie tokenem sesyjnym.

### W jakim modelu działa?

- Client–Server.

## 2. Założenia techniczne

### Transport

- Ethernet / Wi‑Fi,
- IP,
- TCP,
- WebSocket,
- TLS dla bezpieczeństwa.

### Kodowanie wiadomości

- JSON.

### Niezawodność

- TCP zapewnia dostarczanie danych w kolejności i bez strat,
- warstwa aplikacyjna odpowiada za kontrolę stanu sesji, timeout połączenia i keep-alive sesji.

## 3. Struktura komunikatów

### Typy wiadomości

- `INIT` — utworzenie sesji,
- `JOIN` — dołączenie do sesji,
- `KEY_EXCHANGE` — wymiana kluczy,
- `MSG` — przesyłanie wiadomości,
- `SYN/ACK` — w TCP, do potwierdzenia odbioru wiadomości,
- `PING` — keep-alive,
- `CLOSE` — zamknięcie sesji,
- `ERROR` — w razie błędów.

### Pola wiadomości

- `type` — obowiązkowe,
- `session_id` — obowiązkowe [poza `INIT`],
- `msg_id` — obowiązkowe,
- `timestamp` — obowiązkowe,
- `token` — obowiązkowe [poza `INIT` / `JOIN`],
- `payload` — opcjonalnie.

### Format przykładowej ramki

```json
{
  "type": "MSG",
  "session_id": "sess_12345",
  "msg_id": "msg_uuid",
  "timestamp": 123,
  "token": "jwt_token",
  "payload": {
	"ciphertext": "ertantydfzx4wertm"
  }
}
```

### Walidacja

- niepoprawny JSON,
- brak wymaganych pól lub niepoprawne pola (zły token, `session_id`).

## 4. Model stanów / przebieg komunikacji

### Opis sesji

Nawiązanie połączenia → autoryzacja → wymiana danych → zamknięcie.

Przebieg:

1. nawiązanie połączenia TCP,
2. handshake TLS,
3. utworzenie sesji (`INIT`),
4. dołączenie do sesji (`JOIN`),
5. otrzymanie tokenów JWT,
6. sprawdzenie zgodności `session_id` (serwer),
7. walidacja tokenów (serwer),
8. wymiana kluczy (`KEY_EXCHANGE`),
9. komunikacja szyfrowana (`MSG`),
10. zamknięcie sesji.

### Diagram stanów / diagram sekwencji

![Diagram sekwencji](docs/images/Diagram%20sekwencji.png)

![Diagram stanów](docs/images/Diagram%20stanów.png)

### Timeouty, retransmisje / retry, keep-alive

**Timeout połączenia:**

Jeżeli klient:

- nie wyśle żadnej wiadomości,
- ani nie odpowie na `PING`

przez określony czas, połączenie uznawane jest za utracone.

**Keep-alive:**

- serwer wysyła ping,
- jeżeli klient nie odpowie 3 razy pod rząd, sesja zostaje zamknięta.

## 5. Bezpieczeństwo

### Jak realizowane jest bezpieczeństwo komunikacji

#### Poufność

- TLS,
- szyfrowanie end-to-end.

#### Integralność

- podpis JWT.

#### Uwierzytelnienie

- token JWT.

#### Autoryzacja

- na podstawie JWT.

#### Ochrona przed replay

- `msg_id`,
- `timestamp`.

#### Krótki model zagrożeń

- MITM attack,
- odczyt wiadomości przez serwer,
- fałszywy token.

## 6. Obsługa błędów i awarii połączenia

### Kody błędów i ich znaczenie

| Kod błędu | Znaczenie |
| --- | --- |
| `ERROR_BAD_JSON` | Niepoprawny format wiadomości |
| `ERROR_MISSING_FIELD` | Brak wymaganego pola |
| `ERROR_INVALID_TOKEN` | Niepoprawny lub wygasły JWT |
| `ERROR_SESSION_NOT_FOUND` | Sesja nie istnieje |
| `ERROR_TIMEOUT` | Timeout połączenia |
| `ERROR_DISCONNECTED` | Drugi uczestnik utracił połączenie |
| `ERROR_MESSAGE_TOO_LARGE` | Zbyt duża wiadomość |

### Zachowanie po błędach składni / protokołu

- serwer odrzuca wiadomość i wysyła komunikat błędu.

### Timeout połączenia

Serwer co określony czas wysyła `PING` i oczekuje na odpowiedzi od użytkowników. Jeżeli po 3-krotnym wykonaniu tej operacji serwer nie otrzyma odpowiedzi, zamyka połączenie.

### Utrata połączenia w trakcie sesji

- jak w punkcie o timeoutach.

### Duplikaty / niekompletne wiadomości

- zabezpieczenie w postaci `timestamp` i `msg_id` ma temu zapobiegać.

### Limity i ochrona przed nadużyciami

- ograniczony rozmiar wiadomości,
- ograniczona ilość wiadomości w krótkim czasie.

## 7. Przykładowe scenariusze komunikacji

### Minimum 2–3 kompletne przykłady

![Scenariusz 1](docs/images/Scenariusz%201.png)

![Scenariusz 2](docs/images/Scenariusz%202.png)

</details>

