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
- ani nie odpowie na ping WebSocket

przez określony czas, połączenie uznawane jest za utracone.

**Keep-alive:**

- keep-alive realizowany jest przez WebSocket ping/pong,
- brak odpowiedzi przez kilka interwałów powoduje rozłączenie.

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

Keep-alive realizowany jest przez WebSocket ping/pong. Jeżeli klient nie odpowiada przez kilka interwałów, połączenie zostaje zamknięte.

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

<details open>
<summary><h2> Etap II </h2></summary>

## 1. Opis funkcjonalny aplikacji

### Co aplikacja robi?

Aplikacja umożliwia anonimową, szyfrowaną komunikację pomiędzy dwoma użytkownikami.

### Jaki problem użytkownika rozwiązuje?

Aplikacja rozwiązuje problem bezpiecznej komunikacji pomiędzy użytkownikami.

### Kto jest użytkownikiem (aktorzy)?

- **Client A** — tworzy sesję,
- **Client B** — dołącza do sesji,
- **Serwer** — zarządzanie sesjami.

## 2. Architektura rozwiązania

### Model

- Client–Server.

### Komponenty

- CLI,
- serwer,
- moduł autoryzacji (token JWT),
- klient A,
- klient B.

### Diagram komponentów / wdrożenia

![Diagram wdrożenia](docs/images/Diagram%20wdrożenia.png)


### Przepływ danych między komponentami.

- Opiera się na podziale na widoczne metadane i ukrytą treść.
- Klienci łączą się z serwerem, który przechowuje w ulotnej pamięci tylko tymczasowe identyfikatory sesji oraz tokeny JWT dla autoryzacji.
- Serwer pełni rolę listonosza — odczytuje tylko nagłówki komunikatów, aby wiedzieć, do kogo je skierować.
- Treść konwersacji (pole `payload`) przesyłana jest jako `ciphertext` i przepływa przez serwer w formie całkowicie dla niego nieczytelnej dzięki szyfrowaniu end-to-end.

## 3. Przypadki użycia (use cases)

### UC1: Utworzenie nowej, anonimowej sesji komunikacyjnej

**Cel:**
Rozpoczęcie nowej, prywatnej i anonimowej sesji komunikacyjnej, do której może dołączyć drugi użytkownik.

**Aktor:**
Użytkownik A (inicjujący sesję)

**Warunki wstępne:**
- Użytkownik A posiada dostęp do aplikacji klienta,
- serwer relay jest dostępny.

**Scenariusz główny:**
1. Użytkownik A wysyła żądanie `INIT` do serwera,
2. serwer generuje unikalny `session_id` oraz token JWT dla użytkownika A,
3. serwer zwraca użytkownikowi A: `session_id` i JWT,
4. aplikacja prezentuje użytkownikowi A `session_id` do przekazania zaproszonej osobie.

**Scenariusze alternatywne / błędy:**
- Serwer nieosiągalny → zwrot błędu, brak sesji,
- brak zasobów serwera → komunikat błędu,
- żądanie niepoprawne (np. błędny format) → komunikat błędu.

**Wynik końcowy:**
Użytkownik A dysponuje nowym `session_id` oraz tokenem JWT. Jest gotów do nawiązania anonimowej sesji.

### UC2: Dołączenie do istniejącej sesji komunikacyjnej

- **Cel:** anonimowe zestawienie dialogu między dwoma klientami,
- **Aktor:** Client B,
- **Warunki wstępne:** Server ma aktywną sesję, Client B zna `session_id`,
- **Scenariusz główny:** wysłanie `JOIN` z ważnym `session_id` → otrzymanie tokenu JWT,
- **Scenariusze alternatywne:** niepoprawny `session_id`, sesja wygasła,
- **Wynik końcowy:** obaj klienci są w sesji i gotowi do wymiany kluczy.

### UC3: Wysyłanie anonimowych i szyfrowanych wiadomości tekstowych

**Cel:**
Bezpieczna, anonimizowana komunikacja pomiędzy uczestnikami sesji (A ↔ B), bez ujawniania treści serwerowi.

**Aktorzy:**
Użytkownik A i Użytkownik B

**Warunki wstępne:**
- Obaj uczestnicy mają aktywny JWT i wspólne `session_id`,
- pomyślnie przeprowadzona wymiana kluczy szyfrujących (key exchange),
- ustanowione szyfrowanie end-to-end.

**Scenariusz główny:**
1. Użytkownik A szyfruje wiadomość wynegocjowanym kluczem,
2. A przesyła zaszyfrowany komunikat typu `MSG` wraz z JWT do serwera,
3. serwer weryfikuje poprawność JWT, znajduje adresata po `session_id`,
4. serwer przesyła wiadomość do B,
5. B otrzymuje wiadomość, odszyfrowuje ją lokalnie tym samym kluczem,
6. analogiczny przebieg dla A i B na zmianę.

**Scenariusze alternatywne / błędy:**
- Nieprawidłowy / wygaśnięty JWT → serwer odrzuca żądanie, zwraca błąd,
- wiadomość nie da się doręczyć (np. drugi użytkownik offline) → buforowanie lub błąd,
- błąd deszyfrowania po stronie klienta → komunikat o uszkodzonej wiadomości,
- przekroczony limit długości wiadomości → błąd walidacji.

**Wynik końcowy:**
Użytkownicy przesyłają między sobą szyfrowane wiadomości. Treść jest niedostępna dla serwera pośredniczącego.

### UC4: Zakończenie sesji komunikacyjnej

**Cel:**
Poprawne zakończenie rozmowy i unieważnienie aktualnej sesji.

**Aktorzy:**
Użytkownik A bądź B (może dowolny z uczestników), Serwer.

**Warunki wstępne:**
- Trwa aktywna sesja,
- co najmniej jeden użytkownik nadal połączony.

**Scenariusz główny:**
1. Użytkownik przesyła komunikat `CLOSE` do serwera,
2. serwer unieważnia sesję (`session_id`) oraz przypisane do niej JWT,
3. serwer powiadamia obu uczestników o zamknięciu sesji,
4. klient rozłącza się (opcjonalnie usuwa lokalnie klucze i dane powiązane z sesją).

**Scenariusze alternatywne / błędy:**
- Próba zakończenia zamkniętej / nieaktywnej sesji → komunikat o błędzie,
- utrata połączenia przed wysłaniem `CLOSE` → sesja może zostać zamknięta automatycznie po czasie (timeout),
- błąd walidacji JWT → brak możliwości zamknięcia sesji.

**Wynik końcowy:**
Sesja zostaje zamknięta, dalsza komunikacja w jej ramach jest niemożliwa. Klienci usuwają lokalne dane dotyczące sesji.

## 4. Mapowanie aplikacji na protokół

| Funkcja aplikacji | Komunikat protokołu | Opis |
| --- | --- | --- |
| Utworzenie nowej sesji | `INIT` | Uzyskanie unikalnego identyfikatora sesji oraz uprawnienia |
| Dołączenie do sesji | `JOIN` | Dwuetapowe, anonimowe zestawienie dialogu |
| Wymiana kluczy szyfrujących | `KEY_EXCHANGE` | Szyfrowanie wiadomości |
| Wysyłanie wiadomości tekstowych | `MSG` | Serwer jest „głuchy" — przetwarza routing i walidację sesji/JWT |
| Odbieranie wiadomości tekstowych | `MSG` | Serwer jest „głuchy" — przetwarza routing i walidację sesji/JWT |
| Obsługa błędów i problemów | `ERROR` | Klient wie, czy musi ponowić próbę |
| Zakończenie sesji | `CLOSE` | Zamknięcie połączenia |

### Sposób, w jaki protokół wspiera przypadki użycia

- Protokół gwarantuje bezpieczny przepływ danych między klientami bez utraty poufności.
- Warstwowe bezpieczeństwo: TLS (transport) + JWT (autoryzacja) + E2EE (treść).

### Ewentualne rozszerzenia protokołu

- Obsługa grup (zamiast 1-na-1),
- potwierdzenia odczytania wiadomości,
- typowanie (wskaźnik aktywnego pisania),
- obsługa plików (poza tekstem).

## 5. Wymagania niefunkcjonalne

### Bezpieczeństwo

- Szyfrowanie end-to-end (E2EE) dla treści wiadomości — serwer nie ma dostępu,
- połączenie musi być zabezpieczone protokołem TLS,
- dostęp do sesji weryfikowany za pomocą tokenów JWT,
- system nie przechowuje trwałych danych użytkownika.

### Wydajność

- Maksymalny rozmiar pojedynczego komunikatu (aby uniknąć przeciążenia),
- WebSocket dla komunikacji dwukierunkowej w czasie rzeczywistym.

### Niezawodność

- TCP — dostarczanie danych w odpowiedniej kolejności i bez strat,
- monitorowanie aktywności klientów przez WebSocket ping/pong,
- timeout i obsługa żartu.

### Skalowalność

- Możliwość szerokiej obsługi użytkowników (stateless server).

### Logowanie / diagnostyka

- Minimalne logowanie (ze względów bezpieczeństwa).

## 6. Plan implementacji i testowania

### Zakres MVP (minimum działające)

- Bezpieczna wymiana wiadomości bez trwałego zapisywania danych.

### Plan testów

#### Testy funkcjonalne

1. Weryfikacja, czy Client A może utworzyć sesję wysyłając `INIT` i otrzymując poprawne `session_id` + token JWT,
2. sprawdzenie, czy Client B poprawnie dołącza po wysłaniu `JOIN` z ważnym `session_id`,
3. weryfikacja poprawnego przebiegu `KEY_EXCHANGE` i przesyłania `MSG` z potwierdzeniem `ACK`,
4. poprawne obsłużenie `CLOSE` i wyrejestrowanie sesji.

#### Testy bezpieczeństwa

1. Przechwycenie ruchu na serwerze — upewnienie się, że `ciphertext` jest nieczytelny bez kluczy klientów,
2. weryfikacja wymuszenia TLS na warstwie transportowej.

#### Testy obsługi błędów

1. Wysłanie niepoprawnego JSON lub brak wymaganych pól — sprawdzenie błędu,
2. wysłanie `MSG` z nieprawidłowym lub wygasłym tokenem JWT — sprawdzenie odrzucenia,
3. obsługa timeout i utraty połączenia.

### Podział pracy

- Osoba 1: implementacja serwera i klientów,
- osoba 2: implementacja zabezpieczeń,
- osoba 3: dokumentacja, testy i integracja.

</details>
