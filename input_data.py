import sqlite3
import requests
import json
import time
import csv
import os

DB_NAME = "polymarket_anomaly_data.db"

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS markets (
        market_id TEXT PRIMARY KEY, condition_id TEXT, slug TEXT, question TEXT,
        token_id_yes TEXT, token_id_no TEXT, volume REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        trade_id TEXT PRIMARY KEY, condition_id TEXT, proxy_wallet TEXT, side TEXT,
        token_id TEXT, price REAL, size REAL, timestamp DATETIME,
        FOREIGN KEY(condition_id) REFERENCES markets(condition_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        proxy_wallet TEXT PRIMARY KEY, first_seen DATETIME, realized_pnl REAL
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def insert_market_data(market_json):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    token_ids = json.loads(market_json.get("clobTokenIds", "[]"))
    token_id_yes = token_ids[0] if len(token_ids) > 0 else None
    token_id_no = token_ids[1] if len(token_ids) > 1 else None

    cursor.execute('''
    INSERT OR REPLACE INTO markets (market_id, condition_id, slug, question, token_id_yes, token_id_no, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        market_json["id"], market_json["conditionId"], market_json["slug"],
        market_json["question"], token_id_yes, token_id_no, float(market_json["volume"])
    ))

    conn.commit()
    conn.close()

def fetch_recent_trades(condition_id):
    """
    Fetches public historical trades using the Data API.
    Polymarket's public API limits pagination to the most recent ~3,000 trades.
    This safely collects that entire climax window for anomaly detection.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor_db = conn.cursor()
    
    base_url = "https://data-api.polymarket.com/trades"
    limit = 100
    offset = 0

    print(f"Fetching public historical trades from Data API (Max ~3000 trades)...")

    while True:
        params = {"market": condition_id, "limit": limit, "offset": offset}
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            trades = response.json()
            
            if not trades:
                print("No more trades returned by API.")
                break 

            cursor_db.execute("SELECT COUNT(*) FROM trades")
            count_before = cursor_db.fetchone()[0]

            for trade in trades:
                trade_hash = trade.get("transactionHash", "")
                trade_time = str(trade.get("timestamp", ""))
                trade_id = f"{trade_hash}_{trade_time}"
                
                cursor_db.execute('''
                INSERT OR IGNORE INTO trades (trade_id, condition_id, proxy_wallet, side, token_id, price, size, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_id, 
                    condition_id, 
                    trade.get("proxyWallet"),
                    trade.get("side"), 
                    trade.get("asset"), 
                    float(trade.get("price", 0)),
                    float(trade.get("size", 0)), 
                    trade.get("timestamp")
                ))

            conn.commit()
            
            cursor_db.execute("SELECT COUNT(*) FROM trades")
            count_after = cursor_db.fetchone()[0]
            
            if count_after == count_before:
                print("\nHit Polymarket's pagination wall. Collected the maximum recent trades allowed.")
                break

            print(f"Unique Trades in DB: {count_after}")
            
            offset += limit
            time.sleep(0.5) 
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                print("\nReached Polymarket's hard offset limit (3,000).")
                break
            elif response.status_code == 429:
                print("Rate limit hit! Waiting 5 seconds before retrying...")
                time.sleep(5)
                continue
            else:
                print(f"HTTP Error: {e}")
                break
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            break

    conn.close()
    print(f"\nCompleted Data API collection!")

def export_to_csv():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("Exporting data to CSV for VS Code viewing...")
    cursor.execute("SELECT * FROM trades ORDER BY timestamp ASC")
    
    with open("trades_export.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([description[0] for description in cursor.description]) 
        writer.writerows(cursor.fetchall())
        
    print("Data exported successfully to 'trades_export.csv'!")
    conn.close()

if __name__ == "__main__":
    market_payload = {
        "id": "645986",
        "question": "U.S. anti-cartel strike/operation on foreign soil by December 31?",
        "conditionId": "0x2c3dce8515854f167dc523745a6b9d98d22ec9266d9f4921f62fd3e4bf1cfa1b",
        "slug": "us-anti-cartel-operation-on-foreign-soil-by-december-31",
        "clobTokenIds": "[\"86498068750018438192524977941980476748299785729870940867089250086714498791178\", \"110290742709531333936637417418570910881285907663357514844586483587588568832794\"]",
        "volume": "6161817.701307",
    }

    setup_database()
    insert_market_data(market_payload)
    
    # Run the correct Data API fetcher
    fetch_recent_trades(market_payload["conditionId"])
    
    export_to_csv()