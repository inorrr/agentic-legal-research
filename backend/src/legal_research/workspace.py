"""Local workspace persistence. External credentials never enter these records."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_SETTINGS = {"theme": "light", "font_size": "normal", "density": "comfortable", "preferred_summary": "concise"}

class Workspace:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version > 1:
                raise RuntimeError('Workspace schema is newer than this application')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS matters(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS rounds(id TEXT PRIMARY KEY, matter_id TEXT NOT NULL REFERENCES matters(id) ON DELETE CASCADE, number INTEGER NOT NULL, body TEXT NOT NULL, UNIQUE(matter_id,number));
                CREATE TABLE IF NOT EXISTS feedback(matter_id TEXT NOT NULL REFERENCES matters(id) ON DELETE CASCADE, case_id TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(matter_id,case_id));
                CREATE TABLE IF NOT EXISTS selections(matter_id TEXT NOT NULL REFERENCES matters(id) ON DELETE CASCADE, case_id TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(matter_id,case_id));
                CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
                PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                db.execute('PRAGMA foreign_keys=ON')
                yield db
        finally:
            db.close()

    def matters(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT body FROM matters ORDER BY rowid DESC')]

    def create(self, matter):
        with self.connect() as db:
            db.execute('INSERT INTO matters VALUES (?,?)', (matter['id'], json.dumps(matter)))
        return matter

    def detail(self, matter_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM matters WHERE id=?', (matter_id,)).fetchone()
            if row is None: return None
            rounds = [json.loads(r[0]) for r in db.execute('SELECT body FROM rounds WHERE matter_id=? ORDER BY number', (matter_id,))]
            feedback = {r[0]: json.loads(r[1]) for r in db.execute('SELECT case_id,body FROM feedback WHERE matter_id=?', (matter_id,))}
            selections = [json.loads(r[0]) for r in db.execute('SELECT body FROM selections WHERE matter_id=? ORDER BY rowid', (matter_id,))]
            return dict(matter=json.loads(row[0]), rounds=rounds, feedback=feedback, selections=selections)

    def round(self, matter_id, body):
        with self.connect() as db:
            db.execute('INSERT INTO rounds VALUES (?,?,?,?)', (body['id'], matter_id, body['number'], json.dumps(body)))
        return body

    def set_case_state(self, table, matter_id, case_id, body):
        if table not in {'feedback', 'selections'}: raise ValueError('Unknown state')
        with self.connect() as db:
            if body is None:
                db.execute(f'DELETE FROM {table} WHERE matter_id=? AND case_id=?', (matter_id,case_id))
            else:
                db.execute(f'INSERT INTO {table} VALUES (?,?,?) ON CONFLICT(matter_id,case_id) DO UPDATE SET body=excluded.body', (matter_id,case_id,json.dumps(body)))

    def delete(self, matter_id):
        with self.connect() as db: db.execute('DELETE FROM matters WHERE id=?', (matter_id,))

    def settings(self, body=None):
        with self.connect() as db:
            if body is not None:
                db.execute('INSERT INTO settings VALUES (1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body', (json.dumps(body),))
            row = db.execute('SELECT body FROM settings WHERE id=1').fetchone()
            return DEFAULT_SETTINGS.copy() if row is None else json.loads(row[0])
