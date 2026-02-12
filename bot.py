import gspread
from google.oauth2.service_account import Credentials
import requests
from io import BytesIO
import os
import json
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GOOGLE_JSON = json.loads(os.environ.get("GOOGLE_JSON")) 
CHANNELS = ["@LootDealsDost"]
SHEET_NAME = "DealDost"
WORKSHEET_NAME = "deals"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# ---------------- AUTH ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(GOOGLE_JSON, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open(SHEET_NAME).worksheet(WORKSHEET_NAME)

def post_deal(row, caption):
    try:
        res = requests.get(row['Image'], timeout=15)
        img_file = BytesIO(res.content)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {"chat_id": CHANNELS[0], "caption": caption, "parse_mode": "HTML"}
        files = {"photo": ("deal.jpg", img_file)}
        response = requests.post(url, data=payload, files=files)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Post failed: {e}")
        return False

def main():
    records = sheet.get_all_records()
    logging.info("Scanning for one unposted deal...")

    for i, row in enumerate(records):
        # Column 9 is 'Posted'
        if str(row.get('Posted', '')).upper() != "TRUE":
            
            # Formatting the post
            discount = row.get('Discount', 'Loot')
            caption = (
                f"🔥 <b>{row['Platform']} Deal - {discount} OFF</b> 🔥\n\n"
                f"📦 {row['Product']}\n\n"
                f"❌ MRP: <strike>₹{row['MRP']}</strike>\n"
                f"✅ <b>Price: ₹{row['Price']}</b>\n\n"
                f"🛒 <b>Buy Now:</b> <a href='{row['Link']}'>Click Here</a>\n\n"
                f"⚡ <i>Join @LootDealsDost</i>"
            )

            if post_deal(row, caption):
                # Update Column I (9th column) to TRUE
                sheet.update_cell(i + 2, 9, "TRUE") 
                logging.info(f"Successfully posted: {row['Product'][:30]}")
                
                # --- CRITICAL: STOP AFTER ONE POST ---
                return 
            else:
                logging.error("Failed to post. Will try again in 5 minutes.")
                return

    logging.info("No new deals found to post.")

if __name__ == "__main__":
    main()