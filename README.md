# pac-bot — Trading212, Fase 4 (paper trading)

Bot di trading su Trading212 che esegue una sola strategia, `sma_underlying_200`,
su un ETF a leva, in **conto demo**. Gira su Raspberry Pi (ARM64) dentro Docker.

La regola in una riga: **investito nell'ETF a leva finché l'S&P 500 chiude sopra
la sua media mobile a 200 giorni; tutto in cash quando chiude sotto.**

Il percorso che ha portato a questa strategia (diagnosi del bot precedente,
backtest su 4 ETF a leva, criteri di scelta) è in
[docs/piano-strategia-alto-rischio.md](docs/piano-strategia-alto-rischio.md); il
piano operativo di questa fase è in
[docs/fase4-paper-trading.md](docs/fase4-paper-trading.md).

## Come funziona

| | |
|---|---|
| Asset comprato | XS2D — Xtrackers S&P 500 2x Leveraged (`XS2Dl_EQ` su Trading212) |
| Segnale | chiusura dell'S&P 500 (`^GSPC`, Yahoo Finance) contro la sua SMA-200 |
| Capitale | budget fisso di 350€, tracciato da un contatore interno, **non** dal saldo del conto |
| Frequenza | una volta al giorno, alle 09:05 ora italiana, nei giorni feriali |
| Kill-switch | il bot si ferma se l'equity scende oltre il 30% sotto il picco |
| Notifiche | Telegram su acquisto, vendita, kill-switch, dati mancanti, errori ripetuti |

Perché il segnale viene da Yahoo e non da Trading212: **l'API di Trading212 non
espone prezzi storici** — non esiste alcun endpoint di candele, il metadata degli
strumenti non contiene prezzi e `currentPrice` compare solo dentro una posizione
già aperta. Per una media a 200 giorni non è una fonte possibile. Lo storico
scaricato viene tenuto in cache su disco: se Yahoo non risponde il segnale resta
calcolabile, e se la cache invecchia oltre `MAX_SIGNAL_STALENESS_DAYS` il bot
smette di operare e avvisa su Telegram invece di decidere su prezzi vecchi.

Perché le 09:05: il backtest incassa il rendimento **dal giorno successivo** al
segnale (`position.shift(1)`). Valutare la mattina dopo la chiusura USA, a borsa
europea appena aperta, riproduce quell'ipotesi ed esegue l'ordine su un mercato
aperto, invece di lasciarlo in coda tutta la notte.

## Comandi

```bash
# ciclo singolo, senza inviare ordini: stampa segnale, sizing e decisione
python main.py --once --dry-run

# stato interno (posizione, capitale allocato, picco, kill-switch)
python main.py --status

# riattiva il bot dopo che è scattato il kill-switch
python main.py --resume

# test della logica, senza rete e senza broker
python tests/check_logic.py
```

## Setup

1. `cp .env.example .env` e compila le variabili (vedi i commenti nel file).
   Servono **sia** `T212_API_KEY` **sia** `TRADING212_ID`: l'autenticazione è
   Basic, l'header con la sola chiave risponde 401.
2. `docker compose up -d --build`
3. `docker compose logs -f`

Attenzione: dopo ogni modifica al `.env` il container va **ricreato**, non
riavviato — `docker restart` non rilegge le variabili. Il comando esatto è in
[docs/runbook.md](docs/runbook.md).

## File

- `main.py` — il bot: segnale, sizing, acquisto, vendita, kill-switch, notifiche.
- `tests/check_logic.py` — test della logica con broker e dati finti.
- `backtest/` — motore di backtest, strategie e dati storici usati per scegliere
  strategia e asset (Fase 2/3). Non serve al bot in esecuzione.
- `data/` — stato del bot (`fase4_state.json`), storico operazioni
  (`fase4_trades.csv`) e cache del segnale (`signal_cache.csv`).
