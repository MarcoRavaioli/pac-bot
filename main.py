import os
import time
import logging
import csv
import datetime
import base64
from typing import List, Dict

import requests
import pandas as pd
import yfinance as yf
import schedule
from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()

T212_API_KEY = os.getenv("T212_API_KEY")
T212_API_URL = os.getenv("T212_API_URL", "https://demo.trading212.com")
MAX_INVESTMENT_PCT = float(os.getenv("MAX_INVESTMENT_PCT", "0.8"))
MIN_INVESTMENT_EUR = float(os.getenv("MIN_INVESTMENT_EUR", "5.0"))
SAFETY_VALVE_CASH_THRESHOLD = float(os.getenv("SAFETY_VALVE_CASH_THRESHOLD", "40.0"))
SAFETY_VALVE_DAYS = int(os.getenv("SAFETY_VALVE_DAYS", "20"))
Z_SCORE_THRESHOLD = float(os.getenv("Z_SCORE_THRESHOLD", "-1.0"))

ASSETS_STR = os.getenv("ASSETS", "EQQQ,VUSA,21XH")
ASSETS = [asset.strip() for asset in ASSETS_STR.split(',')]

DATA_DIR = "data"
TRADES_HISTORY_FILE = os.path.join(DATA_DIR, "trades_history.csv")

# Map Trading 212 instruments to Yahoo Finance tickers for historical data
YF_TICKER_MAP = {
    "EQQQ": "EQQQ.L",   # Invesco EQQQ Nasdaq-100 (LSE)
    "VUSA": "VUSA.L",   # Vanguard S&P 500 (LSE)
    "21XH": "21XH.DE"   # 21Shares Bitcoin ETP (Xetra)
}

def ensure_data_dir():
    """Ensure data directory and CSV file exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TRADES_HISTORY_FILE):
        with open(TRADES_HISTORY_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Ticker", "Price", "Quantity", "Fees", "Total"])

def log_trade(ticker: str, price: float, quantity: float, fees: float, total: float):
    """Log a trade to the CSV history file for tax compliance (Quadro RW)."""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TRADES_HISTORY_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date_str, ticker, price, quantity, fees, total])
    logger.info(f"Logged trade: {quantity} of {ticker} at {price} (Total: {total}, Fees: {fees})")

def get_last_trade_date() -> datetime.datetime:
    """Read the last trade timestamp from the history CSV."""
    if not os.path.exists(TRADES_HISTORY_FILE):
        return None
        
    try:
        df = pd.read_csv(TRADES_HISTORY_FILE)
        if df.empty:
            return None
        last_date_str = df['Date'].iloc[-1]
        return datetime.datetime.strptime(last_date_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error reading trade history: {e}")
        return None

def get_t212_headers() -> Dict:
    headers = {"Content-Type": "application/json"}
    
    api_id = os.getenv("TRADING212_ID")
    api_key = os.getenv("T212_API_KEY")
    
    if api_id and api_key and api_key != "your_api_key_here":
        # Nuovo schema di autenticazione T212 (Basic base64)
        credentials = f"{api_id}:{api_key}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers["Authorization"] = f"Basic {encoded_credentials}"
    else:
        # Fallback al vecchio template se c'è solo una chiave
        headers["Authorization"] = str(api_key)
        
    return headers

def get_free_cash() -> float:
    """Fetch free cash from Trading 212."""
    url = f"{T212_API_URL}/api/v0/equity/account/cash"
    try:
        response = requests.get(url, headers=get_t212_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data.get('free', 0.0))
    except Exception as e:
        logger.error(f"Failed to fetch free cash: {e}")
        return 0.0

def execute_buy_order(ticker: str, amount_eur: float, current_price_eur: float) -> bool:
    """Execute a market buy order using Trading 212 'quantity' target."""
    if not current_price_eur or current_price_eur <= 0:
        logger.error(f"Cannot buy {ticker}: invalid reference price ({current_price_eur})")
        return False
        
    quantity = round(amount_eur / current_price_eur, 5)
    
    url = f"{T212_API_URL}/api/v0/equity/orders/market"
    payload = {
        "ticker": ticker,
        "quantity": quantity
    }
    
    try:
        response = requests.post(url, headers=get_t212_headers(), json=payload, timeout=10)
        
        # 200 OK means placed.
        if response.status_code == 200:
            logger.info(f"Successfully placed order for {ticker}: {quantity} shares (~{amount_eur} EUR)")
            log_trade(ticker, current_price_eur, quantity, 0.0, round(amount_eur, 2)) 
            return True
        else:
            logger.error(f"Order failed for {ticker}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception during order execution for {ticker}: {e}")
        return False

def calculate_z_score(ticker: str, days: int = 20) -> tuple:
    """Fetch last ~30 days, calculate Z-Score for the last 20 days. Returns (z_score, price_eur)."""
    yf_ticker = YF_TICKER_MAP.get(ticker, ticker)
    try:
        ticker_data = yf.Ticker(yf_ticker)
        hist = ticker_data.history(period="1mo")
        if hist.empty or len(hist) < days:
            logger.warning(f"Not enough data to calculate Z-Score for {ticker}")
            return None, None
            
        closes = hist['Close'].tail(days)
        mean = closes.mean()
        std = closes.std()
        
        current_price = closes.iloc[-1]
        z_score = 0.0 if std == 0 else (current_price - mean) / std
        
        # Convert to EUR
        currency = ticker_data.fast_info.get('currency', 'USD')
        price_eur = current_price
        
        if currency == 'GBp':
            fx = yf.Ticker('GBPEUR=X').history(period='1d')
            fx_val = fx['Close'].iloc[-1] if not fx.empty else 1.17
            price_eur = (current_price / 100.0) * fx_val
        elif currency == 'GBP':
            fx = yf.Ticker('GBPEUR=X').history(period='1d')
            fx_val = fx['Close'].iloc[-1] if not fx.empty else 1.17
            price_eur = current_price * fx_val
        elif currency == 'USD':
            fx = yf.Ticker('USDEUR=X').history(period='1d')
            fx_val = fx['Close'].iloc[-1] if not fx.empty else 0.92
            price_eur = current_price * fx_val
            
        return z_score, price_eur
    except Exception as e:
        logger.error(f"Failed to calculate Z-Score for {ticker}: {e}")
        return None, None

def is_market_open() -> bool:
    """Basic check to avoid placing orders on weekends."""
    now = datetime.datetime.now()
    if now.weekday() >= 5: # Saturday (5) or Sunday (6)
        return False
    return True

def run_trading_logic():
    """Main execution orchestrator."""
    logger.info("Starting trading logic evaluation...")
    if not T212_API_KEY or T212_API_KEY == "your_api_key_here":
        logger.error("API Key not set correctly. Evaluation aborted.")
        return

    if not is_market_open():
        logger.info("Market is closed (weekend). Skipping evaluation.")
        return

    ensure_data_dir()
    
    free_cash = get_free_cash()
    logger.info(f"Current free cash: {free_cash} EUR")
    
    if free_cash < MIN_INVESTMENT_EUR:
        logger.info(f"Insufficient funds ({free_cash} < {MIN_INVESTMENT_EUR}).")
        return

    max_affordable = free_cash * MAX_INVESTMENT_PCT
    investment_amount = min(max_affordable, free_cash)
    if investment_amount < MIN_INVESTMENT_EUR:
        investment_amount = free_cash # Use all if available > 5
        if investment_amount < MIN_INVESTMENT_EUR:
            return

    # Calculate Z-Scores
    z_scores = {}
    prices = {}
    for asset in ASSETS:
        z, p_eur = calculate_z_score(asset, days=20)
        if z is not None:
            z_scores[asset] = z
            prices[asset] = p_eur
            logger.info(f"Z-Score for {asset}: {z:.2f} (Price: {p_eur:.2f} EUR)")

    if not z_scores:
        logger.warning("Could not calculate any Z-scores.")
        return

    # Check Safety Valve
    last_trade = get_last_trade_date()
    days_since_last_trade = SAFETY_VALVE_DAYS + 1 
    if last_trade:
        delta = datetime.datetime.now() - last_trade
        days_since_last_trade = delta.days

    safety_valve_triggered = False
    if days_since_last_trade >= SAFETY_VALVE_DAYS and free_cash > SAFETY_VALVE_CASH_THRESHOLD:
        logger.info(f"Safety valve triggered: No trades in {days_since_last_trade} days and cash {free_cash} > {SAFETY_VALVE_CASH_THRESHOLD}")
        safety_valve_triggered = True

    # Decide what to buy
    assets_to_buy = []
    
    # 1. Normal Z-Score Strategy
    for asset, z in z_scores.items():
        if z < Z_SCORE_THRESHOLD:
            assets_to_buy.append((asset, z))
            
    # 2. Safety Valve Execution
    if safety_valve_triggered and not assets_to_buy:
        lowest_asset = min(z_scores, key=z_scores.get)
        logger.info(f"Safety valve forcing buy on {lowest_asset} (Z: {z_scores[lowest_asset]:.2f})")
        assets_to_buy.append((lowest_asset, z_scores[lowest_asset]))

    if not assets_to_buy:
        logger.info("No assets met the buying criteria.")
        return

    # Execute buys
    amount_per_asset = investment_amount / len(assets_to_buy)
    for asset, z in assets_to_buy:
        if amount_per_asset >= MIN_INVESTMENT_EUR:
            logger.info(f"Attempting to buy {amount_per_asset:.2f} EUR of {asset}")
            execute_buy_order(asset, amount_per_asset, prices[asset])
        else:
            logger.info(f"Calculated amount for {asset} ({amount_per_asset}) is below minimum ({MIN_INVESTMENT_EUR}).")

def main():
    logger.info("Trading 212 Automated Bot Started.")
    ensure_data_dir()
    
    # Initial run
    run_trading_logic()

    # Schedule: every 6 hours
    schedule.every(6).hours.do(run_trading_logic)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
