"""Conexión SQLite: uso entre threads (lo que necesita el dashboard)."""
import threading

from grupo3 import db


def test_connect_cross_thread(tmp_path):
    """La conexión con check_same_thread=False se puede usar desde otro thread.

    Reproduce el bug del dashboard: la conexión cacheada con st.cache_resource
    se usa desde un thread de rerun distinto al de creación. Sin el flag,
    sqlite3 lanza ProgrammingError ("created in a thread...").
    """
    conn = db.connect(str(tmp_path / "t.db"), check_same_thread=False)
    db.init_db(conn)

    resultado = {}

    def worker():
        resultado["n"] = conn.execute("SELECT COUNT(*) FROM analisis").fetchone()[0]

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    assert resultado["n"] == 0  # tablas creadas, sin filas, sin error de thread
