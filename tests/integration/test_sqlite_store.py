from pathlib import Path

from app.persistence.sqlite_store import SQLiteStore


def test_sqlite_store_creates_session_and_turns(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()

    session_id = store.create_session("student-001", "clarify_problem")
    store.add_turn(session_id, "student", "题目是向量数量积")
    store.add_turn(session_id, "assistant", "先想投影")

    turns = store.list_turns(session_id)

    assert session_id > 0
    assert len(turns) == 2
    assert turns[0]["role"] == "student"
    assert turns[1]["content"] == "先想投影"
