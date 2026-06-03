import time
import uuid
from typing import Tuple

from common.models import CiphertextPayload, MsgFrame


def build_msg_frame(session_id: str, ciphertext: str) -> Tuple[str, MsgFrame]:
    """Zwraca (msg_id, ramka) z zaszyfrowanym ciphertext w payload."""
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    frame = MsgFrame(
        session_id=session_id,
        msg_id=msg_id,
        timestamp=int(time.time()),
        payload=CiphertextPayload(ciphertext=ciphertext),
    )
    return msg_id, frame
