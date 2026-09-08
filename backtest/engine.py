"""Motore di backtest: da una serie di posizione giornaliera calcola equity curve
e metriche, con costi di transazione inclusi (T212 non applica commissioni su
azioni/ETF, ma spread e slippage reali esistono e vanno stimati)."""
import numpy as np
import pandas as pd

TRANSACTION_COST_PCT = 0.0015  # 0.15% per cambio di posizione (spread/slippage stimati)
TRADING_DAYS_PER_YEAR = 252


def run_backtest(df: pd.DataFrame, position: pd.Series) -> dict:
    price = df["Close"]
    daily_return = price.pct_change().fillna(0.0)

    position_change = position.diff().abs().fillna(position.iloc[0])
    cost = position_change * TRANSACTION_COST_PCT

    strategy_return = position.shift(1).fillna(0.0) * daily_return - cost
    equity = (1 + strategy_return).cumprod()

    return {
        "equity": equity,
        "daily_return": strategy_return,
        "n_trades": int(position_change[position_change > 0].count()),
    }


def cagr(equity: pd.Series) -> float:
    if len(equity) < 2 or equity.iloc[-1] <= 0:
        return -1.0
    years = len(equity) / TRADING_DAYS_PER_YEAR
    if years <= 0:
        return 0.0
    return equity.iloc[-1] ** (1 / years) - 1


def max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    return drawdown.min()


def sharpe(daily_return: pd.Series) -> float:
    std = daily_return.std()
    if std == 0 or np.isnan(std):
        return 0.0
    return (daily_return.mean() / std) * np.sqrt(TRADING_DAYS_PER_YEAR)


def win_rate(position: pd.Series, daily_return: pd.Series) -> float:
    """% di giorni investiti con rendimento positivo, sui giorni investiti."""
    invested_days = position.shift(1).fillna(0.0) > 0
    if invested_days.sum() == 0:
        return float("nan")
    return (daily_return[invested_days] > 0).mean()


def run_hfea_backtest(equity_df: pd.DataFrame, bond_df: pd.DataFrame, weight_equity: float = 0.55,
                       rebalance_freq: str = "QE") -> dict:
    """Portafoglio a due asset (leva azionaria + leva obbligazionaria) ribilanciato
    periodicamente al peso target, stile HFEA. Costo di transazione applicato solo
    nei giorni di ribilanciamento, proporzionale allo scostamento corretto."""
    idx = equity_df.index.intersection(bond_df.index)
    r_eq = equity_df.loc[idx, "Close"].pct_change().fillna(0.0)
    r_bond = bond_df.loc[idx, "Close"].pct_change().fillna(0.0)

    rebalance_dates = set(r_eq.resample(rebalance_freq).last().index) & set(idx)

    w_eq = weight_equity
    equity_curve = []
    value = 1.0
    for date in idx:
        value *= (1 + w_eq * r_eq.loc[date] + (1 - w_eq) * r_bond.loc[date])
        # drift naturale dei pesi dopo il rendimento del giorno
        eq_value = w_eq * (1 + r_eq.loc[date])
        bond_value = (1 - w_eq) * (1 + r_bond.loc[date])
        w_eq = eq_value / (eq_value + bond_value)

        if date in rebalance_dates and abs(w_eq - weight_equity) > 1e-9:
            turnover = abs(w_eq - weight_equity)
            value *= (1 - turnover * TRANSACTION_COST_PCT)
            w_eq = weight_equity

        equity_curve.append(value)

    equity = pd.Series(equity_curve, index=idx)
    daily_return = equity.pct_change().fillna(0.0)
    return {"equity": equity, "daily_return": daily_return, "n_trades": len(rebalance_dates)}


def summarize_hfea(equity_df: pd.DataFrame, bond_df: pd.DataFrame, weight_equity: float = 0.55) -> dict:
    result = run_hfea_backtest(equity_df, bond_df, weight_equity)
    equity = result["equity"]
    return {
        "cagr": cagr(equity),
        "max_drawdown": max_drawdown(equity),
        "sharpe": sharpe(result["daily_return"]),
        "n_trades": result["n_trades"],
        "win_rate": float("nan"),
        "final_equity": equity.iloc[-1] if len(equity) else float("nan"),
    }


def dual_momentum_returns(dfs: dict, lookback: int = 252) -> pd.Series:
    """Rendimento giornaliero di un portafoglio Dual Momentum: ogni fine mese,
    tiene l'asset con il rendimento a `lookback` giorni più alto tra quelli
    candidati, solo se quel rendimento è positivo (filtro assoluto), altrimenti
    cash. Ribilanciamento mensile, costo di transazione sul cambio di asset.

    Ritorna la serie di rendimenti giornalieri (non l'equity) così può essere
    tagliata per sotto-periodo e ricomposta da 1.0, come le altre strategie."""
    idx = None
    for df in dfs.values():
        idx = df.index if idx is None else idx.intersection(df.index)
    prices = {name: df.loc[idx, "Close"] for name, df in dfs.items()}
    returns = {name: p.pct_change().fillna(0.0) for name, p in prices.items()}
    momentum = {name: p.pct_change(lookback) for name, p in prices.items()}

    periods = pd.PeriodIndex(idx, freq="M")
    next_periods = periods[1:].append(pd.PeriodIndex([pd.Period("2999-01", freq="M")]))
    rebalance_dates = set(idx[periods != next_periods])

    current_asset = None
    daily_return = []
    for date in idx:
        r = returns[current_asset].loc[date] if current_asset else 0.0
        if date in rebalance_dates:
            candidates = {name: momentum[name].loc[date] for name in dfs if not pd.isna(momentum[name].loc[date])}
            best = max(candidates, key=candidates.get) if candidates else None
            new_asset = best if (best and candidates[best] > 0) else None
            if new_asset != current_asset:
                r -= TRANSACTION_COST_PCT
            current_asset = new_asset
        daily_return.append(r)

    return pd.Series(daily_return, index=idx)


def equal_weight_returns(dfs: dict) -> pd.Series:
    """Rendimento giornaliero di un paniere a pesi uguali sugli stessi asset di
    dual_momentum_returns, mai ribilanciato — baseline onesta per isolare
    l'effetto della rotazione, non solo quello di tenere più asset."""
    idx = None
    for df in dfs.values():
        idx = df.index if idx is None else idx.intersection(df.index)
    returns = pd.DataFrame({name: df.loc[idx, "Close"].pct_change().fillna(0.0) for name, df in dfs.items()})
    weight = 1.0 / len(dfs)
    values = {name: [] for name in dfs}
    for name in dfs:
        values[name] = weight * (1 + returns[name]).cumprod()
    total = pd.concat(values.values(), axis=1).sum(axis=1)
    return total.pct_change().fillna(total.iloc[0] - 1)


def summarize_from_returns(daily_return: pd.Series) -> dict:
    equity = (1 + daily_return).cumprod()
    return {
        "cagr": cagr(equity),
        "max_drawdown": max_drawdown(equity),
        "sharpe": sharpe(daily_return),
        "n_trades": None,
        "win_rate": float("nan"),
        "final_equity": equity.iloc[-1] if len(equity) else float("nan"),
    }


def summarize(df: pd.DataFrame, position: pd.Series) -> dict:
    result = run_backtest(df, position)
    equity = result["equity"]
    return {
        "cagr": cagr(equity),
        "max_drawdown": max_drawdown(equity),
        "sharpe": sharpe(result["daily_return"]),
        "n_trades": result["n_trades"],
        "win_rate": win_rate(position, result["daily_return"]),
        "final_equity": equity.iloc[-1] if len(equity) else float("nan"),
    }
