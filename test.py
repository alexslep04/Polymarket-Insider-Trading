import csv
import requests
import time
import os

INPUT_CSV = 'trades_export.csv'
OUTPUT_CSV = 'enriched_users_roi.csv'

def get_unique_wallets_and_market(filename):
    """Reads the exported trades CSV and extracts all unique wallets and the market condition ID."""
    wallets = set()
    condition_ids = set()
    
    if not os.path.exists(filename):
        print(f"Error: Could not find {filename}. Make sure it is in the same folder.")
        return [], None

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('proxy_wallet'):
                wallets.add(row['proxy_wallet'])
            if row.get('condition_id'):
                condition_ids.add(row['condition_id'])
                
    # Convert sets to lists. Use the first condition_id found as our target market.
    return list(wallets), list(condition_ids)[0] if condition_ids else None

def process_users():
    wallets, target_condition_id = get_unique_wallets_and_market(INPUT_CSV)
    
    if not wallets:
        return

    # Load already processed wallets to allow for resuming if the script stops
    processed_wallets = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('proxy_wallet'):
                    processed_wallets.add(row['proxy_wallet'])

    wallets_to_process = [w for w in wallets if w not in processed_wallets]
    
    if not wallets_to_process:
        print("All users in the CSV have already been enriched! Check 'enriched_users_roi.csv'.")
        return

    print(f"Found {len(wallets)} total unique wallets in {INPUT_CSV}.")
    print(f"Resuming progress: {len(wallets_to_process)} wallets left to enrich...")

    # Open output file in append mode so we save after every single user
    write_headers = not os.path.exists(OUTPUT_CSV)
    
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['proxy_wallet', 'first_seen', 'realized_pnl', 'total_bought', 'roi_percentage']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if write_headers:
            writer.writeheader()

        for i, wallet in enumerate(wallets_to_process):
            first_seen = "Unknown"
            realized_pnl = 0.0
            total_bought = 0.0

            # 1. Fetch first_seen (Wallet Age) from Gamma API
            try:
                prof_resp = requests.get("https://gamma-api.polymarket.com/public-profile", params={"address": wallet})
                if prof_resp.status_code == 200:
                    first_seen = prof_resp.json().get("createdAt", "Unknown")
            except Exception:
                pass

            # 2. Fetch PnL and total bought from Data API
            try:
                params = {"user": wallet}
                if target_condition_id:
                    params["market"] = target_condition_id
                    
                pos_resp = requests.get("https://data-api.polymarket.com/closed-positions", params=params)
                
                if pos_resp.status_code == 200:
                    positions = pos_resp.json()
                    for pos in positions:
                        realized_pnl += float(pos.get("realizedPnl", 0))
                        total_bought += float(pos.get("totalBought", 0))
            except Exception:
                pass

            # 3. Calculate ROI Percentage
            roi_percentage = 0.0
            if total_bought > 0:
                roi_percentage = (realized_pnl / total_bought) * 100

            # Write the row to the CSV
            writer.writerow({
                'proxy_wallet': wallet,
                'first_seen': first_seen,
                'realized_pnl': round(realized_pnl, 2),
                'total_bought': round(total_bought, 2),
                'roi_percentage': round(roi_percentage, 2)
            })
            
            f.flush() # Force save to disk immediately so you never lose data

            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1} / {len(wallets_to_process)} users...")

            time.sleep(0.3) # API Rate Limit Protection

    print(f"\nSuccess! All user data has been saved to '{OUTPUT_CSV}'.")

if __name__ == "__main__":
    process_users()