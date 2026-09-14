"""Bot di Fase 4 — paper trading della strategia `sma_underlying_200` su XS2D.

Regola, in una riga: investito nell'ETF a leva finché l'S&P 500 (indice
sottostante, non a leva) chiude sopra la sua media mobile a 200 giorni; fuori,
tutto in cash, quando chiude sotto.

Differenze rispetto al bot precedente (vedi docs/piano-strategia-alto-rischio.md):

- il sizing non guarda più il cash disponibile del conto (era la causa del bug
  originale: frazioni decrescenti di un saldo che si esauriva) ma un budget
  nozionale fisso tracciato da un contatore interno in `data/fase4_state.json`;
- la vendita esiste davvero: il vecchio `check_take_profits` si limitava a
  loggare un'opportunità;
- c'è un kill-switch sul drawdown dal picco che ferma il bot e chiede conferma
  manuale;
- gira una volta al giorno, non ogni 30 minuti: il segnale usa chiusure
  giornaliere, calcolarlo più spesso aggiunge solo chiamate e superficie di bug.

Fonte del segnale: Yahoo Finance (^GSPC), la stessa serie usata nel backtest.
L'API di Trading212 non espone prezzi storici (nessun endpoint di candele, il
metadata degli strumenti non contiene prezzi, `currentPrice` esiste solo dentro
una posizione già aperta): per una media a 200 giorni non è una fonte possibile.
Lo storico scaricato viene tenuto in cache su disco, così un'interruzione di
Yahoo non blocca il segnale; se la cache diventa troppo vecchia il bot non opera
e avvisa su Telegram.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import schedule
import yfinance as yf
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fase4")

ROME = ZoneInfo("Europe/Rome")

# Ora italiana dopo la quale la chiusura USA del giorno e' consolidata su Yahoo.
# Prima di quest'ora la riga di oggi, se c'e', e' una quotazione intraday.
ORA_CHIUSURA_USA = (22, 15)


# --------------------------------------------------------------------------- #
# Configurazione
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    api_key: str
    api_id: str
    api_url: str
    t212_ticker: str          # ticker Trading212 dell'ETF a leva da comprare
    yf_asset: str             # stesso ETF su Yahoo, serve solo per il prezzo di sizing
    yf_signal: str            # indice sottostante su Yahoo, da cui esce il segnale
    sma_window: int
    budget_eur: float
    kill_switch_dd: float     # es. 0.30 = si ferma a -30% dal picco
    max_staleness_days: int   # oltre questa età dei dati il bot non opera
    run_at: str               # "HH:MM" ora italiana
    min_order_eur: float
    slippage_buffer: float    # margine sul sizing per non sforare il budget
    telegram_token: str
    telegram_chat_id: str
    data_dir: Path

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            api_key=os.getenv("T212_API_KEY", "").strip(),
            api_id=os.getenv("TRADING212_ID", "").strip(),
            api_url=os.getenv("T212_API_URL", "https://demo.trading212.com").strip().rstrip("/"),
            t212_ticker=os.getenv("T212_TICKER", "XS2Dl_EQ").strip(),
            yf_asset=os.getenv("YF_ASSET_TICKER", "XS2D.L").strip(),
            yf_signal=os.getenv("YF_SIGNAL_TICKER", "^GSPC").strip(),
            sma_window=int(os.getenv("SMA_WINDOW", "200")),
            budget_eur=float(os.getenv("BUDGET_EUR", "350")),
            kill_switch_dd=float(os.getenv("KILL_SWITCH_DRAWDOWN", "0.30")),
            max_staleness_days=int(os.getenv("MAX_SIGNAL_STALENESS_DAYS", "5")),
            run_at=os.getenv("RUN_AT", "09:05").strip(),
            min_order_eur=float(os.getenv("MIN_ORDER_EUR", "5.0")),
            slippage_buffer=float(os.getenv("SLIPPAGE_BUFFER", "0.005")),
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            data_dir=Path(os.getenv("DATA_DIR", "data")),
        )


# --------------------------------------------------------------------------- #
# Notifiche
# --------------------------------------------------------------------------- #
class Notifier:
    """Manda messaggi su Telegram con l'API HTTP diretta. Se il token non è
    configurato logga soltanto: il bot deve funzionare anche senza notifiche."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, text: str) -> bool:
        logger.info("NOTIFICA: %s", text.replace("\n", " | "))
        if not self.enabled:
            logger.warning("Telegram non configurato: messaggio solo a log.")
            return False
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": text},
                timeout=15,
            )
            if resp.status_code != 200:
                logger.error("Telegram ha risposto %s: %s", resp.status_code, resp.text[:200])
                return False
            return True
        except Exception as exc:  # rete assente, DNS, timeout
            logger.error("Invio Telegram fallito: %s", exc)
            return False


# --------------------------------------------------------------------------- #
# Broker
# --------------------------------------------------------------------------- #
class Trading212Broker:
    """Solo le chiamate che servono a questa strategia.

    Autenticazione: Basic con `TRADING212_ID:T212_API_KEY`. Verificato il
    2026-09-08 contro il conto demo: l'header semplice `Authorization: <chiave>`
    risponde 401, il Basic risponde 200.
    """

    def __init__(self, api_key: str, api_id: str, api_url: str):
        self.api_key = api_key
        self.api_id = api_id
        self.api_url = api_url.rstrip("/")

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_id:
            credentials = f"{self.api_id}:{self.api_key}"
            encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded}"
        else:
            headers["Authorization"] = self.api_key
        return headers

    def get_cash(self) -> dict:
        resp = requests.get(
            f"{self.api_url}/api/v0/equity/account/cash", headers=self._headers(), timeout=15
        )
        resp.raise_for_status()
        return resp.json()

    def get_position(self, ticker: str) -> Optional[dict]:
        """Posizione aperta sul ticker, o None. Usa /positions perché include
        `walletImpact` con costo e valore correnti già in euro (valuta del
        conto): niente conversioni fatte da noi per il kill-switch."""
        resp = requests.get(
            f"{self.api_url}/api/v0/equity/positions", headers=self._headers(), timeout=15
        )
        resp.raise_for_status()
        for pos in resp.json():
            if (pos.get("instrument") or {}).get("ticker") == ticker:
                impact = pos.get("walletImpact") or {}
                return {
                    "quantity": float(pos.get("quantity") or 0.0),
                    "quantity_sellable": float(pos.get("quantityAvailableForTrading") or 0.0),
                    "current_price": float(pos.get("currentPrice") or 0.0),
                    "total_cost_eur": float(impact.get("totalCost") or 0.0),
                    "current_value_eur": float(impact.get("currentValue") or 0.0),
                    "unrealized_pl_eur": float(impact.get("unrealizedProfitLoss") or 0.0),
                    "created_at": pos.get("createdAt") or "",
                }
        return None

    def get_fills(self, ticker: str, since: datetime) -> list[dict]:
        """Esecuzioni sul ticker avvenute da `since` in poi, dalla più recente.

        Servono per sapere quanto denaro si è mosso davvero: `netValue` è in euro
        e comprende le commissioni. Convenzione verificata sul conto demo l'8/9:
        acquisto XS2D `netValue` 348,35 = controvalore 347,83 + commissione di
        cambio 0,52; vendita VUSA `netValue` 997,70 = incasso, positivo. Una
        vendita con commissione di cambio non è ancora stata osservata.

        Rate limit dell'endpoint: 6 richieste al minuto. Il bot ne fa una a giro.
        """
        fills: list[dict] = []
        path = f"/api/v0/equity/history/orders?ticker={ticker}&limit=50"
        for _ in range(5):  # 250 esecuzioni: per questa strategia è molto oltre il necessario
            resp = requests.get(f"{self.api_url}{path}", headers=self._headers(), timeout=15)
            resp.raise_for_status()
            body = resp.json()
            troppo_vecchio = False
            for item in body.get("items") or []:
                fill = item.get("fill") or {}
                order = item.get("order") or {}
                if not fill.get("filledAt"):
                    continue  # ordine annullato o non eseguito
                filled_at = datetime.fromisoformat(fill["filledAt"].replace("Z", "+00:00"))
                if filled_at < since:
                    troppo_vecchio = True
                    continue
                impact = fill.get("walletImpact") or {}
                fees = sum(-float(t.get("quantity") or 0.0) for t in impact.get("taxes") or [])
                fills.append({
                    "side": order.get("side") or ("BUY" if float(fill.get("quantity") or 0) > 0 else "SELL"),
                    "quantity": abs(float(fill.get("quantity") or 0.0)),
                    "net_value_eur": float(impact.get("netValue") or 0.0),
                    "fees_eur": round(fees, 2),
                    "filled_at": filled_at,
                })
            path = body.get("nextPagePath")
            if not path or troppo_vecchio:
                break
        return fills

    def place_market_order(self, ticker: str, quantity: float, precision: int = 5) -> dict:
        """Quantità positiva = acquisto, negativa = vendita (convenzione T212).
        Se l'API rifiuta la precisione decimale, riprova con una cifra in meno."""
        qty = round(quantity, precision) if precision > 0 else float(int(quantity))
        resp = requests.post(
            f"{self.api_url}/api/v0/equity/orders/market",
            headers=self._headers(),
            json={"ticker": ticker, "quantity": qty},
            timeout=20,
        )
        if resp.status_code == 200:
            logger.info("Ordine accettato: %s di %s", qty, ticker)
            return {"ok": True, "quantity": qty, "response": resp.json()}
        if resp.status_code == 400 and "quantity-precision-mismatch" in resp.text and precision > 0:
            logger.warning("Precisione %s rifiutata per %s, riprovo con %s.", precision, ticker, precision - 1)
            return self.place_market_order(ticker, quantity, precision - 1)
        logger.error("Ordine rifiutato per %s: %s - %s", ticker, resp.status_code, resp.text[:300])
        return {"ok": False, "quantity": qty, "error": f"{resp.status_code} {resp.text[:300]}"}


# --------------------------------------------------------------------------- #
# Segnale
# --------------------------------------------------------------------------- #
@dataclass
class Signal:
    date: pd.Timestamp
    close: float
    sma: float
    invested: bool          # True = si sta sopra la media, quindi dentro
    age_days: int           # giorni di calendario tra l'ultima chiusura e oggi
    from_cache: bool        # True se Yahoo non ha risposto e si è usata la cache


class SignalSource:
    """Chiusure giornaliere dell'indice sottostante, con cache su disco.

    La cache non è un'ottimizzazione ma una rete di sicurezza: se Yahoo non
    risponde il segnale resta calcolabile sui dati di ieri (una SMA a 200 giorni
    non cambia idea da un giorno all'altro). Se invece i dati diventano vecchi
    oltre `max_staleness_days` il bot smette di operare e avvisa: preferisco un
    bot fermo a un bot che decide su prezzi di due settimane fa.
    """

    def __init__(self, yf_ticker: str, window: int, cache_path: Path, max_staleness_days: int):
        self.yf_ticker = yf_ticker
        self.window = window
        self.cache_path = cache_path
        self.max_staleness_days = max_staleness_days

    def _read_cache(self) -> Optional[pd.Series]:
        if not self.cache_path.exists():
            return None
        try:
            df = pd.read_csv(self.cache_path, index_col=0, parse_dates=True)
            if df.empty or "Close" not in df.columns:
                return None
            return df["Close"].astype(float).sort_index()
        except Exception as exc:
            logger.error("Cache del segnale illeggibile (%s): %s", self.cache_path, exc)
            return None

    def _write_cache(self, closes: pd.Series) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        closes.to_frame("Close").to_csv(self.cache_path)

    def _download(self) -> Optional[pd.Series]:
        try:
            # 2 anni bastano ampiamente per una media a 200 giorni di borsa.
            hist = yf.Ticker(self.yf_ticker).history(period="2y", auto_adjust=True)
            if hist.empty or "Close" not in hist:
                logger.error("Yahoo ha risposto senza dati per %s.", self.yf_ticker)
                return None
            closes = hist["Close"].astype(float)
            closes.index = pd.DatetimeIndex(closes.index).tz_localize(None).normalize()
            return closes.sort_index()
        except Exception as exc:
            logger.error("Download da Yahoo fallito per %s: %s", self.yf_ticker, exc)
            return None

    @staticmethod
    def _scarta_barra_incompleta(closes: pd.Series, now: datetime) -> pd.Series:
        """Toglie la riga di oggi finché la seduta USA non è chiusa.

        La strategia è definita sulle chiusure giornaliere: durante la seduta
        Yahoo restituisce la quotazione corrente come se fosse la riga di oggi, e
        un giro lanciato a mano nel pomeriggio deciderebbe su un prezzo intraday
        invece che su una chiusura. Alle 09:05, l'orario del giro automatico, il
        caso non si presenta — ma un `--once` di pomeriggio sì.
        """
        if len(closes) == 0:
            return closes
        oggi = now.date()
        chiusura_fatta = (now.hour, now.minute) >= ORA_CHIUSURA_USA
        if closes.index[-1].date() == oggi and not chiusura_fatta:
            logger.info(
                "Scarto la riga di oggi (%s): la seduta USA non è ancora chiusa, "
                "sarebbe una quotazione intraday e non una chiusura.", oggi,
            )
            return closes.iloc[:-1]
        return closes

    def get(self, now: Optional[datetime] = None) -> Optional[Signal]:
        """None se non c'è abbastanza storia o se i dati sono troppo vecchi."""
        now = now or datetime.now(ROME)
        cached = self._read_cache()
        fresh = self._download()

        if fresh is not None:
            closes = fresh if cached is None else fresh.combine_first(cached).sort_index()
            self._write_cache(closes)
            from_cache = False
        elif cached is not None:
            closes = cached
            from_cache = True
            logger.warning("Yahoo non disponibile: uso la cache (ultima chiusura %s).", closes.index[-1].date())
        else:
            logger.error("Nessun dato di segnale: né Yahoo né cache.")
            return None

        closes = self._scarta_barra_incompleta(closes, now)

        if len(closes) < self.window:
            logger.error("Storico troppo corto per la SMA-%s: solo %s righe.", self.window, len(closes))
            return None

        last_date = closes.index[-1]
        age = (now.date() - last_date.date()).days
        if age > self.max_staleness_days:
            logger.error(
                "Dati del segnale vecchi di %s giorni (ultima chiusura %s, limite %s).",
                age, last_date.date(), self.max_staleness_days,
            )
            return None

        sma = float(closes.rolling(self.window).mean().iloc[-1])
        close = float(closes.iloc[-1])
        return Signal(
            date=last_date,
            close=close,
            sma=sma,
            invested=close > sma,
            age_days=age,
            from_cache=from_cache,
        )


class PriceSource:
    """Prezzo corrente dell'ETF, convertito in euro: serve solo a trasformare il
    budget in una quantità di quote, perché l'API T212 accetta ordini a quantità
    e non a controvalore. Un errore di qualche decimo di percento qui sposta di
    pochi centesimi l'importo investito, non la strategia."""

    FALLBACK_FX = {"USD": 0.92, "GBP": 1.17, "GBp": 0.0117, "EUR": 1.0}

    def __init__(self, yf_ticker: str):
        self.yf_ticker = yf_ticker

    def _fx_to_eur(self, currency: str) -> Optional[float]:
        if currency == "EUR":
            return 1.0
        pair = {"USD": "USDEUR=X", "GBP": "GBPEUR=X", "GBp": "GBPEUR=X"}.get(currency)
        if pair is None:
            logger.error("Valuta non gestita: %s", currency)
            return None
        try:
            hist = yf.Ticker(pair).history(period="5d", auto_adjust=True)
            if hist.empty:
                raise ValueError("serie vuota")
            rate = float(hist["Close"].iloc[-1])
            return rate / 100.0 if currency == "GBp" else rate
        except Exception as exc:
            logger.warning("Cambio %s non disponibile (%s): uso il fallback.", pair, exc)
            return self.FALLBACK_FX.get(currency)

    def price_eur(self) -> Optional[float]:
        try:
            ticker = yf.Ticker(self.yf_ticker)
            hist = ticker.history(period="5d", auto_adjust=True)
            if hist.empty:
                logger.error("Nessun prezzo da Yahoo per %s.", self.yf_ticker)
                return None
            price = float(hist["Close"].iloc[-1])
            currency = "EUR"
            try:
                currency = ticker.fast_info.get("currency") or "EUR"
            except Exception:
                logger.warning("Valuta di %s non leggibile: assumo EUR.", self.yf_ticker)
            fx = self._fx_to_eur(currency)
            if not fx:
                return None
            return price * fx
        except Exception as exc:
            logger.error("Prezzo di %s non recuperabile: %s", self.yf_ticker, exc)
            return None


# --------------------------------------------------------------------------- #
# Stato persistente
# --------------------------------------------------------------------------- #
@dataclass
class State:
    """Il contatore interno del capitale allocato. È qui, e non nel saldo del
    conto, che il bot legge quanto può investire: il conto demo ha 5000€ che non
    c'entrano nulla con i 350€ che stiamo validando."""

    cash_eur: float                       # capitale allocato non investito
    invested: bool = False
    quantity: float = 0.0
    cash_before_buy: float = -1.0         # cash prima dell'ultimo acquisto (-1 = non impostato)
    last_position_value_eur: float = 0.0  # ultima valutazione nota della posizione, in euro
    peak_equity_eur: float = 0.0          # massimo storico di (cash + posizione)
    killed: bool = False
    kill_reason: str = ""
    last_signal_date: str = ""
    last_action_date: str = ""
    last_run_utc: str = ""
    consecutive_errors: int = 0
    last_error: str = ""
    stale_alert_date: str = ""            # per non ripetere l'alert ogni giro
    ticker: str = ""                      # strumento a cui si riferiscono posizione e contatore
    pending_sell_estimate_eur: float = 0.0  # incasso stimato dell'ultima vendita, da confermare
    pending_sell_since_utc: str = ""      # istante della vendita, per ritrovarne l'esecuzione

    @classmethod
    def load(cls, path: Path, budget_eur: float) -> "State":
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                known = {f for f in cls.__dataclass_fields__}
                return cls(**{k: v for k, v in raw.items() if k in known})
            except Exception as exc:
                logger.error("Stato illeggibile (%s): %s — riparto da zero.", path, exc)
        return cls(cash_eur=budget_eur, peak_equity_eur=budget_eur)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=False))
        tmp.replace(path)  # scrittura atomica: uno stato mezzo scritto è peggio di nessuno


# --------------------------------------------------------------------------- #
# Bot
# --------------------------------------------------------------------------- #
# Tolleranza sui timestamp di Trading212. Verificato l'8/9: `filledAt` del fill
# (14:18:51.000Z) è PRIMA del `createdAt` della posizione (14:18:51.767Z), perché
# il fill ha i secondi troncati. Senza margine l'acquisto verrebbe escluso.
MARGINE_TIMESTAMP = timedelta(minutes=2)


class Fase4Bot:
    def __init__(self, cfg: Config, broker=None, signal_source=None, price_source=None, notifier=None):
        self.cfg = cfg
        self.broker = broker or Trading212Broker(cfg.api_key, cfg.api_id, cfg.api_url)
        self.signal_source = signal_source or SignalSource(
            cfg.yf_signal, cfg.sma_window, cfg.data_dir / "signal_cache.csv", cfg.max_staleness_days
        )
        self.price_source = price_source or PriceSource(cfg.yf_asset)
        self.notifier = notifier or Notifier(cfg.telegram_token, cfg.telegram_chat_id)
        self.state_path = cfg.data_dir / "fase4_state.json"
        self.trades_path = cfg.data_dir / "fase4_trades.csv"
        self.state = State.load(self.state_path, cfg.budget_eur)

    # ---------------------------------------------------------------- utility
    def _log_trade(self, action: str, quantity: float, price_eur: float, signal: Signal, note: str = "") -> None:
        self.cfg.data_dir.mkdir(parents=True, exist_ok=True)
        new_file = not self.trades_path.exists()
        with self.trades_path.open("a", newline="") as fh:
            writer = csv.writer(fh)
            if new_file:
                writer.writerow(
                    ["timestamp", "azione", "ticker", "quantita", "prezzo_eur", "controvalore_eur",
                     "data_segnale", "close_indice", "sma_indice", "cash_residuo_eur", "nota"]
                )
            writer.writerow([
                datetime.now(ROME).strftime("%Y-%m-%d %H:%M:%S"),
                action, self.cfg.t212_ticker, f"{quantity:.6f}", f"{price_eur:.4f}",
                f"{quantity * price_eur:.2f}", signal.date.date(), f"{signal.close:.2f}",
                f"{signal.sma:.2f}", f"{self.state.cash_eur:.2f}", note,
            ])

    def _record_error(self, message: str) -> None:
        self.state.consecutive_errors += 1
        self.state.last_error = message
        logger.error("%s (errori consecutivi: %s)", message, self.state.consecutive_errors)
        # Criterio di Fase 4: lo stesso problema per più di 2 cicli è uno STOP da indagare.
        if self.state.consecutive_errors > 2:
            self.notifier.send(
                f"⚠️ Bot Fase 4: {self.state.consecutive_errors} cicli consecutivi in errore.\n"
                f"Ultimo errore: {message}\nIl bot non sta operando: serve un controllo."
            )

    def _clear_errors(self) -> None:
        self.state.consecutive_errors = 0
        self.state.last_error = ""

    # ------------------------------------------------------------------- core
    def run_once(self, dry_run: bool = False, now: Optional[datetime] = None) -> str:
        """Un ciclo completo. Ritorna una stringa con l'esito, utile nei test."""
        now = now or datetime.now(ROME)
        # Il processo principale vive per settimane, mentre `--once` e `--resume`
        # girano in processi separati (`docker exec`) e scrivono lo stesso file.
        # Tenere lo stato in memoria dall'avvio voleva dire sovrascrivere le loro
        # modifiche: il 9/9 ha prodotto un falso "posizione disallineata", e un
        # `--resume` dopo il kill-switch sarebbe stato annullato in silenzio.
        self.state = State.load(self.state_path, self.cfg.budget_eur)
        self.state.last_run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
        outcome = "nessuna-azione"
        try:
            outcome = self._run_once_inner(dry_run, now)
        finally:
            self.state.save(self.state_path)
        return outcome

    def _run_once_inner(self, dry_run: bool, now: datetime) -> str:
        if self.state.killed:
            logger.warning(
                "Kill-switch attivo (%s): nessuna operazione. Riattivare con `--resume`.",
                self.state.kill_reason or "motivo non registrato",
            )
            return "kill-switch-attivo"

        signal = self.signal_source.get(now=now)
        if signal is None:
            self._record_error("Segnale non disponibile (Yahoo giù e cache assente o troppo vecchia).")
            oggi = now.date().isoformat()
            if self.state.stale_alert_date != oggi:
                self.state.stale_alert_date = oggi
                self.notifier.send(
                    "⚠️ Bot Fase 4: dati del segnale non disponibili o troppo vecchi.\n"
                    "Nessuna operazione eseguita oggi."
                )
            return "segnale-non-disponibile"

        if self.state.invested and self.state.ticker and self.state.ticker != self.cfg.t212_ticker:
            # Cambiare T212_TICKER a posizione aperta farebbe credere al bot che la
            # posizione sia stata venduta a mano (sul ticker nuovo non c'è nulla),
            # con un riaccredito finto e un acquisto sul nuovo strumento mentre il
            # vecchio resta aperto. Il cambio va fatto solo a bot in cash.
            messaggio = (
                f"T212_TICKER cambiato in {self.cfg.t212_ticker} mentre il bot è investito su "
                f"{self.state.ticker}. Nessuna operazione: rimettere il ticker precedente, "
                "oppure cambiarlo solo quando `--status` dice IN CASH."
            )
            self._record_error(messaggio)
            self.notifier.send(f"⚠️ Bot Fase 4: {messaggio}")
            return "ticker-cambiato-da-investito"
        if not self.state.invested and self.state.ticker != self.cfg.t212_ticker:
            if self.state.ticker:
                logger.info("Ticker cambiato da %s a %s a bot in cash: da ora opero sul nuovo.",
                            self.state.ticker, self.cfg.t212_ticker)
            self.state.ticker = self.cfg.t212_ticker
        elif not self.state.ticker:
            self.state.ticker = self.cfg.t212_ticker  # stato scritto prima che il campo esistesse

        try:
            position = self.broker.get_position(self.cfg.t212_ticker)
        except Exception as exc:
            self._record_error(f"Lettura posizione fallita: {exc}")
            return "errore-broker"

        self._clear_errors()
        anomalia = self._reconcile(position)

        equity = self._equity(position)
        if anomalia:
            # Il contenuto del recinto è cambiato fuori dal bot: il vecchio picco
            # si riferisce a un capitale diverso e produrrebbe un drawdown finto.
            logger.warning(
                "Riallineamento con il broker: riporto il picco da %.2f€ a %.2f€ (equity attuale).",
                self.state.peak_equity_eur, equity,
            )
            self.state.peak_equity_eur = equity
            self.notifier.send(
                "ℹ️ Bot Fase 4: posizione disallineata rispetto allo stato interno "
                f"(ora: {'investito' if self.state.invested else 'in cash'}).\n"
                f"Stato riallineato al broker: capitale allocato {self.state.cash_eur:.2f}€, "
                f"picco riportato a {equity:.2f}€ per non far scattare il kill-switch "
                "su un salto contabile.\nNessuna operazione in questo giro: si riparte dal prossimo."
            )
        elif equity > self.state.peak_equity_eur:
            self.state.peak_equity_eur = equity
        drawdown = (equity / self.state.peak_equity_eur - 1.0) if self.state.peak_equity_eur > 0 else 0.0

        logger.info(
            "Segnale %s: chiusura %s = %.2f, SMA-%s = %.2f -> %s | equity %.2f€ (picco %.2f€, drawdown %.1f%%)",
            self.cfg.yf_signal, signal.date.date(), signal.close, self.cfg.sma_window, signal.sma,
            "DENTRO" if signal.invested else "FUORI", equity, self.state.peak_equity_eur, drawdown * 100,
        )
        self.state.last_signal_date = signal.date.date().isoformat()

        if anomalia:
            # Qualcuno ha operato a mano su questo strumento. Il bot si prende un
            # giro di pausa: chi ha ricevuto la notifica ha il tempo di guardare
            # prima che riparta da solo a comprare o vendere.
            logger.warning("Giro saltato dopo il riallineamento: si riprende al prossimo ciclo.")
            return "riallineamento"

        if drawdown <= -self.cfg.kill_switch_dd:
            self.state.killed = True
            self.state.kill_reason = (
                f"drawdown {drawdown * 100:.1f}% dal picco di {self.state.peak_equity_eur:.2f}€ "
                f"(equity {equity:.2f}€) il {now.date().isoformat()}"
            )
            self.notifier.send(
                f"🛑 KILL-SWITCH Bot Fase 4\n"
                f"Drawdown {drawdown * 100:.1f}% dal picco ({self.state.peak_equity_eur:.2f}€ -> {equity:.2f}€).\n"
                f"Il bot si ferma e non opera più: la posizione resta aperta.\n"
                f"Per riattivarlo serve una conferma manuale (vedi runbook)."
            )
            return "kill-switch-scattato"

        if signal.invested and not self.state.invested:
            return self._buy(signal, dry_run)
        if not signal.invested and self.state.invested:
            return self._sell(signal, position, dry_run)

        logger.info("Nessun cambio di posizione: segnale e stato coincidono (%s).",
                    "investito" if self.state.invested else "in cash")
        return "nessuna-azione"

    def _reconcile(self, position: Optional[dict]) -> bool:
        """Allinea lo stato interno a quello che dice il broker.

        Ritorna True se ha trovato un'anomalia, cioè una posizione comparsa o
        sparita senza che sia stato il bot a farlo: un ordine eseguito a mano
        dalla app, uno stato perso, un container ricreato. In quel caso il
        capitale del recinto cambia per motivi contabili e non di mercato, e chi
        chiama deve riancorare il picco invece di leggere un finto drawdown —
        il kill-switch non deve mai scattare per un errore di lettura.

        Il contatore interno viene riancorato al denaro uscito davvero, letto
        dalle esecuzioni (`_costo_reale`), e non resta appeso alla stima fatta al
        momento dell'ordine. L'ancoraggio parte dal cash che c'era *prima*
        dell'acquisto, così ripeterlo a ogni giro dà sempre lo stesso risultato
        anche dopo un round-trip in utile (il budget non è più 350€ fissi).
        """
        anomalia = False
        if position and position["quantity"] > 0:
            if not self.state.invested:
                anomalia = True
                logger.warning(
                    "Il broker ha una posizione su %s ma lo stato diceva 'in cash': la adotto.",
                    self.cfg.t212_ticker,
                )
                self.state.cash_before_buy = self.state.cash_eur
            self.state.invested = True
            self.state.quantity = position["quantity"]
            self.state.last_position_value_eur = position["current_value_eur"]
            base = self.state.cash_before_buy if self.state.cash_before_buy >= 0 else self.state.cash_eur
            self.state.cash_eur = round(max(0.0, base - self._costo_reale(position)), 2)
        elif self.state.invested:
            anomalia = True
            logger.warning(
                "Lo stato diceva 'investito' ma il broker non ha posizioni su %s: torno in cash.",
                self.cfg.t212_ticker,
            )
            # La posizione e' stata venduta fuori dal bot: il ricavo e' finito sul
            # conto e il recinto lo perderebbe di vista. Riaccredito l'ultima
            # valutazione nota: e' una stima, ma e' molto meglio di uno zero.
            if self.state.last_position_value_eur > 0:
                self.state.cash_eur = round(self.state.cash_eur + self.state.last_position_value_eur, 2)
                logger.warning(
                    "Riaccredito al capitale allocato l'ultima valutazione nota della posizione: %.2f€.",
                    self.state.last_position_value_eur,
                )
            self.state.invested = False
            self.state.quantity = 0.0
            self.state.cash_before_buy = -1.0
            self.state.last_position_value_eur = 0.0

        if not self.state.invested and self.state.pending_sell_since_utc:
            self._conferma_vendita()
        return anomalia

    def _costo_reale(self, position: dict) -> float:
        """Euro usciti per la posizione aperta, commissioni comprese.

        `totalCost` della posizione NON include la commissione di cambio: sul
        primo acquisto era 347,83€ contro 348,35€ usciti davvero. Sommo quindi il
        `netValue` delle esecuzioni dall'apertura della posizione: acquisti meno
        eventuali vendite parziali fatte a mano. Se lo storico non è leggibile
        torno a `totalCost` — sbaglia di circa lo 0,15%, non blocca il bot.
        """
        try:
            aperta_il = datetime.fromisoformat(position["created_at"].replace("Z", "+00:00"))
            fills = self.broker.get_fills(self.cfg.t212_ticker, aperta_il - MARGINE_TIMESTAMP)
        except Exception as exc:
            logger.warning("Storico esecuzioni non leggibile (%s): uso totalCost, senza commissioni.", exc)
            return position["total_cost_eur"]

        acquisti = [f for f in fills if f["side"] == "BUY"]
        if not acquisti:
            logger.warning("Nessuna esecuzione di acquisto trovata per la posizione: uso totalCost, senza commissioni.")
            return position["total_cost_eur"]
        vendite = [f for f in fills if f["side"] == "SELL"]
        costo = sum(f["net_value_eur"] for f in acquisti) - sum(f["net_value_eur"] for f in vendite)
        commissioni = sum(f["fees_eur"] for f in fills)
        logger.info("Costo reale della posizione: %.2f€ (commissioni %.2f€, totalCost T212 %.2f€).",
                    costo, commissioni, position["total_cost_eur"])
        return costo

    def _conferma_vendita(self) -> None:
        """Sostituisce l'incasso stimato dell'ultima vendita con quello eseguito.

        Al momento dell'ordine il bot conosce solo la valutazione di T212 di
        pochi secondi prima, senza commissioni. Se l'esecuzione non c'è ancora
        (ordine in coda a mercato chiuso) riprova al giro successivo.
        """
        try:
            dal = datetime.fromisoformat(self.state.pending_sell_since_utc) - MARGINE_TIMESTAMP
            vendite = [f for f in self.broker.get_fills(self.cfg.t212_ticker, dal) if f["side"] == "SELL"]
        except Exception as exc:
            logger.warning("Non riesco a confermare l'incasso dell'ultima vendita (%s): riprovo al prossimo giro.", exc)
            return
        if not vendite:
            logger.info("Vendita non ancora eseguita secondo lo storico: riprovo al prossimo giro.")
            return
        reale = sum(f["net_value_eur"] for f in vendite)
        commissioni = sum(f["fees_eur"] for f in vendite)
        scarto = reale - self.state.pending_sell_estimate_eur
        self.state.cash_eur = round(max(0.0, self.state.cash_eur + scarto), 2)
        logger.info(
            "Vendita confermata: incasso %.2f€ (stimato %.2f€, commissioni %.2f€): cash corretto di %+.2f€ a %.2f€.",
            reale, self.state.pending_sell_estimate_eur, commissioni, scarto, self.state.cash_eur,
        )
        self.state.pending_sell_estimate_eur = 0.0
        self.state.pending_sell_since_utc = ""

    def _equity(self, position: Optional[dict]) -> float:
        """Capitale allocato + valore corrente della posizione, in euro. Il
        valore lo dà T212 già convertito nella valuta del conto: nessuna
        conversione fatta da noi, nessun errore di cambio nel kill-switch."""
        valore_posizione = position["current_value_eur"] if position else 0.0
        return round(self.state.cash_eur + valore_posizione, 2)

    def _buy(self, signal: Signal, dry_run: bool) -> str:
        price = self.price_source.price_eur()
        if not price or price <= 0:
            self._record_error("Prezzo dell'ETF non disponibile: acquisto rimandato.")
            return "errore-prezzo"

        investibile = self.state.cash_eur * (1 - self.cfg.slippage_buffer)
        if investibile < self.cfg.min_order_eur:
            logger.warning("Capitale disponibile %.2f€ sotto il minimo d'ordine: niente acquisto.",
                           self.state.cash_eur)
            return "capitale-insufficiente"

        quantity = math.floor((investibile / price) * 1e5) / 1e5
        if quantity <= 0:
            logger.warning("Quantità calcolata nulla (prezzo %.2f€, disponibile %.2f€).", price, investibile)
            return "quantita-nulla"

        logger.info("ACQUISTO %s: %.5f quote a ~%.2f€ (~%.2f€ dei %.2f€ allocati).",
                    self.cfg.t212_ticker, quantity, price, quantity * price, self.state.cash_eur)
        if dry_run:
            self._log_trade("BUY-DRY", quantity, price, signal, "dry-run, nessun ordine inviato")
            return "acquisto-simulato"

        try:
            result = self.broker.place_market_order(self.cfg.t212_ticker, quantity)
        except Exception as exc:
            self._record_error(f"Invio ordine di acquisto fallito: {exc}")
            return "errore-ordine"
        if not result.get("ok"):
            self._record_error(f"Ordine di acquisto rifiutato: {result.get('error')}")
            return "ordine-rifiutato"

        eseguita = float(result.get("quantity", quantity))
        self.state.ticker = self.cfg.t212_ticker
        self.state.cash_before_buy = self.state.cash_eur
        self.state.invested = True
        self.state.quantity = eseguita
        # Stima: il costo esatto in euro lo rileggiamo da T212 al prossimo giro
        # (`_reconcile`), quando la posizione risulta aperta.
        self.state.cash_eur = round(max(0.0, self.state.cash_eur - eseguita * price), 2)
        self.state.last_action_date = datetime.now(ROME).date().isoformat()
        self._log_trade("BUY", eseguita, price, signal)
        self.notifier.send(
            f"🟢 Bot Fase 4 — ACQUISTO\n"
            f"{eseguita:.5f} quote di {self.cfg.t212_ticker} a ~{price:.2f}€ (~{eseguita * price:.2f}€)\n"
            f"Segnale: {self.cfg.yf_signal} {signal.close:.2f} sopra la SMA-{self.cfg.sma_window} "
            f"{signal.sma:.2f} (chiusura {signal.date.date()})"
        )
        return "acquisto-eseguito"

    def _sell(self, signal: Signal, position: Optional[dict], dry_run: bool) -> str:
        if not position or position["quantity_sellable"] <= 0:
            logger.warning("Vendita richiesta ma non c'è quantità vendibile: torno in cash nello stato.")
            self.state.invested = False
            self.state.quantity = 0.0
            return "niente-da-vendere"

        quantity = position["quantity_sellable"]
        valore = position["current_value_eur"]
        prezzo_eur = valore / quantity if quantity else 0.0

        logger.info("VENDITA %s: %.5f quote, valore corrente %.2f€.", self.cfg.t212_ticker, quantity, valore)
        if dry_run:
            self._log_trade("SELL-DRY", quantity, prezzo_eur, signal, "dry-run, nessun ordine inviato")
            return "vendita-simulata"

        inviata_il = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            result = self.broker.place_market_order(self.cfg.t212_ticker, -quantity)
        except Exception as exc:
            self._record_error(f"Invio ordine di vendita fallito: {exc}")
            return "errore-ordine"
        if not result.get("ok"):
            self._record_error(f"Ordine di vendita rifiutato: {result.get('error')}")
            return "ordine-rifiutato"

        # Il ricavo esatto dipende dal prezzo di esecuzione e dalle commissioni,
        # che non conosciamo nell'istante dell'ordine: accredito la valutazione
        # di T212 di pochi secondi prima e la correggo al giro successivo con
        # l'incasso eseguito (`_conferma_vendita`).
        self.state.cash_eur = round(self.state.cash_eur + valore, 2)
        self.state.pending_sell_estimate_eur = valore
        self.state.pending_sell_since_utc = inviata_il
        self.state.invested = False
        self.state.quantity = 0.0
        self.state.cash_before_buy = -1.0
        self.state.last_action_date = datetime.now(ROME).date().isoformat()
        self._log_trade("SELL", quantity, prezzo_eur, signal, "ricavo stimato sulla valutazione T212")
        self.notifier.send(
            f"🔴 Bot Fase 4 — VENDITA\n"
            f"{quantity:.5f} quote di {self.cfg.t212_ticker} per ~{valore:.2f}€\n"
            f"Segnale: {self.cfg.yf_signal} {signal.close:.2f} sotto la SMA-{self.cfg.sma_window} "
            f"{signal.sma:.2f} (chiusura {signal.date.date()})\n"
            f"Capitale allocato ora in cash: {self.state.cash_eur:.2f}€"
        )
        return "vendita-eseguita"

    # ------------------------------------------------------------- operazioni
    def resume(self) -> None:
        """Riattiva il bot dopo un kill-switch, riportando il picco al valore
        attuale: altrimenti ripartirebbe già in drawdown e si fermerebbe subito."""
        self.state = State.load(self.state_path, self.cfg.budget_eur)
        if not self.state.killed:
            logger.info("Il kill-switch non è attivo: niente da riattivare.")
            return
        try:
            position = self.broker.get_position(self.cfg.t212_ticker)
        except Exception as exc:
            logger.error("Non riesco a leggere la posizione per riancorare il picco: %s", exc)
            return
        self._reconcile(position)
        equity = self._equity(position)
        motivo = self.state.kill_reason
        self.state.killed = False
        self.state.kill_reason = ""
        self.state.peak_equity_eur = equity
        self.state.save(self.state_path)
        logger.info("Kill-switch disattivato (era: %s). Nuovo picco di riferimento: %.2f€.", motivo, equity)
        self.notifier.send(f"✅ Bot Fase 4 riattivato manualmente. Nuovo picco di riferimento: {equity:.2f}€.")

    def status(self) -> str:
        righe = [
            f"ticker: {self.cfg.t212_ticker} | segnale: {self.cfg.yf_signal} SMA-{self.cfg.sma_window}",
            f"budget: {self.cfg.budget_eur:.2f}€ | kill-switch: -{self.cfg.kill_switch_dd * 100:.0f}% dal picco",
            f"stato: {'INVESTITO' if self.state.invested else 'IN CASH'} | quantità: {self.state.quantity:.5f}",
            f"cash allocato: {self.state.cash_eur:.2f}€ | picco equity: {self.state.peak_equity_eur:.2f}€",
            f"kill-switch: {'ATTIVO — ' + self.state.kill_reason if self.state.killed else 'non attivo'}",
            f"ultimo segnale: {self.state.last_signal_date or '—'} | ultima azione: {self.state.last_action_date or '—'}",
            f"errori consecutivi: {self.state.consecutive_errors} {('(' + self.state.last_error + ')') if self.state.last_error else ''}",
        ]
        return "\n".join(righe)


# --------------------------------------------------------------------------- #
# Avvio
# --------------------------------------------------------------------------- #
def _giorno_feriale(now: Optional[datetime] = None) -> bool:
    return (now or datetime.now(ROME)).weekday() < 5


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot Fase 4 — paper trading sma_underlying_200.")
    parser.add_argument("--once", action="store_true", help="esegue un solo ciclo e esce")
    parser.add_argument("--dry-run", action="store_true", help="calcola tutto ma non invia ordini")
    parser.add_argument("--resume", action="store_true", help="riattiva il bot dopo un kill-switch")
    parser.add_argument("--status", action="store_true", help="stampa lo stato interno e esce")
    args = parser.parse_args()

    cfg = Config.from_env()
    if not cfg.api_key:
        logger.error("T212_API_KEY non configurata: esco.")
        raise SystemExit(1)

    bot = Fase4Bot(cfg)

    if args.status:
        print(bot.status())
        return
    if args.resume:
        bot.resume()
        return
    if args.once:
        esito = bot.run_once(dry_run=args.dry_run)
        logger.info("Esito del ciclo: %s", esito)
        return

    def ciclo_giornaliero() -> None:
        if not _giorno_feriale():
            logger.info("Weekend: nessuna valutazione.")
            return
        bot.run_once(dry_run=args.dry_run)

    logger.info(
        "Bot Fase 4 avviato: %s su segnale %s SMA-%s, budget %.2f€, esecuzione ogni giorno alle %s (ora italiana).",
        cfg.t212_ticker, cfg.yf_signal, cfg.sma_window, cfg.budget_eur, cfg.run_at,
    )
    logger.info("Stato all'avvio:\n%s", bot.status())
    schedule.every().day.at(cfg.run_at).do(ciclo_giornaliero)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
