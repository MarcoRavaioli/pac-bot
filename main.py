import os
import time
import logging
import csv
import datetime
import base64
from typing import List, Dict, Optional, Tuple
import pytz

import requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import schedule
from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Map Trading 212 instruments to Yahoo Finance tickers for historical data
YF_TICKER_MAP = {
    "EQQQ": "EQQQ.L",   # Invesco EQQQ Nasdaq-100 (LSE)
    "VUSA": "VUSA.L",   # Vanguard S&P 500 (LSE)
    "21XH": "21XH.DE"   # 21Shares Bitcoin ETP (Xetra)
}

class Trading212Broker:
    def __init__(self, api_key: str, api_url: str, api_id: str = None):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.api_id = api_id
        self.exact_ticker_map = {}
        
    def get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_id and self.api_key and self.api_key != "your_api_key_here":
            credentials = f"{self.api_id}:{self.api_key}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            headers["Authorization"] = f"Basic {encoded}"
        else:
            headers["Authorization"] = str(self.api_key)
        return headers

    def get_free_cash(self) -> float:
        url = f"{self.api_url}/api/v0/equity/account/cash"
        try:
            resp = requests.get(url, headers=self.get_headers(), timeout=10)
            resp.raise_for_status()
            return float(resp.json().get('free', 0.0))
        except Exception as e:
            logger.error(f"Failed to fetch free cash: {e}")
            return 0.0
            
    def resolve_tickers(self, assets: List[str]):
        if self.exact_ticker_map:
            return
            
        url = f"{self.api_url}/api/v0/equity/metadata/instruments"
        try:
            resp = requests.get(url, headers=self.get_headers(), timeout=10)
            if resp.status_code == 200:
                instruments = resp.json()
                for asset in assets:
                    matches = [i for i in instruments if i.get("shortName") == asset]
                    if not matches:
                        matches = [i for i in instruments if asset in i.get("ticker", "")]
                    
                    if matches:
                        eur_matches = [m for m in matches if m.get("currencyCode") == "EUR"]
                        best_match = eur_matches[0] if eur_matches else matches[0]
                        self.exact_ticker_map[asset] = best_match["ticker"]
                        logger.info(f"Resolved asset {asset} to Trading 212 Ticker: {best_match['ticker']}")
                    else:
                        logger.error(f"Could not find exact T212 instrument for {asset}")
            else:
                logger.error(f"Failed to fetch instruments: {resp.status_code}")
        except Exception as e:
            logger.error(f"Exception resolving T212 tickers: {e}")
            
    def get_portfolio(self) -> Dict[str, dict]:
        """Fetch open positions."""
        url = f"{self.api_url}/api/v0/equity/portfolio"
        portfolio = {}
        try:
            resp = requests.get(url, headers=self.get_headers(), timeout=10)
            if resp.status_code == 200:
                positions = resp.json()
                for pos in positions:
                    ticker = pos.get("ticker")
                    # Reverse lookup to assign short name
                    short_name = next((k for k, v in self.exact_ticker_map.items() if v == ticker), ticker)
                    portfolio[short_name] = {
                        "quantity": float(pos.get("quantity", 0)),
                        "averagePrice": float(pos.get("averagePrice", 0)),
                        "currentPrice": float(pos.get("currentPrice", 0)),
                        "ppl": float(pos.get("ppl", 0)), # Profit/Loss
                        "fxPpl": float(pos.get("fxPpl", 0))
                    }
            return portfolio
        except Exception as e:
            logger.error(f"Exception fetching portfolio: {e}")
            return portfolio

    def execute_market_order(self, ticker: str, quantity: float, attempt_precision: int = 5) -> bool:
        exact_ticker = self.exact_ticker_map.get(ticker, ticker)
        q = round(quantity, attempt_precision) if attempt_precision > 0 else int(quantity)
        
        url = f"{self.api_url}/api/v0/equity/orders/market"
        payload = {"ticker": exact_ticker, "quantity": q}
        
        try:
            resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info(f"Order executed: {q} of {ticker}")
                return True
            elif resp.status_code == 400 and "quantity-precision-mismatch" in resp.text:
                if attempt_precision > 0:
                    logger.warning(f"Precision {attempt_precision} rejected for {ticker}. Retrying {attempt_precision - 1}...")
                    return self.execute_market_order(ticker, quantity, attempt_precision - 1)
                else:
                    return False
            else:
                logger.error(f"Order failed {ticker}: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Exception executing order for {ticker}: {e}")
            return False

class EAStrategy:
    def __init__(self, z_score_threshold: float, history_days: int = 40):
        self.z_score_threshold = z_score_threshold
        self.history_days = history_days
        
    def convert_to_eur(self, current_price: float, currency: str) -> float:
        try:
            if currency == 'GBp':
                fx = yf.Ticker('GBPEUR=X').history(period='1d')
                fx_val = fx['Close'].iloc[-1] if not fx.empty else 1.17
                return (current_price / 100.0) * fx_val
            elif currency == 'GBP':
                fx = yf.Ticker('GBPEUR=X').history(period='1d')
                fx_val = fx['Close'].iloc[-1] if not fx.empty else 1.17
                return current_price * fx_val
            elif currency == 'USD':
                fx = yf.Ticker('USDEUR=X').history(period='1d')
                fx_val = fx['Close'].iloc[-1] if not fx.empty else 0.92
                return current_price * fx_val
            return current_price
        except:
            return current_price

    def analyze_asset(self, ticker: str) -> Tuple[Optional[float], Optional[float], Dict[str, float]]:
        """Returns Conviction Score (0.0 to 1.0), Current Price EUR, and indicator dictionary."""
        yf_ticker = YF_TICKER_MAP.get(ticker, ticker)
        try:
            ticker_data = yf.Ticker(yf_ticker)
            hist = ticker_data.history(period="3mo") # Need enough data for 20-day MA and RSI
            if hist.empty or len(hist) < 30:
                return None, None, {}
                
            closes = hist['Close']
            
            # 1. Z-Score (20 days)
            recent_20 = closes.tail(20)
            mean_20 = recent_20.mean()
            std_20 = recent_20.std()
            price = closes.iloc[-1]
            z_score = 0.0 if std_20 == 0 else (price - mean_20) / std_20
            
            # 2. RSI (14 days)
            rsi = ta.rsi(closes, length=14).iloc[-1]
            if pd.isna(rsi):
                rsi = 50.0
                
            # 3. Bollinger Bands (20 days, 2 std)
            bb = ta.bbands(closes, length=20, std=2)
            lower_band = bb['BBL_20_2.0'].iloc[-1] if not bb.empty else price
            
            # Conviction Logic
            conviction = 0.0
            indicators = {
                "Z-Score": z_score,
                "RSI": rsi,
                "Price": price,
                "LowerBand": lower_band
            }
            
            # Strong Buy Signals:
            # - Z-Score less than threshold
            # - RSI < 40 (approaching oversold)
            # - Price near or below lower bollinger band
            if z_score < self.z_score_threshold:
                conviction += 0.4
            if rsi < 40:
                conviction += 0.3
            elif rsi < 30: # Extreme
                conviction += 0.4 
            if price <= lower_band * 1.01: # Within 1% of lower band
                conviction += 0.3
                
            currency = ticker_data.fast_info.get('currency', 'USD')
            price_eur = self.convert_to_eur(price, currency)
            
            return min(conviction, 1.0), price_eur, indicators
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None, None, {}

class TradingBot:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("T212_API_KEY")
        self.api_url = os.getenv("T212_API_URL", "https://demo.trading212.com")
        self.api_id = os.getenv("TRADING212_ID")
        
        self.max_invest_pct = float(os.getenv("MAX_INVESTMENT_PCT", "0.8"))
        self.min_invest_eur = float(os.getenv("MIN_INVESTMENT_EUR", "5.0"))
        self.safety_cash = float(os.getenv("SAFETY_VALVE_CASH_THRESHOLD", "40.0"))
        self.safety_days = int(os.getenv("SAFETY_VALVE_DAYS", "20"))
        
        z_threshold = float(os.getenv("Z_SCORE_THRESHOLD", "-1.0"))
        
        assets_str = os.getenv("ASSETS", "EQQQ,VUSA,21XH")
        self.assets = [a.strip() for a in assets_str.split(',')]
        
        self.broker = Trading212Broker(self.api_key, self.api_url, self.api_id)
        self.strategy = EAStrategy(z_score_threshold=z_threshold)
        
        self.data_dir = "data"
        self.history_file = os.path.join(self.data_dir, "trades_history.csv")
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, mode='w', newline='') as f:
                csv.writer(f).writerow(["Date", "Ticker", "Price", "Quantity", "Fees", "Total", "Action"])

    def log_trade(self, ticker: str, price: float, quantity: float, total: float, action: str="BUY"):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.history_file, mode='a', newline='') as f:
            csv.writer(f).writerow([date_str, ticker, price, quantity, 0.0, total, action])
        logger.info(f"Logged {action}: {quantity} of {ticker} at {price} (Total: {total})")

    def get_days_since_last_trade(self) -> int:
        if not os.path.exists(self.history_file):
            return self.safety_days + 1
        try:
            df = pd.read_csv(self.history_file)
            if df.empty:
                return self.safety_days + 1
            last_date = datetime.datetime.strptime(df['Date'].iloc[-1], "%Y-%m-%d %H:%M:%S")
            return (datetime.datetime.now() - last_date).days
        except Exception as e:
            logger.error(f"Error reading history: {e}")
            return 0
            
    def is_market_open(self) -> bool:
        """Check if European/US Markets are roughly open. CET 09:00 to 22:00 allows trading on UK, Xetra and US"""
        tz = pytz.timezone("Europe/Rome")
        now_rome = datetime.datetime.now(tz)
        
        # Check if Weekend
        if now_rome.weekday() >= 5:
            return False
            
        # Check Time (09:00 - 22:15)
        # 09:00 connects Xetra, 22:00 closes Wall Street.
        if now_rome.hour >= 9 and now_rome.hour <= 22:
            return True
            
        return False

    def check_take_profits(self):
        """Phase 3: Gestione Posizioni Aperte. Verifichiamo se qualche asset è in grosso profitto."""
        # Se c'è una var d'ambiente TAKE_PROFIT_PCT, ad esempio '0.15' = 15%
        tp_threshold_str = os.getenv("TAKE_PROFIT_PCT")
        if not tp_threshold_str:
            return
            
        try:
            tp_threshold = float(tp_threshold_str)
        except:
            return
            
        portfolio = self.broker.get_portfolio()
        for asset, data in portfolio.items():
            avg_price = data['averagePrice']
            curr_price = data['currentPrice']
            qty = data['quantity']
            
            if avg_price > 0 and qty > 0:
                roi = (curr_price - avg_price) / avg_price
                if roi >= tp_threshold:
                    logger.info(f"TAKE PROFIT OPPORTUNITY per {asset}. ROI: {roi*100:.2f}% (Avg: {avg_price}, Curr: {curr_price})")
                    # Qui la logica di SELL effettiva se l'utente desidererà implementarla

    def run(self):
        logger.info("Starting Expert Advisor iteration...")
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.error("API Key non configurata.")
            return

        if not self.is_market_open():
            logger.info("Market Closed in session hours. Skipping.")
            return

        self.broker.resolve_tickers(self.assets)
        self.check_take_profits() # Opzionale, se TAKE_PROFIT_PCT è impostato
        
        free_cash = self.broker.get_free_cash()
        logger.info(f"Free Cash: {free_cash:.2f} EUR")
        
        if free_cash < self.min_invest_eur:
            return

        # 1. Analyze Market
        convictions = {}
        prices = {}
        
        tradeable_assets = [a for a in self.assets if a in self.broker.exact_ticker_map]
        for asset in tradeable_assets:
            conviction, price_eur, ind = self.strategy.analyze_asset(asset)
            if conviction is not None:
                convictions[asset] = conviction
                prices[asset] = price_eur
                logger.info(f"Strategy {asset} | Conviction: {conviction:.2f} | Z: {ind.get('Z-Score',0):.2f} | RSI: {ind.get('RSI',0):.2f}")

        # 2. Safety Valve
        days_idle = self.get_days_since_last_trade()
        if days_idle >= self.safety_days and free_cash > self.safety_cash:
            logger.info(f"Safety valve triggered (Idle for {days_idle} days). Forcing buy.")
            if convictions:
                best_asset = max(convictions, key=convictions.get)
                convictions[best_asset] = max(0.5, convictions[best_asset]) # Boost conviction
            
        # 3. Dynamic Allocation based on Conviction
        assets_to_buy = {a: c for a, c in convictions.items() if c > 0}
        
        if not assets_to_buy:
            logger.info("No trading signals met the criteria.")
            return
            
        max_investment = free_cash * self.max_invest_pct
        
        total_conv = sum(assets_to_buy.values())
        avg_conv = total_conv / len(assets_to_buy)
        
        dynamic_investment = max_investment * avg_conv
        
        if dynamic_investment < self.min_invest_eur:
            dynamic_investment = free_cash if free_cash < (self.min_invest_eur * 2) else self.min_invest_eur
            
        alloc_per_asset = dynamic_investment / len(assets_to_buy)
        
        # 4. Execute Orders
        for asset, conv in assets_to_buy.items():
            if alloc_per_asset >= self.min_invest_eur:
                price = prices[asset]
                qty = alloc_per_asset / price
                logger.info(f"Signal: BUY {asset} - Allocating {alloc_per_asset:.2f} EUR (Conviction: {conv:.2f})")
                success = self.broker.execute_market_order(asset, qty)
                if success:
                    self.log_trade(asset, price, qty, alloc_per_asset, "BUY")
            else:
                logger.debug(f"Allocation per {asset} ({alloc_per_asset}) < Minimum.")

def main():
    logger.info("Trading 212 Expert Advisor Started.")
    bot = TradingBot()
    
    # Run once at startup
    bot.run()

    # Schedule: every 30 minutes
    # It will only execute meaningful logic if during market hours
    schedule.every(30).minutes.do(bot.run)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
