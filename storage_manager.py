import json, os, sqlite3, time

class StorageManager:
    def __init__(self, json_path="output/crawled.json", sqlite_path=None):
        self.json_path = json_path
        dir_name = os.path.dirname(json_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        self.buffer = []
        self.sqlite_path = sqlite_path
        if sqlite_path:
            self._init_sqlite(sqlite_path)

    def _init_sqlite(self, path):
        self.conn = sqlite3.connect(path)
        cur = self.conn.cursor()
        cur.execute("""
             CREATE TABLE IF NOT EXISTS pages(
             id INTEGER PRIMARY KEY,
             url TEXT UNIQUE,
             title TEXT,
             meta_description TEXT,
             text BLOB,
             emails TEXT,
             relevance_score REAL,
             summary TEXT,
             entities TEXT,
             timestamp REAL
             );
             """)
        self.conn.commit()

    def add_record(self, record):
        record['fetched_at'] = time.time()
        self.buffer.append(record)
        # immediate append to sqlite if enabled
        if self.sqlite_path:
            cur = self.conn.cursor()
            try:
                cur.execute(
    "INSERT OR IGNORE INTO pages(url,title,meta_description,text,emails,relevance_score,summary,entities,timestamp) VALUES(?,?,?,?,?,?,?, ?,?)",
    (record.get("url"), record.get("title"), record.get("meta_description"),
     record.get("text"), ",".join(record.get("emails",[])), record.get("relevance_score"),
     record.get("summary"), str(record.get("entities")), record['fetched_at'])
)

                self.conn.commit()
            except Exception as e:
                print(f"[Storage] SQLite insert error: {e}")

    def save(self):
        # append to JSON file
        if self.buffer:
            existing = []
            if os.path.exists(self.json_path):
                try:
                    with open(self.json_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []
            existing.extend(self.buffer)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            self.buffer = []

    def close(self):
        # Flush any remaining buffered data before closing
        if self.buffer:
            self.save()
        if self.sqlite_path:
            self.conn.close()
