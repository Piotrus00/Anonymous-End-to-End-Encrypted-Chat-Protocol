from common.models import CloseNoticeFrame, ErrorFrame, InitOkFrame, JoinOkFrame


def init_ok(session_id: str, msg_id: str, timestamp: int, token: str) -> InitOkFrame:
    return InitOkFrame(session_id=session_id, msg_id=msg_id, timestamp=timestamp, token=token)


def join_ok(
    session_id: str,
    msg_id: str,
    timestamp: int,
    token: str | None = None,
) -> JoinOkFrame:
    return JoinOkFrame(session_id=session_id, msg_id=msg_id, timestamp=timestamp, token=token)


def close_notice(session_id: str, msg_id: str, timestamp: int) -> CloseNoticeFrame:
    return CloseNoticeFrame(session_id=session_id, msg_id=msg_id, timestamp=timestamp)


def error(code: str, details: str) -> ErrorFrame:
    return ErrorFrame(error_code=code, details=details)
