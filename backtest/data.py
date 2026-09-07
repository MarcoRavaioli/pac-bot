"""Scarica e mette in cache lo storico prezzi dei 4 ETF candidati (Fase 2 del piano)."""
from pathlib import Path

import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"

TICKERS = {
    "LQQ": "LQQ.PA",   # Amundi Nasdaq-100 Daily 2x Leveraged
    "QQQ3": "QQQ3.L",  # WisdomTree Nasdaq 100 3x Daily Leveraged
    "XS2D": "XS2D.L",  # Xtrackers S&P 500 2x Leveraged Daily Swap
    "3USL": "3USL.L",  # WisdomTree S&P 500 3x Daily Leveraged
}


OHLC = ["Open", "High", "Low", "Close"]


def _clean(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Corregge anomalie verificate manualmente nei dati Yahoo (nessuno split
    registrato in tk.splits, ma il prezzo mostra un salto e poi resta al nuovo
    livello: reverse split reale non gestito dal fornitore)."""
    df = df.copy()
    if name == "LQQ":
        # 2014-12-31: 86.29 -> 2015-01-02: 0.42, il prezzo resta lì dopo:
        # reverse split reale, riallineo all'indietro.
        before, after = df.loc["2014-12-31", "Close"], df.loc["2015-01-02", "Close"]
        ratio = after / before
        mask = df.index < "2015-01-02"
        df.loc[mask, OHLC] *= ratio
    if name == "3USL":
        # Stesso pattern a inizio serie (2012-12-17: 102.35 -> 2012-12-18: 5.05,
        # resta lì). Fuori dai sotto-periodi analizzati, corretto solo per non
        # sporcare le medie mobili che guardano indietro nel 2013.
        before, after = df.loc["2012-12-17", "Close"], df.loc["2012-12-18", "Close"]
        ratio = after / before
        mask = df.index < "2012-12-18"
        df.loc[mask, OHLC] *= ratio
        # 2017-06-26/27: +1900% e poi -95%, il giorno dopo torna esattamente al
        # livello di prima: glitch isolato del fornitore, non uno split. Interpolo.
        bad = pd.to_datetime(["2017-06-26", "2017-06-27"])
        df.loc[df.index.isin(bad), OHLC] = float("nan")
        df[OHLC] = df[OHLC].interpolate()
    return df


def download_all(force: bool = False) -> dict[str, pd.DataFrame]:
    DATA_DIR.mkdir(exist_ok=True)
    out = {}
    for name, ticker in TICKERS.items():
        path = DATA_DIR / f"{name}.csv"
        if path.exists() and not force:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
        else:
            df = yf.Ticker(ticker).history(period="max", auto_adjust=True)
            df.index = df.index.tz_localize(None)
            df.to_csv(path)
        out[name] = _clean(name, df)
    return out


if __name__ == "__main__":
    data = download_all(force=True)
    for name, df in data.items():
        print(name, df.index[0].date(), "->", df.index[-1].date(), f"({len(df)} righe)")
