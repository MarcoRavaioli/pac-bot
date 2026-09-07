"""Strategie candidate (Fase 1 del piano). Ognuna produce una serie di posizione
giornaliera in {0.0, 1.0}: 0 = fuori mercato (cash), 1 = investito al 100% del
capitale allocato. Sizing binario in/out, non frazionario: evita il bug del bot
originale (reinvestiva frazioni decrescenti di un cash che si esauriva)."""
import numpy as np
import pandas as pd

STOP_LOSS_PCT = 0.15  # esce se il prezzo scende oltre il 15% dall'ingresso


def mean_reversion(df: pd.DataFrame, lookback: int = 20, buy_z: float = -1.0, sell_z: float = 0.5) -> pd.Series:
    """Compra sul dip (Z-score sotto soglia), vende quando il prezzo torna sopra
    media, con stop-loss. Evoluzione della logica del bot originale."""
    price = df["Close"]
    mean = price.rolling(lookback).mean()
    std = price.rolling(lookback).std()
    z = (price - mean) / std

    position = pd.Series(0.0, index=price.index)
    invested = False
    for i in range(len(price)):
        if pd.isna(z.iloc[i]):
            continue
        if not invested and z.iloc[i] < buy_z:
            invested = True
        elif invested and z.iloc[i] > sell_z:
            invested = False
        position.iloc[i] = 1.0 if invested else 0.0
    return _apply_stop_loss_vectorized(price, position)


def momentum(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
    """Trend-following classico: investito quando prezzo > MA veloce e MA veloce
    > MA lenta (uptrend confermato), fuori altrimenti."""
    price = df["Close"]
    ma_fast = price.rolling(fast).mean()
    ma_slow = price.rolling(slow).mean()
    raw = ((price > ma_fast) & (ma_fast > ma_slow)).astype(float)
    raw[ma_slow.isna()] = 0.0
    return _apply_stop_loss_vectorized(price, raw)


def buy_and_hold(df: pd.DataFrame) -> pd.Series:
    return pd.Series(1.0, index=df.index)


def cash(df: pd.DataFrame) -> pd.Series:
    return pd.Series(0.0, index=df.index)


def _apply_stop_loss_vectorized(price: pd.Series, raw_position: pd.Series) -> pd.Series:
    """Versione più semplice e verificabile dello stop-loss: cammina in avanti,
    esce forzatamente se il prezzo scende troppo dall'ingresso, resta fuori
    finché il segnale grezzo non ridiventa 1 dopo essere stato 0."""
    position = np.zeros(len(price))
    values = price.values
    raw = raw_position.values
    in_trade = False
    entry_price = 0.0
    for i in range(len(values)):
        if not in_trade:
            if raw[i] == 1.0:
                in_trade = True
                entry_price = values[i]
                position[i] = 1.0
        else:
            if raw[i] == 0.0:
                in_trade = False
                position[i] = 0.0
            elif values[i] <= entry_price * (1 - STOP_LOSS_PCT):
                in_trade = False
                position[i] = 0.0
            else:
                position[i] = 1.0
    return pd.Series(position, index=price.index)


def sma_underlying_200(df: pd.DataFrame, underlying_close: pd.Series) -> pd.Series:
    """Investito nell'ETF a leva quando l'indice SOTTOSTANTE (non leva) è sopra
    la sua media mobile a 200 giorni, altrimenti cash. Segnale pulito, calcolato
    su un indice senza il rumore del decadimento da leva — approccio documentato
    in letteratura (vedi docs/piano-strategia-alto-rischio.md, sezione ricerca)."""
    underlying_aligned = underlying_close.reindex(df.index, method="ffill")
    ma200 = underlying_aligned.rolling(200).mean()
    position = (underlying_aligned > ma200).astype(float)
    position[ma200.isna()] = 0.0
    return position


def vol_target(df: pd.DataFrame, target_annual_vol: float = 0.15, lookback: int = 20, max_position: float = 1.0) -> pd.Series:
    """Dimensiona l'esposizione in proporzione inversa alla volatilità realizzata
    invece di stare tutto dentro o tutto fuori: riduce l'esposizione quando il
    mercato è nervoso, la aumenta quando è calmo (capped a max_position)."""
    daily_return = df["Close"].pct_change()
    realized_vol = daily_return.rolling(lookback).std() * np.sqrt(252)
    position = (target_annual_vol / realized_vol).clip(upper=max_position)
    position[realized_vol.isna() | (realized_vol == 0)] = 0.0
    return position


STRATEGIES = {
    "mean_reversion": mean_reversion,
    "momentum": momentum,
    "vol_target": vol_target,
    "buy_and_hold": buy_and_hold,
    "cash": cash,
}
# sma_underlying_200 non è qui: richiede il sottostante come argomento extra,
# gestita a parte in run.py (una per asset, vedi data.UNDERLYING).
