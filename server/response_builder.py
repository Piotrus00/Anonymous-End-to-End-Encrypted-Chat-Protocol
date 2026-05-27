from typing import Any, Dict


def init_ok(session_id: str, msg_id: Any, timestamp: Any) -> Dict[str, Any]:
    return {
        "type": "INIT_OK",
        "session_id": session_id,
        "msg_id": msg_id,
        "timestamp": timestamp,
        "payload": {"status": "OK"},
    }


def join_ok(session_id: str, msg_id: Any, timestamp: Any) -> Dict[str, Any]:
    return {
        "type": "JOIN_OK",
        "session_id": session_id,
        "msg_id": msg_id,
        "timestamp": timestamp,
        "payload": {"status": "OK"},
    }


def close_notice(session_id: str, msg_id: Any, timestamp: Any) -> Dict[str, Any]:
    return {
        "type": "CLOSE",
        "session_id": session_id,
        "msg_id": msg_id,
        "timestamp": timestamp,
        "payload": {"status": "SESSION_CLOSED"},
    }


def ping(msg_id: Any, timestamp: Any) -> Dict[str, Any]:
    return {
        "type": "PING",
        "msg_id": msg_id,
        "timestamp": timestamp,
    }


def error(code: str, details: str) -> Dict[str, str]:
    return {
        "type": "ERROR",
        "error_code": code,
        "details": details,
    }
