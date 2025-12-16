"""Storage module for SQLite database operations."""
import sqlite3
import pandas as pd
import threading

class TickStorage:
    def __init__(self, db_path="ticks.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                ON ticks(symbol, timestamp)
            """)
            conn.commit()
            conn.close()
    
    def insert_ticks_batch(self, ticks):
        if not ticks:
            return
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO ticks (timestamp, symbol, price, quantity) VALUES (?, ?, ?, ?)",
                ticks
            )
            conn.commit()
            conn.close()
    
    def get_ticks(self, symbol=None, limit=None, start_time=None, end_time=None):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT timestamp, symbol, price, quantity FROM ticks WHERE 1=1"
            params = []
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            query += " ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            return df
    
    def get_latest_ticks(self, symbol, n=1000):
        return self.get_ticks(symbol=symbol, limit=n)
    
    def get_tick_count(self, symbol=None):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if symbol:
                cursor.execute("SELECT COUNT(*) FROM ticks WHERE symbol = ?", (symbol,))
            else:
                cursor.execute("SELECT COUNT(*) FROM ticks")
            count = cursor.fetchone()[0]
            conn.close()
            return count
    
    def get_symbols(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM ticks")
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            return symbols
