from common.models import CloseNoticeFrame, ErrorFrame, InitOkFrame, JoinOkFrame, PingFrame


def init_ok(session_id: str, msg_id: str, timestamp: int) -> InitOkFrame:
    return InitOkFrame(session_id=session_id, msg_id=msg_id, timestamp=timestamp)


def join_ok(session_id: str, msg_id: str, timestamp: int) -> JoinOkFrame:
    return JoinOkFrame(session_id=session_id, msg_id=msg_id, timestamp=timestamp)


def close_notice(session_id: str, msg_id: str, timestamp: int) -> CloseNoticeFrame:
    return CloseNoticeFrame(session_id=session_id, msg_id=msg_id, timestamp=timestamp)


def ping(msg_id: str, timestamp: int) -> PingFrame:
    return PingFrame(msg_id=msg_id, timestamp=timestamp)


def error(code: str, details: str) -> ErrorFrame:
    return ErrorFrame(error_code=code, details=details)
