import asyncio
import json
import sqlite3
import datetime
from websockets import connect

# --- CONFIGURATION ---
BINANCE_WS_URL = "wss://fstream.binance.com/ws/"
DB_NAME = "market_data.db"
# We track 4 symbols to allow for cross-correlation heatmaps
SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt"]

def init_db():
    """
    Creates the database table if it doesn't exist.
    Schema: symbol (text), price (real), quantity (real), timestamp (datetime)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (symbol TEXT, price REAL, quantity REAL, timestamp DATETIME)''')
    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized successfully.")

def save_trade(symbol, price, quantity, timestamp):
    """Inserts a single trade tick into the SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO trades (symbol, price, quantity, timestamp) VALUES (?, ?, ?, ?)",
                  (symbol, price, quantity, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

async def binance_listener(symbol):
    """
    Connects to Binance WebSocket for a specific symbol.
    Handles real-time stream and network reconnections.
    """
    url = f"{BINANCE_WS_URL}{symbol.lower()}@trade"
    
    # Auto-reconnect loop
    while True:
        try:
            async with connect(url) as websocket:
                print(f"✅ Connected to {symbol}")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Parse only 'trade' events
                    if data.get('e') == 'trade':
                        # Normalizing data [Requirement: Data Handling]
                        # T = trade time (ms), p = price, q = quantity
                        timestamp = datetime.datetime.fromtimestamp(data['T'] / 1000.0)
                        price = float(data['p'])
                        quantity = float(data['q'])
                        
                        save_trade(symbol, price, quantity, timestamp)
                        
        except Exception as e:
            print(f"⚠️ Connection error for {symbol}: {e}. Retrying in 5s...")
            await asyncio.sleep(5) 

async def main():
    """Main entry point for the Asyncio loop."""
    init_db()
    # Create a listening task for every symbol in our list
    tasks = [binance_listener(sym) for sym in SYMBOLS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        print("Starting Ingestion Engine...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ingestion stopped by user.")
        