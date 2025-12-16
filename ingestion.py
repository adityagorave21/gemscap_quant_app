"""Real-time data ingestion from Binance Futures WebSocket."""
import json
import threading
import time
from datetime import datetime
import websocket
from storage import TickStorage

class BinanceTickIngestion:
    def __init__(self, symbols, storage):
        self.symbols = [s.lower() for s in symbols]
        self.storage = storage
        self.ws_connections = {}
        self.running = False
        self.threads = []
        self.tick_buffer = []
        self.buffer_lock = threading.Lock()
        self.stats = {symbol: {'count': 0, 'last_price': 0} for symbol in self.symbols}
        self.stats_lock = threading.Lock()
    
    def _on_message(self, ws, message, symbol):
        try:
            data = json.loads(message)
            if data.get('e') == 'trade':
                timestamp = datetime.fromtimestamp(data['T'] / 1000.0).isoformat()
                price = float(data['p'])
                quantity = float(data['q'])
                with self.buffer_lock:
                    self.tick_buffer.append((timestamp, symbol.upper(), price, quantity))
                with self.stats_lock:
                    self.stats[symbol]['count'] += 1
                    self.stats[symbol]['last_price'] = price
        except:
            pass
    
    def _start_symbol_stream(self, symbol):
        url = f"wss://fstream.binance.com/ws/{symbol}@trade"
        ws = websocket.WebSocketApp(url, on_message=lambda ws, msg: self._on_message(ws, msg, symbol))
        self.ws_connections[symbol] = ws
        thread = threading.Thread(target=ws.run_forever, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _flush_buffer(self):
        while self.running:
            time.sleep(1)
            with self.buffer_lock:
                if self.tick_buffer:
                    try:
                        self.storage.insert_ticks_batch(self.tick_buffer.copy())
                        self.tick_buffer.clear()
                    except:
                        pass
    
    def start(self):
        if self.running:
            return
        self.running = True
        for symbol in self.symbols:
            self._start_symbol_stream(symbol)
        thread = threading.Thread(target=self._flush_buffer, daemon=True)
        thread.start()
    
    def stop(self):
        self.running = False
        for ws in self.ws_connections.values():
            try:
                ws.close()
            except:
                pass
    
    def get_stats(self):
        with self.stats_lock:
            return self.stats.copy()
    
    def is_running(self):
        return self.running
