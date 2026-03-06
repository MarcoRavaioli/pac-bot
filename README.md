# Trading 212 Automated Bot

A Python-based automated investment bot for Trading 212, designed to run on a Raspberry Pi (ARM64). The bot monitors a list of high-risk/high-growth assets (EQQQ, VUSA, 21XH) and invests small amounts monthly based on a 20-day Z-Score strategy.

## Features

- **Z-Score Strategy**: Buys assets when their 20-day Z-Score drops below -1.0 (mild dip).
- **Safety Valve**: Forces a buy on the lowest Z-score asset if cash > 40€ and no trade occurred in the last 20 days.
- **Dynamic Sizing**: Invests a safe percentage (e.g., 80%) of available free cash.
- **Tax Compliance (Italy)**: Logs all trades to `data/trades_history.csv` including Date, Ticker, Price, Quantity, and Fees for 'Quadro RW'.
- **Dockerized for Raspberry Pi**: Ready to run 24/7.

## Setup Instructions

1. **Clone the repository** (if applicable) and navigate to the directory.
2. **Setup Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Trading 212 API key (Practice or Live).
3. **Build and Run**:
   ```bash
   docker-compose up -d --build
   ```
4. **View Logs**:
   ```bash
   docker-compose logs -f
   ```

## Configuration (`.env`)

- `T212_API_KEY`: Your Account API Key.
- `T212_API_URL`: Use `https://demo.trading212.com` for Practice or `https://live.trading212.com` for Real Money.
- `MAX_INVESTMENT_PCT`: Percentage of total free cash to invest per signal (default: `0.8` for 80%).
- `MIN_INVESTMENT_EUR`: Minimum trade amount (default: `5.0`).
- `ASSETS`: Comma-separated list of instruments to trade.
