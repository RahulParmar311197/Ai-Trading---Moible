from sqlalchemy import create_engine

from app.database.session import SQLAlchemyExecutor, create_database_engine


def test_database_engine_does_not_connect_during_creation() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"
    engine.dispose()


def test_sqlalchemy_executor_reads_and_writes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")

    executor = SQLAlchemyExecutor(engine)
    executor.execute("INSERT INTO items (id, name) VALUES (:id, :name)", {"id": 1, "name": "NIFTY"})
    row = executor.fetch_one("SELECT * FROM items WHERE id = :id", {"id": 1})
    assert row == {"id": 1, "name": "NIFTY"}
    assert executor.fetch_all("SELECT * FROM items", {}) == [row]
    engine.dispose()
