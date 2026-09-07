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


STRATEGIES = {
    "mean_reversion": mean_reversion,
    "momentum": momentum,
    "buy_and_hold": buy_and_hold,
    "cash": cash,
}
