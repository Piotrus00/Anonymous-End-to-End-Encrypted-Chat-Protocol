import asyncio
import time

from common.models import JoinFrame


async def send_join(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    session_id: str,
    encode_message,
    decode_message,
) -> bool:
    join_message = JoinFrame(session_id=session_id, msg_id="msg_002", timestamp=int(time.time()))

    print(f"\n-> Wysylam JOIN dla sesji {session_id}...")
    writer.write(encode_message(join_message))
    await writer.drain()

    try:
        data = await reader.readuntil(b'\n')
    except asyncio.LimitOverrunError as e:
        print("X Odpowiedz serwera przekroczyla dozwolony rozmiar")
        try:
            await reader.readexactly(e.consumed)
        except asyncio.IncompleteReadError:
            pass
        return False
    except asyncio.IncompleteReadError:
        print("X Serwer zamknal polaczenie")
        return False

    if not data:
        print("X Serwer zamknal polaczenie")
        return False

    success, response = decode_message(data)
    if not success:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False

    if response is None:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False

    if response.type == "ERROR":
        print(f"X Blad serwera: {response.details}")
        return False

    if response.type != "JOIN_OK":
        print(f"X Blad: Oczekiwano JOIN_OK, otrzymano {response.type}")
        return False

    print(f"OK Dolaczono do sesji: {session_id}")
    return True
