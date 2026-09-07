"""Orchestrazione Fase 2: esegue tutte le strategie su tutti gli asset, calcola le
metriche per sotto-periodo e applica le soglie di accettazione della Fase 3 —
FISSATE QUI, prima di guardare un solo risultato, per non aggiustarle a posteriori.

Include sia le strategie originali (mean_reversion, momentum) sia le tre trovate
in ricerca (sma_underlying_200, vol_target, hfea) — stessa disciplina per tutte.
"""
from pathlib import Path

import pandas as pd

from data import download_all, UNDERLYING
from engine import run_backtest, summarize, summarize_hfea, run_hfea_backtest
from strategies import STRATEGIES, sma_underlying_200

SUB_PERIODS = [
    ("2013-2015", "2013-01-01", "2015-12-31"),
    ("2016-2019", "2016-01-01", "2019-12-31"),
    ("2020 (crash+recupero)", "2020-01-01", "2020-12-31"),
    ("2021-2022 (bear)", "2021-01-01", "2022-12-31"),
    ("2023-oggi", "2023-01-01", None),
]
OOS_START = "2020-01-01"  # out-of-sample: mai guardato per scegliere i parametri sopra

HFEA_PAIRS = [("QQQ3", "3BUL"), ("3USL", "3BUL")]
HFEA_WEIGHT_EQUITY = 0.55

# --- Soglie di accettazione (Fase 3), decise ORA, valide per OGNI candidato
# (vecchi e nuovi allo stesso modo) ---
MIN_CAGR_EDGE_VS_BUYHOLD = 0.02      # +2 punti percentuali annualizzati sull'OOS
MIN_SUBPERIODS_BEATEN = 3            # su 5 sotto-periodi
MAX_ACCEPTABLE_DRAWDOWN = -0.75      # -75%, oltre è scartata a prescindere
SHARPE_MUST_NOT_WORSEN = True        # Sharpe OOS strategia >= Sharpe OOS buy&hold


def slice_period(df: pd.DataFrame, start: str, end: str | None) -> pd.DataFrame:
    return df.loc[start:end] if end else df.loc[start:]


def cumulative_return(df: pd.DataFrame, position: pd.Series) -> float:
    result = run_backtest(df, position)
    return result["equity"].iloc[-1] - 1 if len(result["equity"]) else float("nan")


def evaluate(asset_label: str, strat_label: str, buyhold_summary_fn, candidate_summary_fn,
             candidate_return_fn, buyhold_return_fn, rows: list, verdicts: list):
    """buyhold_summary_fn/candidate_summary_fn: (start,end)->dict metriche.
    *_return_fn: (start,end)->rendimento cumulato netto."""
    n_beaten = 0
    for period_name, start, end in SUB_PERIODS:
        try:
            m = candidate_summary_fn(start, end)
            strat_ret = candidate_return_fn(start, end)
            bh_ret = buyhold_return_fn(start, end)
        except (KeyError, ZeroDivisionError):
            continue
        if m is None:
            continue
        beats = strat_ret > bh_ret
        n_beaten += int(beats)
        rows.append({
            "asset": asset_label, "strategy": strat_label, "period": period_name,
            "cagr": m["cagr"], "max_dd": m["max_drawdown"], "sharpe": m["sharpe"],
            "n_trades": m["n_trades"], "cum_return": strat_ret, "buyhold_cum_return": bh_ret,
            "beats_buyhold": beats,
        })

    m_oos = candidate_summary_fn(OOS_START, None)
    m_bh_oos = buyhold_summary_fn(OOS_START, None)
    if m_oos is None or m_bh_oos is None:
        return

    edge_ok = m_oos["cagr"] >= m_bh_oos["cagr"] + MIN_CAGR_EDGE_VS_BUYHOLD
    dd_ok = m_oos["max_drawdown"] >= MAX_ACCEPTABLE_DRAWDOWN
    sharpe_ok = (not SHARPE_MUST_NOT_WORSEN) or (m_oos["sharpe"] >= m_bh_oos["sharpe"])
    subperiods_ok = n_beaten >= MIN_SUBPERIODS_BEATEN
    verdicts.append({
        "asset": asset_label, "strategy": strat_label,
        "oos_cagr": m_oos["cagr"], "oos_cagr_buyhold": m_bh_oos["cagr"],
        "oos_max_dd": m_oos["max_drawdown"], "oos_sharpe": m_oos["sharpe"],
        "oos_sharpe_buyhold": m_bh_oos["sharpe"],
        "subperiods_beaten": f"{n_beaten}/{len(SUB_PERIODS)}",
        "edge_ok": edge_ok, "dd_ok": dd_ok, "sharpe_ok": sharpe_ok,
        "subperiods_ok": subperiods_ok, "PASSED": edge_ok and dd_ok and sharpe_ok and subperiods_ok,
    })


def main():
    data = download_all()
    rows, verdicts = [], []

    for asset_name in ("LQQ", "QQQ3", "XS2D", "3USL"):
        df = data[asset_name]
        bh_position = STRATEGIES["buy_and_hold"](df)

        def bh_summary(start, end, df=df, bh_position=bh_position):
            df_p = slice_period(df, start, end)
            if len(df_p) < 30:
                return None
            return summarize(df_p, bh_position.loc[df_p.index])

        def bh_return(start, end, df=df, bh_position=bh_position):
            df_p = slice_period(df, start, end)
            return cumulative_return(df_p, bh_position.loc[df_p.index])

        candidates = {}
        for strat_name in ("mean_reversion", "momentum", "vol_target"):
            position_full = STRATEGIES[strat_name](df)
            candidates[strat_name] = position_full

        underlying = data[UNDERLYING[asset_name]]["Close"]
        candidates["sma_underlying_200"] = sma_underlying_200(df, underlying)

        for strat_name, position_full in candidates.items():
            def cand_summary(start, end, df=df, pos=position_full):
                df_p = slice_period(df, start, end)
                if len(df_p) < 30:
                    return None
                return summarize(df_p, pos.loc[df_p.index])

            def cand_return(start, end, df=df, pos=position_full):
                df_p = slice_period(df, start, end)
                return cumulative_return(df_p, pos.loc[df_p.index])

            evaluate(asset_name, strat_name, bh_summary, cand_summary, cand_return, bh_return, rows, verdicts)

    # --- HFEA: coppie leva azionaria + leva obbligazionaria ---
    bond_df = data["3BUL"]
    for equity_name, bond_name in HFEA_PAIRS:
        eq_df = data[equity_name]
        label = f"HFEA({equity_name}+{bond_name})"
        bh_position_eq = STRATEGIES["buy_and_hold"](eq_df)

        def bh_summary(start, end, eq_df=eq_df, bh_position_eq=bh_position_eq):
            df_p = slice_period(eq_df, start, end)
            if len(df_p) < 30:
                return None
            return summarize(df_p, bh_position_eq.loc[df_p.index])

        def bh_return(start, end, eq_df=eq_df, bh_position_eq=bh_position_eq):
            df_p = slice_period(eq_df, start, end)
            return cumulative_return(df_p, bh_position_eq.loc[df_p.index])

        def cand_summary(start, end, eq_df=eq_df, bond_df=bond_df):
            eq_p = slice_period(eq_df, start, end)
            bond_p = slice_period(bond_df, start, end)
            if len(eq_p) < 30 or len(bond_p) < 30:
                return None
            return summarize_hfea(eq_p, bond_p, HFEA_WEIGHT_EQUITY)

        def cand_return(start, end, eq_df=eq_df, bond_df=bond_df):
            eq_p = slice_period(eq_df, start, end)
            bond_p = slice_period(bond_df, start, end)
            r = run_hfea_backtest(eq_p, bond_p, HFEA_WEIGHT_EQUITY)
            return r["equity"].iloc[-1] - 1 if len(r["equity"]) else float("nan")

        evaluate(label, "hfea", bh_summary, cand_summary, cand_return, bh_return, rows, verdicts)

    detail_df = pd.DataFrame(rows)
    verdict_df = pd.DataFrame(verdicts)

    out_dir = Path(__file__).parent
    detail_df.to_csv(out_dir / "risultati_dettaglio.csv", index=False)
    verdict_df.to_csv(out_dir / "risultati_verdetto.csv", index=False)
    write_report(detail_df, verdict_df, out_dir / "report.md")
    print(verdict_df.to_string(index=False))


def write_report(detail_df: pd.DataFrame, verdict_df: pd.DataFrame, path: Path):
    lines = ["# Risultati Fase 2 — Backtest\n"]
    lines.append("Soglie di accettazione (Fase 3), fissate prima di eseguire il backtest, "
                  "valide allo stesso modo per le strategie originali e per quelle emerse "
                  "dalla ricerca:\n")
    lines.append(f"- CAGR out-of-sample (2020-oggi) >= CAGR buy&hold + {MIN_CAGR_EDGE_VS_BUYHOLD:.0%}")
    lines.append("- Sharpe out-of-sample non peggiore di buy&hold")
    lines.append(f"- Max drawdown out-of-sample non oltre {MAX_ACCEPTABLE_DRAWDOWN:.0%}")
    lines.append(f"- Batte buy&hold in almeno {MIN_SUBPERIODS_BEATEN}/{len(SUB_PERIODS)} sotto-periodi\n")

    lines.append("## Verdetto per asset/strategia (out-of-sample 2020-oggi)\n")
    lines.append(verdict_df.to_markdown(index=False, floatfmt=".2%"))

    lines.append("\n\n## Dettaglio per sotto-periodo\n")
    lines.append(detail_df.to_markdown(index=False, floatfmt=".2%"))

    path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
