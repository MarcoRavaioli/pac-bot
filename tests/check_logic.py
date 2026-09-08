"""Test della logica di Fase 4 senza toccare rete, broker o Trading212.

Si lancia con:  .venv/bin/python tests/check_logic.py
Stampa una riga per controllo e esce con codice 1 se qualcosa fallisce.

Non copre: l'invio reale degli ordini a Trading212 e l'invio reale su Telegram —
quelli si verificano solo contro il conto demo (vedi docs/runbook.md).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import Config, Fase4Bot, Signal, SignalSource, State, ROME  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent
ESITI: list[tuple[bool, str]] = []


def check(condizione: bool, descrizione: str) -> None:
    ESITI.append((bool(condizione), descrizione))
    print(f"{'PASS' if condizione else 'FAIL'}  {descrizione}")


# --------------------------------------------------------------------------- #
# Doppioni finti delle dipendenze esterne
# --------------------------------------------------------------------------- #
class BrokerFinto:
    def __init__(self, posizione=None):
        self.posizione = posizione
        self.ordini: list[tuple[str, float]] = []
        self.errore_su_lettura = False

    def get_position(self, ticker: str):
        if self.errore_su_lettura:
            raise RuntimeError("broker irraggiungibile")
        return self.posizione

    def place_market_order(self, ticker: str, quantity: float, precision: int = 5):
        self.ordini.append((ticker, quantity))
        return {"ok": True, "quantity": round(quantity, precision)}


class SegnaleFinto:
    def __init__(self, invested: bool | None):
        self.invested = invested

    def get(self, now=None):
        if self.invested is None:
            return None
        return Signal(
            date=pd.Timestamp("2026-09-04"),
            close=7718.60,
            sma=7000.00 if self.invested else 8000.00,
            invested=self.invested,
            age_days=1,
            from_cache=False,
        )


class PrezzoFinto:
    def __init__(self, valore: float | None):
        self.valore = valore

    def price_eur(self):
        return self.valore


class NotifierFinto:
    def __init__(self):
        self.messaggi: list[str] = []
        self.enabled = True

    def send(self, text: str) -> bool:
        self.messaggi.append(text)
        return True


def posizione(quantita: float, costo: float, valore: float) -> dict:
    return {
        "quantity": quantita,
        "quantity_sellable": quantita,
        "current_price": valore / quantita if quantita else 0.0,
        "total_cost_eur": costo,
        "current_value_eur": valore,
        "unrealized_pl_eur": round(valore - costo, 2),
    }


def bot_di_prova(tmp: Path, broker, segnale, prezzo, notifier, budget: float = 350.0) -> Fase4Bot:
    cfg = Config(
        api_key="finta", api_id="finto", api_url="https://demo.trading212.com",
        t212_ticker="XS2Dl_EQ", yf_asset="XS2D.L", yf_signal="^GSPC", sma_window=200,
        budget_eur=budget, kill_switch_dd=0.30, max_staleness_days=5, run_at="09:05",
        min_order_eur=5.0, slippage_buffer=0.005, telegram_token="", telegram_chat_id="",
        data_dir=tmp,
    )
    return Fase4Bot(cfg, broker=broker, signal_source=segnale, price_source=prezzo, notifier=notifier)


# --------------------------------------------------------------------------- #
# 1. Il segnale del bot coincide con quello del backtest
# --------------------------------------------------------------------------- #
def test_segnale_uguale_al_backtest(tmp: Path) -> None:
    csv_gspc = RADICE / "backtest" / "data" / "GSPC.csv"
    if not csv_gspc.exists():
        check(False, f"dati storici del backtest non trovati in {csv_gspc}")
        return

    storico = pd.read_csv(csv_gspc, index_col=0, parse_dates=True)["Close"].astype(float).sort_index()
    cache = tmp / "signal_cache.csv"
    cache.parent.mkdir(parents=True, exist_ok=True)
    storico.to_frame("Close").to_csv(cache)

    class SenzaRete(SignalSource):
        def _download(self):  # Yahoo non raggiungibile: deve bastare la cache
            return None

    sorgente = SenzaRete("^GSPC", 200, cache, max_staleness_days=100000)
    # Il giro automatico gira la mattina DOPO l'ultima chiusura disponibile.
    giorno_dopo = storico.index[-1] + pd.Timedelta(days=1)
    segnale = sorgente.get(now=datetime(giorno_dopo.year, giorno_dopo.month, giorno_dopo.day, 9, 5, tzinfo=ROME))

    atteso_sma = float(storico.rolling(200).mean().iloc[-1])
    atteso_dentro = bool(storico.iloc[-1] > atteso_sma)

    check(segnale is not None, "segnale calcolabile dalla sola cache, senza rete")
    if segnale is None:
        return
    check(segnale.from_cache is True, "il bot segnala di aver usato la cache quando Yahoo non risponde")
    check(abs(segnale.sma - atteso_sma) < 1e-6, f"SMA-200 identica al calcolo diretto ({segnale.sma:.2f})")
    check(segnale.invested == atteso_dentro,
          f"posizione uguale al criterio del backtest (chiusura {segnale.close:.2f} vs SMA {segnale.sma:.2f} "
          f"-> {'dentro' if segnale.invested else 'fuori'})")

    # Confronto diretto con la funzione del backtest, su tutta la serie.
    sys.path.insert(0, str(RADICE / "backtest"))
    import strategies  # noqa: E402

    df_finto = pd.DataFrame({"Close": storico})  # l'ETF non serve: la posizione dipende solo dal sottostante
    posizioni_backtest = strategies.sma_underlying_200(df_finto, storico)
    check(bool(posizioni_backtest.iloc[-1] == 1.0) == segnale.invested,
          "stessa decisione della funzione sma_underlying_200 del backtest sull'ultimo giorno")


def test_dati_troppo_vecchi(tmp: Path) -> None:
    csv_gspc = RADICE / "backtest" / "data" / "GSPC.csv"
    storico = pd.read_csv(csv_gspc, index_col=0, parse_dates=True)["Close"].astype(float).sort_index()
    cache = tmp / "cache_vecchia.csv"
    storico.to_frame("Close").to_csv(cache)

    class SenzaRete(SignalSource):
        def _download(self):
            return None

    sorgente = SenzaRete("^GSPC", 200, cache, max_staleness_days=5)
    molto_dopo = datetime(2030, 1, 1, 9, 5, tzinfo=ROME)
    check(sorgente.get(now=molto_dopo) is None,
          "con dati più vecchi del limite il segnale è None (il bot non opera alla cieca)")


# --------------------------------------------------------------------------- #
# 2. Macchina a stati: compra, non ricompra, vende
# --------------------------------------------------------------------------- #
def test_barra_intraday(tmp: Path) -> None:
    """Durante la seduta USA la riga di oggi e' una quotazione, non una chiusura."""
    csv_gspc = RADICE / "backtest" / "data" / "GSPC.csv"
    storico = pd.read_csv(csv_gspc, index_col=0, parse_dates=True)["Close"].astype(float).sort_index()

    # Aggiungo una riga "di oggi" con un valore assurdo, come farebbe uno spike intraday.
    oggi = pd.Timestamp("2026-09-08")
    con_intraday = pd.concat([storico, pd.Series([1000.0], index=[oggi])])
    cache = tmp / "cache_intraday.csv"
    con_intraday.to_frame("Close").to_csv(cache)

    class SenzaRete(SignalSource):
        def _download(self):
            return None

    sorgente = SenzaRete("^GSPC", 200, cache, max_staleness_days=5)

    pomeriggio = datetime(2026, 9, 8, 16, 15, tzinfo=ROME)   # seduta USA aperta
    sig_pomeriggio = sorgente.get(now=pomeriggio)
    check(sig_pomeriggio is not None and sig_pomeriggio.date.date() != oggi.date(),
          "giro di pomeriggio: la riga di oggi viene scartata, si usa l'ultima chiusura vera")
    check(sig_pomeriggio is not None and sig_pomeriggio.close != 1000.0,
          "il valore intraday non entra nella decisione")

    sera = datetime(2026, 9, 8, 22, 30, tzinfo=ROME)          # dopo la chiusura USA
    sig_sera = sorgente.get(now=sera)
    check(sig_sera is not None and sig_sera.date.date() == oggi.date(),
          "dopo le 22:15 la riga di oggi e' una chiusura e viene usata")

    mattina = datetime(2026, 9, 9, 9, 5, tzinfo=ROME)         # il giro automatico
    sig_mattina = sorgente.get(now=mattina)
    check(sig_mattina is not None and sig_mattina.date.date() == oggi.date(),
          "il giro delle 09:05 usa la chiusura del giorno prima, senza scartare nulla")


def test_acquisto(tmp: Path) -> None:
    broker = BrokerFinto(posizione=None)
    notifier = NotifierFinto()
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(311.40), notifier)

    esito = bot.run_once()
    atteso_qty = (350.0 * 0.995) / 311.40

    check(esito == "acquisto-eseguito", "segnale sopra la media e nessuna posizione -> acquisto")
    check(len(broker.ordini) == 1 and broker.ordini[0][0] == "XS2Dl_EQ", "ordine inviato sul ticker giusto")
    check(broker.ordini[0][1] > 0, "quantità positiva = acquisto (convenzione T212)")
    check(abs(broker.ordini[0][1] - atteso_qty) < 1e-4,
          f"quantità dal budget fisso, non dal saldo del conto ({broker.ordini[0][1]:.5f} quote)")
    check(bot.state.cash_eur < 5.0, f"budget quasi tutto investito, residuo {bot.state.cash_eur:.2f}€")
    check(any("ACQUISTO" in m for m in notifier.messaggi), "notifica Telegram di acquisto")

    # Secondo giro con lo stesso segnale: il broker ora ha la posizione.
    broker.posizione = posizione(1.118, 348.0, 350.0)
    esito2 = bot.run_once()
    check(esito2 == "nessuna-azione", "secondo giro con segnale invariato: nessun nuovo ordine")
    check(len(broker.ordini) == 1, "nessun doppio acquisto")
    check(abs(bot.state.cash_eur - 2.0) < 0.01,
          f"cash riancorato al costo reale letto da T212 ({bot.state.cash_eur:.2f}€ = 350 - 348)")


def test_vendita(tmp: Path) -> None:
    broker = BrokerFinto(posizione=posizione(1.118, 348.0, 402.0))
    notifier = NotifierFinto()
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(359.57), notifier)
    bot.run_once()  # adotta la posizione esistente

    bot.signal_source = SegnaleFinto(False)  # il segnale si spegne
    esito = bot.run_once()

    check(esito == "vendita-eseguita", "segnale sotto la media con posizione aperta -> vendita")
    check(len(broker.ordini) == 1 and broker.ordini[0][1] < 0, "quantità negativa = vendita")
    check(abs(abs(broker.ordini[0][1]) - 1.118) < 1e-6, "vende tutta la quantità disponibile")
    check(bot.state.invested is False and bot.state.quantity == 0.0, "stato tornato in cash")
    check(abs(bot.state.cash_eur - 404.0) < 0.01,
          f"cash = residuo 2€ + valore posizione 402€ = {bot.state.cash_eur:.2f}€ (utile del round-trip)")
    check(any("VENDITA" in m for m in notifier.messaggi), "notifica Telegram di vendita")


def test_niente_vendita_senza_segnale_spento(tmp: Path) -> None:
    broker = BrokerFinto(posizione=posizione(1.118, 348.0, 300.0))
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(268.0), NotifierFinto())
    bot.run_once()   # primo giro: adotta la posizione trovata sul broker
    esito = bot.run_once()
    check(esito == "nessuna-azione" and not broker.ordini,
          "posizione in perdita ma segnale ancora valido: non vende (nessuno stop-loss di prezzo)")


# --------------------------------------------------------------------------- #
# 3. Kill-switch
# --------------------------------------------------------------------------- #
def test_kill_switch(tmp: Path) -> None:
    broker = BrokerFinto(posizione=posizione(1.118, 348.0, 350.0))
    notifier = NotifierFinto()
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(313.0), notifier)
    bot.run_once()
    check(abs(bot.state.peak_equity_eur - 352.0) < 0.01,
          f"picco registrato a {bot.state.peak_equity_eur:.2f}€ (cash 2 + posizione 350)")

    # -29%: sotto la soglia, non deve scattare.
    broker.posizione = posizione(1.118, 348.0, 248.0)
    esito = bot.run_once()
    check(esito == "nessuna-azione" and not bot.state.killed,
          "drawdown -29.0%: il bot continua a lavorare")

    # -31%: deve scattare.
    broker.posizione = posizione(1.118, 348.0, 240.0)
    esito = bot.run_once()
    check(esito == "kill-switch-scattato" and bot.state.killed, "drawdown oltre -30%: kill-switch attivo")
    check(not broker.ordini, "il kill-switch non vende: la posizione resta aperta, come da piano")
    check(any("KILL-SWITCH" in m for m in notifier.messaggi), "notifica Telegram del kill-switch")

    # Con il segnale spento il bot fermo non deve comunque operare.
    bot.signal_source = SegnaleFinto(False)
    esito = bot.run_once()
    check(esito == "kill-switch-attivo" and not broker.ordini, "da fermo non esegue più nessun ordine")

    # Lo stato sopravvive al riavvio del container.
    bot2 = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(313.0), NotifierFinto())
    check(bot2.state.killed, "il kill-switch resta attivo dopo un riavvio (stato su disco)")

    bot2.resume()
    check(not bot2.state.killed, "--resume riattiva il bot")
    check(abs(bot2.state.peak_equity_eur - 242.0) < 0.01,
          f"il picco riparte dall'equity attuale ({bot2.state.peak_equity_eur:.2f}€), non dal vecchio massimo")


# --------------------------------------------------------------------------- #
# 4. Riallineamento con il broker e gestione errori
# --------------------------------------------------------------------------- #
def test_riallineamento(tmp: Path) -> None:
    # Posizione aperta a mano dalla app mentre lo stato dice "in cash".
    broker = BrokerFinto(posizione=posizione(1.0, 300.0, 320.0))
    notifier = NotifierFinto()
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(320.0), notifier)
    esito = bot.run_once()
    check(esito == "riallineamento" and not broker.ordini,
          "posizione trovata sul broker: la adotta invece di comprarne un'altra")
    check(bot.state.invested and abs(bot.state.quantity - 1.0) < 1e-9, "quantita' presa dal broker")
    check(abs(bot.state.cash_eur - 50.0) < 0.01,
          f"cash allocato = budget 350 - costo reale 300 = {bot.state.cash_eur:.2f}€")
    check(abs(bot.state.peak_equity_eur - 370.0) < 0.01,
          "picco ancorato all'equity del momento dell'adozione, non al budget iniziale")
    check(any("disallineata" in m for m in notifier.messaggi), "il disallineamento viene notificato")

    # Riancoraggio idempotente: rieseguire non deve spostare il contatore.
    bot.run_once()
    check(abs(bot.state.cash_eur - 50.0) < 0.01,
          f"secondo giro: il cash resta {bot.state.cash_eur:.2f}€ (ancoraggio idempotente)")

    # Posizione chiusa a mano mentre lo stato dice "investito": e' un salto
    # contabile, non un crollo di mercato. Il kill-switch NON deve scattare.
    broker.posizione = None
    esito = bot.run_once()
    check(esito == "riallineamento" and not bot.state.killed,
          "posizione venduta a mano: nessun kill-switch su un drawdown finto")
    check(not bot.state.invested and not broker.ordini,
          "il giro del riallineamento non invia ordini: prima la notifica, poi si opera")
    check(abs(bot.state.cash_eur - 370.0) < 0.01,
          f"il ricavo stimato rientra nel capitale allocato ({bot.state.cash_eur:.2f}€), non va perso")

    # Da qui il bot puo' ricomprare normalmente al segnale successivo.
    esito = bot.run_once()
    check(esito == "acquisto-eseguito" and len(broker.ordini) == 1,
          "dopo il riallineamento il bot riprende a operare al giro dopo")


def test_errori(tmp: Path) -> None:
    notifier = NotifierFinto()
    broker = BrokerFinto(posizione=None)
    broker.errore_su_lettura = True
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(311.0), notifier)

    for _ in range(3):
        esito = bot.run_once()
    check(esito == "errore-broker" and not broker.ordini, "broker irraggiungibile: nessun ordine al buio")
    check(bot.state.consecutive_errors == 3, f"errori consecutivi contati ({bot.state.consecutive_errors})")
    check(any("cicli consecutivi in errore" in m for m in notifier.messaggi),
          "oltre 2 cicli in errore: alert Telegram, come da criteri di Fase 4")

    broker.errore_su_lettura = False
    bot.run_once()
    check(bot.state.consecutive_errors == 0, "il contatore si azzera quando torna a funzionare")


def test_segnale_assente(tmp: Path) -> None:
    notifier = NotifierFinto()
    broker = BrokerFinto(posizione=None)
    bot = bot_di_prova(tmp, broker, SegnaleFinto(None), PrezzoFinto(311.0), notifier)
    esito = bot.run_once()
    check(esito == "segnale-non-disponibile" and not broker.ordini,
          "senza segnale non si opera")
    bot.run_once()
    check(sum("segnale non disponibili" in m or "troppo vecchi" in m for m in notifier.messaggi) == 1,
          "l'alert sui dati mancanti parte una volta al giorno, non a ogni giro")


def test_prezzo_assente(tmp: Path) -> None:
    broker = BrokerFinto(posizione=None)
    bot = bot_di_prova(tmp, broker, SegnaleFinto(True), PrezzoFinto(None), NotifierFinto())
    esito = bot.run_once()
    check(esito == "errore-prezzo" and not broker.ordini, "senza prezzo non si dimensiona un ordine a caso")


# --------------------------------------------------------------------------- #
def main() -> int:
    prove = [
        test_segnale_uguale_al_backtest,
        test_dati_troppo_vecchi,
        test_barra_intraday,
        test_acquisto,
        test_vendita,
        test_niente_vendita_senza_segnale_spento,
        test_kill_switch,
        test_riallineamento,
        test_errori,
        test_segnale_assente,
        test_prezzo_assente,
    ]
    for prova in prove:
        print(f"\n--- {prova.__name__} ---")
        tmp = Path(tempfile.mkdtemp(prefix="fase4-test-"))
        try:
            prova(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    falliti = [d for ok, d in ESITI if not ok]
    print(f"\n{len(ESITI) - len(falliti)}/{len(ESITI)} controlli superati.")
    for d in falliti:
        print(f"  FALLITO: {d}")
    return 1 if falliti else 0


if __name__ == "__main__":
    raise SystemExit(main())
