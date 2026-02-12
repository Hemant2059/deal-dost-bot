import gspread
from google.oauth2.service_account import Credentials
import requests
from io import BytesIO
import logging
import os
import json
import time

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GOOGLE_JSON = json.loads(os.environ.get("GOOGLE_JSON")) 

CHANNELS = ["@LootDealsDost"]
SHEET_NAME = "LootDeals"
WORKSHEET_NAME = "deals"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# ---------------- AUTH ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(GOOGLE_JSON, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open(SHEET_NAME).worksheet(WORKSHEET_NAME)

def get_discount(row):
    # Use existing discount if present, else calculate
    existing = str(row.get('Discount', '')).replace('%', '').strip()
    if existing and existing != "0":
        return f"{existing}%"
    
    try:
        mrp = float(str(row['MRP']).replace(',', ''))
        price = float(str(row['Price']).replace(',', ''))
        calc = round(((mrp - price) / mrp) * 100)
        return f"{calc}%"
    except:
        return "Special Price"

def post_deal(row, caption):
    try:
        # Download image from URL provided in sheet
        res = requests.get(row['Image'], timeout=15)
        img_file = BytesIO(res.content)
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {"chat_id": CHANNELS[0], "caption": caption, "parse_mode": "HTML"}
        files = {"photo": ("deal.jpg", img_file)}
        
        response = requests.post(url, data=payload, files=files)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to post image: {e}")
        return False

def main():
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        # Only process rows where 'Posted' is not TRUE
        if str(row.get('Posted', '')).upper() != "TRUE":
            discount_val = get_discount(row)
            
            # Format Badge
            badge = "🚨 <b>LIMITED TIME DEAL</b> 🚨\n" if str(row.get('isLimited')).upper() == "TRUE" else ""
            coupon = f"\n🎟️ <b>Extra:</b> {row['Coupon']}" if row.get('Coupon') else ""
            
            caption = (
                f"{badge}"
                f"🔥 <b>{row['Platform']} LOOT - {discount_val} OFF</b> 🔥\n\n"
                f"📦 {row['Product']}\n\n"
                f"❌ MRP: <strike>₹{row['MRP']}</strike>\n"
                f"✅ <b>Price: ₹{row['Price']}</b>{coupon}\n\n"
                f"🛒 <b>Buy Now:</b> <a href='{row['Link']}'>Click Here to Shop</a>\n\n"
                f"⚡ <i>Join @LootDealsDost for more!</i>"
            )

            if post_deal(row, caption):
                # Column I (Posted) is the 9th column
                sheet.update_cell(i + 2, 9, "TRUE") 
                logging.info(f"Successfully posted: {row['Product'][:30]}")
                time.sleep(5) # Delay to avoid Telegram flood limits

if __name__ == "__main__":
    main()