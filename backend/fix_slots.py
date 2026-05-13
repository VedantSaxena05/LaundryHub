from sqlalchemy import create_engine, text
from collections import defaultdict

DB_PATH = "test.db"

e = create_engine(f"sqlite:///{DB_PATH}")
with e.connect() as c:
    r = c.execute(text("DELETE FROM slots WHERE status = 'used'"))
    print(f"Deleted {r.rowcount} used slot(s)")

    rows = c.execute(text(
        "SELECT id, student_id, date FROM slots "
        "WHERE status != 'cancelled' "
        "ORDER BY student_id, date"
    )).fetchall()

    idx = defaultdict(int)
    for slot_id, student_id, date in rows:
        idx[student_id] += 1
        c.execute(
            text("UPDATE slots SET month_index = :i WHERE id = :id"),
            {"i": idx[student_id], "id": slot_id}
        )

    c.commit()
    print("month_index re-sequenced")
