"""Orchestrazione Fase 2: esegue tutte le strategie su tutti gli asset, calcola le
metriche per sotto-periodo e applica le soglie di accettazione della Fase 3 —
FISSATE QUI, prima di guardare un solo risultato, per non aggiustarle a posteriori.
"""
from pathlib import Path

import pandas as pd

from data import download_all
from engine import run_backtest, summarize
from strategies import STRATEGIES

SUB_PERIODS = [
    ("2013-2015", "2013-01-01", "2015-12-31"),
    ("2016-2019", "2016-01-01", "2019-12-31"),
    ("2020 (crash+recupero)", "2020-01-01", "2020-12-31"),
    ("2021-2022 (bear)", "2021-01-01", "2022-12-31"),
    ("2023-oggi", "2023-01-01", None),
]
OOS_START = "2020-01-01"  # out-of-sample: mai guardato per scegliere i parametri sopra

# --- Soglie di accettazione (Fase 3), decise ORA ---
MIN_CAGR_EDGE_VS_BUYHOLD = 0.02      # +2 punti percentuali annualizzati sull'OOS
MIN_SUBPERIODS_BEATEN = 3            # su 5 sotto-periodi
MAX_ACCEPTABLE_DRAWDOWN = -0.75      # -75%, oltre è scartata a prescindere
SHARPE_MUST_NOT_WORSEN = True        # Sharpe OOS strategia >= Sharpe OOS buy&hold


def slice_period(df: pd.DataFrame, start: str, end: str | None) -> pd.DataFrame:
    if end:
        return df.loc[start:end]
    return df.loc[start:]


def cumulative_return(df: pd.DataFrame, position: pd.Series) -> float:
    result = run_backtest(df, position)
    return result["equity"].iloc[-1] - 1 if len(result["equity"]) else float("nan")


def main():
    data = download_all()
    rows = []
    verdicts = []

    for asset_name, df in data.items():
        for strat_name, strat_fn in STRATEGIES.items():
            if strat_name == "cash":
                continue  # cash è il pavimento di riferimento, non un candidato
            position_full = strat_fn(df)

            for period_name, start, end in SUB_PERIODS:
                df_p = slice_period(df, start, end)
                pos_p = position_full.loc[df_p.index]
                if len(df_p) < 30:
                    continue
                m = summarize(df_p, pos_p)
                bh_p = STRATEGIES["buy_and_hold"](df_p)
                bh_return = cumulative_return(df_p, bh_p)
                strat_return = cumulative_return(df_p, pos_p)
                rows.append({
                    "asset": asset_name, "strategy": strat_name, "period": period_name,
                    "cagr": m["cagr"], "max_dd": m["max_drawdown"], "sharpe": m["sharpe"],
                    "n_trades": m["n_trades"], "win_rate": m["win_rate"],
                    "cum_return": strat_return, "buyhold_cum_return": bh_return,
                    "beats_buyhold": strat_return > bh_return,
                })

            # --- Valutazione Fase 3 sull'out-of-sample (2020-oggi) ---
            df_oos = slice_period(df, OOS_START, None)
            pos_oos = position_full.loc[df_oos.index]
            m_oos = summarize(df_oos, pos_oos)
            bh_oos_pos = STRATEGIES["buy_and_hold"](df_oos)
            m_bh_oos = summarize(df_oos, bh_oos_pos)

            n_beaten = sum(
                1 for r in rows
                if r["asset"] == asset_name and r["strategy"] == strat_name and r["beats_buyhold"]
            )

            edge_ok = m_oos["cagr"] >= m_bh_oos["cagr"] + MIN_CAGR_EDGE_VS_BUYHOLD
            dd_ok = m_oos["max_drawdown"] >= MAX_ACCEPTABLE_DRAWDOWN
            sharpe_ok = (not SHARPE_MUST_NOT_WORSEN) or (m_oos["sharpe"] >= m_bh_oos["sharpe"])
            subperiods_ok = n_beaten >= MIN_SUBPERIODS_BEATEN

            passed = edge_ok and dd_ok and sharpe_ok and subperiods_ok
            verdicts.append({
                "asset": asset_name, "strategy": strat_name,
                "oos_cagr": m_oos["cagr"], "oos_cagr_buyhold": m_bh_oos["cagr"],
                "oos_max_dd": m_oos["max_drawdown"], "oos_sharpe": m_oos["sharpe"],
                "oos_sharpe_buyhold": m_bh_oos["sharpe"],
                "subperiods_beaten": f"{n_beaten}/{len(SUB_PERIODS)}",
                "edge_ok": edge_ok, "dd_ok": dd_ok, "sharpe_ok": sharpe_ok,
                "subperiods_ok": subperiods_ok, "PASSED": passed,
            })

    detail_df = pd.DataFrame(rows)
    verdict_df = pd.DataFrame(verdicts)

    out_dir = Path(__file__).parent
    detail_df.to_csv(out_dir / "risultati_dettaglio.csv", index=False)
    verdict_df.to_csv(out_dir / "risultati_verdetto.csv", index=False)

    write_report(detail_df, verdict_df, out_dir / "report.md")
    print(verdict_df.to_string(index=False))


def write_report(detail_df: pd.DataFrame, verdict_df: pd.DataFrame, path: Path):
    lines = ["# Risultati Fase 2 — Backtest\n"]
    lines.append("Soglie di accettazione (Fase 3), fissate prima di eseguire il backtest:\n")
    lines.append(f"- CAGR out-of-sample (2020-oggi) >= CAGR buy&hold + {MIN_CAGR_EDGE_VS_BUYHOLD:.0%}")
    lines.append(f"- Sharpe out-of-sample non peggiore di buy&hold")
    lines.append(f"- Max drawdown out-of-sample non oltre {MAX_ACCEPTABLE_DRAWDOWN:.0%}")
    lines.append(f"- Batte buy&hold in almeno {MIN_SUBPERIODS_BEATEN}/{len(SUB_PERIODS)} sotto-periodi\n")

    lines.append("## Verdetto per asset/strategia (out-of-sample 2020-oggi)\n")
    lines.append(verdict_df.to_markdown(index=False, floatfmt=".2%"))

    lines.append("\n\n## Dettaglio per sotto-periodo\n")
    lines.append(detail_df.to_markdown(index=False, floatfmt=".2%"))

    path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
