# Anonymous-End-to-End-Encrypted-Chat-Protocol

Temat projektu:
A2CP – Anonymous End-to-End Encrypted Chat Protocol

Opis ogólny:
Celem projektu jest zaprojektowanie i implementacja autorskiego protokołu komunikacyjnego umożliwiającego anonimową komunikację pomiędzy dwoma użytkownikami za pośrednictwem serwera pośredniczącego (relay). Protokół zapewnia poufność, integralność oraz podstawową anonimowość na poziomie aplikacyjnym.

Główne założenia:

komunikacja w modelu klient–serwer (serwer jako broker wiadomości),
brak tożsamości użytkowników – komunikacja odbywa się w ramach anonimowych sesji,
autoryzacja oparta o tokeny sesyjne (JWT bez danych użytkownika),
szyfrowanie end-to-end – serwer nie ma dostępu do treści wiadomości,
własny format komunikatów i logika protokołu (typy wiadomości, stany, błędy).

Jak to działa (wysoki poziom):

Jeden użytkownik tworzy sesję komunikacyjną (session_id).
Drugi użytkownik dołącza do sesji.
Serwer przydziela obu stronom tokeny JWT identyfikujące ich udział w sesji.
Klienci wymieniają klucze szyfrowania (przez serwer) i ustanawiają szyfrowanie end-to-end.
Wiadomości są szyfrowane po stronie klienta i przekazywane przez serwer bez możliwości ich odczytu.
Serwer odpowiada jedynie za routowanie wiadomości i walidację tokenów.

Kluczowe elementy protokołu:

typy wiadomości: INIT, JOIN, KEY_EXCHANGE, MSG, ERROR, CLOSE
model stanów: połączenie → dołączenie do sesji → wymiana kluczy → komunikacja → zakończenie
obsługa błędów: niepoprawny token, wygasła sesja, utrata połączenia, brak drugiego uczestnika
mechanizmy bezpieczeństwa:
JWT (autoryzacja sesji),
podpisy tokenów (np. RSA lub HMAC),
szyfrowanie end-to-end (np. AES z kluczem uzgodnionym między klientami)

Dlaczego ten projekt:

prosty i intuicyjny model działania (łatwy do wytłumaczenia),
spełnia wszystkie wymagania (protokół, bezpieczeństwo, obsługa błędów),
zawiera nowoczesne podejścia (JWT, E2E encryption),
dobrze nadaje się do demonstracji i testowania (np. dwaj klienci + serwer).

Podział pracy (propozycja):

osoba 1: implementacja serwera (zarządzanie sesjami, routing, walidacja tokenów),
osoba 2: implementacja klienta (komunikacja, szyfrowanie, obsługa sesji),
osoba 3: dokumentacja + testy + spójność całości (oraz scenariusze błędów).