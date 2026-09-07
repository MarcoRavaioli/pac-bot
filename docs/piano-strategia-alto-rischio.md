# Piano: strategia ad alto rischio su Trading212

Stato: **Fase 2 eseguita (2026-09-07)** — vedi [risultato e verdetto](#risultato-fase-2--2026-09-07)
in fondo al documento. Nessuna strategia attiva ha superato le soglie fissate.

## Contesto — diagnosi del bot attuale (pac-bot)

- Gira in **demo** (`T212_API_URL=https://demo.trading212.com`), non soldi veri.
- Strategia: mean-reversion su Z-score 20gg (EQQQ/VUSA/21XH), compra sotto Z < -1.0, con
  "safety valve" oltre i 20 giorni senza trade e cash > 40€.
- Ha bruciato i 1000€ demo iniziali tra il 6 e il 20 marzo 2026 con acquisti ravvicinati
  a importi decrescenti (probabile `MAX_INVESTMENT_PCT` troppo alto in origine, ora 0.2).
- Da marzo il cash libero è fermo a 5.02€: sotto la soglia minima quasi sempre, quindi il
  bot gira ogni 6 ore ma non conclude trade utili. Ultimo trade eseguito: 17 luglio 2026.
- Bug noti: Z-Score `nan` intermittente (fetch prezzi storici fallisce a volte); un ordine
  del 1° settembre è fallito per "insufficient funds" nonostante 5.02€ liberi dichiarati.

Questo bot **non è la base da estendere**: la sua logica di sizing ha un bug di fondo e
opera su asset a bassa volatilità (ETF large-cap), l'opposto di "alto rischio". Va trattato
come riferimento/prototipo, non come punto di partenza da patchare.

## Obiettivo e vincoli posti da Marco

- Budget dedicato: **300-400€, per intero perdibile** (nessun rientro garantito).
- Precedente: 600€ bruciati in copy-trading — motivo per cui qui si vuole **evidenza
  statistica prima di rischiare soldi**, non fiducia in un sistema opaco.
- Vuole "fare qualche soldo in modo passivo": aspettativa da correggere nel processo — non
  esiste automazione che garantisca rendimento passivo; l'obiettivo realistico è un
  processo di validazione rigoroso prima di ogni euro vero.
- Nessun vincolo di asset stringente: propongo io (Claude) sulla base delle best practice,
  Marco decide/conferma i parametri finali di rischio.

## Scelta di asset — raccomandazione

Restare su **Trading212** (stessa piattaforma, stessa API già integrata, stesso bot da cui
partire) con **ETF a leva 2x/3x** su indici (Nasdaq/S&P) invece di crypto o opzioni:

- Crypto: altro exchange, altra custodia, fiscalità più complessa in Italia — complessità
  operativa aggiuntiva senza motivo per un primo esperimento.
- Opzioni/derivati: leva intrinseca + scadenze + greche — rischio non "calcolato" finché
  Marco non padroneggia il meccanismo; da valutare solo in una fase successiva, se richiesto.
- ETF a leva: restano regolati, orario di borsa definito, stessa integrazione API. Attenzione
  nota fin da subito: il ribilanciamento giornaliero causa **decadimento da leva** su mercati
  laterali/volatili — va misurato nel backtest, non ignorato.

Punto aperto: Marco può cambiare idea su questa scelta in qualunque fase — nessuna decisione
è vincolante finché non si passa a soldi veri (fase 5).

## Fase 0 — Cornice di rischio (prima di scegliere la strategia)

- Capitale totale esperimento: 300-400€, isolato dal resto del portafoglio.
- Position sizing a regola fissa e pre-decisa (es. % fissa per trade), mai discrezionale
  o calcolata "a sentimento" a runtime.
- Kill-switch automatico: oltre una soglia di drawdown (es. -25/30% del capitale allocato)
  il bot si ferma da solo e notifica — non decide di "aspettare che risalga".
- Reporting: notifica Telegram (infrastruttura già esistente per altri bot sul Pi), cadenza
  da definire con Marco (giornaliera vs settimanale — **punto aperto**).

## Fase 1 — Candidati di strategia

Testare più di una strategia in parallelo, non sceglierne una a priori:

1. **Mean-reversion evoluta**: stessa logica Z-score del bot attuale, ma con stop-loss
   vero e position sizing corretto (non il bug attuale).
2. **Momentum/trend-following** su ETF a leva — logica diversa, spesso complementare alla
   mean-reversion in regimi di mercato diversi.
3. **Baseline di controllo obbligatoria**: buy&hold sullo stesso asset, e "cash fermo" —
   se una strategia non batte queste due, si scarta a prescindere da quanto sembri
   sofisticata.

## Fase 2 — Backtest rigoroso

- Dati storici multi-anno, almeno 2015-2025, inclusi i crash reali (2020, 2022) — una
  strategia mai testata su un crollo è una scommessa, non una strategia.
- Costi reali inclusi: spread, commissioni, decadimento da leva sugli ETF a leva.
- Split out-of-sample: parametri messi a punto su una parte dei dati, validati su una
  parte mai vista — altrimenti il backtest si autoinganna (overfitting).

## Fase 3 — Soglie di accettazione (decise PRIMA di vedere i risultati)

Da fissare insieme a Marco prima di lanciare il backtest, es.:

- Sharpe minimo accettabile.
- Drawdown massimo tollerato.
- Deve battere buy&hold su almeno 3 sotto-periodi distinti (non un solo periodo fortunato).

Se una strategia non passa le soglie, si scarta — non si "aggiusta finché non torna bene".

## Fase 4 — Paper trading (demo)

- Minimo 2-3 mesi di esecuzione reale in demo (non backtest) per validare l'esecuzione
  vera: slippage, bug di integrazione (es. i `nan` e l'errore "insufficient funds" già
  visti nel bot attuale), non solo la matematica della strategia.

## Fase 5 — Live con soldi veri (300-400€)

Solo dopo Fasi 2-4 superate:

- Kill-switch attivo fin dal primo giorno.
- Sizing conservativo, anche più prudente di quanto validato in backtest, almeno all'inizio.
- Monitoraggio attivo di Marco via Telegram — non "set and forget".

## Tempistica onesta

- Fasi 2-3 (backtest): giorni.
- Fase 4 (paper trading): mesi, non settimane — è la parte che richiede pazienza reale.
- Fase 5: nessuna data fissata finché le fasi precedenti non danno evidenza solida.

## Decisioni prese

- **Cadenza notifiche**: riepilogo settimanale via Telegram + notifica immediata sugli
  eventi importanti (trade eseguito, kill-switch scattato). Niente riepilogo giornaliero.
- **Asset confermato**: ETF a leva 2x/3x su Trading212 (nessuna alternativa da valutare).

## Candidati ETF a leva (recuperati il 2026-09-07)

Chiave API rigenerata e funzionante — vedi [runbook.md](runbook.md) per la causa del
problema iniziale (non era la chiave: era il container che non rileggeva `.env`).

Interrogando `/api/v0/equity/metadata/instruments` (16095 strumenti totali su
Trading212), filtrando per ETF a leva **long** (esclusi short/inverse) su indici
azionari ampi, sono emersi 39 strumenti. Elenco completo salvato in
`data/leveraged_index_etfs.json` sul Pi (non versionato — è un dump di riferimento,
rigenerabile in qualsiasi momento con la stessa query).

**Shortlist proposta per il backtest (Fase 2)** — mi limito a S&P 500 e Nasdaq 100 a
2x/3x, i più liquidi e conosciuti, per non disperdere la fase di validazione su 39
varianti quasi equivalenti tra loro:

| Ticker | Nome | Leva | Valuta |
|---|---|---|---|
| LQQ | Amundi Nasdaq-100 Daily 2x Leveraged (Acc) | 2x | EUR |
| QQQ3 / LQQ3 | WisdomTree Nasdaq 100 3x Daily Leveraged | 3x | EUR/USD/GBX |
| DBPG / XS2D | Xtrackers S&P 500 2x Leveraged Daily Swap (Acc) | 2x | EUR/USD |
| 3USL / SPY3 | WisdomTree / Leverage Shares S&P 500 3x Daily Leveraged | 3x | EUR/USD |

Esclusi dalla shortlist ma presenti nell'elenco completo, da valutare solo in una fase
successiva se la shortlist non dà risultati soddisfacenti:

- Leva **5x** su S&P 500 e Nasdaq 100 (WisdomTree) — decadimento da leva ancora più
  marcato, rischio sproporzionato per un primo esperimento.
- Indici europei (DAX, CAC 40, FTSE 100, EURO STOXX 50) — stessa logica, ma mercati e
  orari diversi da gestire; si aggiungono complessità senza un motivo chiaro ora.

## Risultato Fase 2 (2026-09-07)

Codice e dati completi in [`../backtest/`](../backtest/), report dettagliato in
[`../backtest/report.md`](../backtest/report.md).

**Verdetto: nessuna delle due strategie attive (mean-reversion evoluta, momentum) ha
superato le soglie di Fase 3 su nessuno dei 4 ETF**, sull'out-of-sample 2020-oggi.
Per la regola fissata all'inizio ("se non passa le soglie si scarta, non si aggiusta
finché non torna bene"), non si passa alla Fase 4 con nessuna delle due così com'è.

Perché, in breve:
- Il periodo out-of-sample (2020-oggi) è dominato da un bull market fortissimo
  (2023-2025 su tutti e quattro gli asset). In un mercato che sale quasi sempre,
  qualunque strategia che stia anche solo parzialmente fuori castiga durissimo il
  rendimento totale — è un test strutturalmente sfavorevole al market timing, non
  un giudizio definitivo sul market timing in generale.
- **Buy&hold vince nettamente sul rendimento** (dal +23%/anno di XS2D al +34%/anno
  di QQQ3) ma con **drawdown tra -61% e -84%** durante il 2020/2022 — è il prezzo
  reale della leva, non un difetto della simulazione.
- **Momentum è l'unica logica che batte buy&hold**, e lo fa in modo consistente
  (100% dei casi) nel sotto-periodo 2021-2022 (bear), con drawdown molto più
  contenuti (es. QQQ3: -25% invece di -81%). Ma rinuncia a gran parte del rally
  2023-2025 restando fuori mercato per periodi prolungati, quindi perde su CAGR
  totale.
- **Mean-reversion è la più debole**: né miglior rendimento né miglior protezione,
  in pratica l'evoluzione della logica del bot originale non funziona su questa
  classe di strumenti.

**Tre strade concrete da qui, discusse con Marco:**

1. **Buy&hold puro** su uno dei 4 ETF, accettando esplicitamente drawdown fino a
   -80% come parte del rischio già concordato (300-400€ perdibili) — nessun bot
   necessario. È la scelta con il rendimento storico più alto, ma è una scommessa
   sulla continuazione del trend, non una strategia con un vantaggio dimostrato.
2. **Momentum** come compromesso: rendimento medio atteso più basso, ma drawdown
   molto più contenuti — più sensato se vedere il conto a -80% è inaccettabile a
   prescindere dall'importo in gioco.
3. **Fermarsi e non passare a Fase 4/5** con queste due strategie, e valutare se
   ha senso un nuovo giro di Fase 1 (altre logiche o altre classi di asset) prima
   di rischiare qualunque euro — anche in demo.

## Ricerca su approcci pubblici e secondo giro di backtest (2026-09-07)

Su richiesta di Marco ("come fanno le persone online a farlo"), ricerca su
strategie documentate pubblicamente per ETF a leva (non contenuti social,
letteratura/community verificabile). Tre approcci emersi e testati con la stessa
disciplina (soglie fissate prima dei risultati):

1. **SMA a 200 giorni calcolata sul sottostante non a leva** (es. indice Nasdaq
   100 pulito) invece che sull'ETF a leva stesso — investito solo quando il
   sottostante è sopra la sua media, altrimenti cash.
2. **HFEA** (Hedgefundie's Excellent Adventure, Bogleheads) — leva azionaria +
   leva obbligazionaria a lunga scadenza, ribilanciate periodicamente. Non
   esiste l'equivalente UCITS del Treasury USA usato originariamente; sostituito
   con WisdomTree Bund 10Y 3x (unico bond a leva lunga disponibile su T212).
3. **Volatility targeting** — esposizione inversamente proporzionale alla
   volatilità realizzata, invece di stare tutto dentro/fuori.

Fonti: [QuantifiedStrategies](https://www.quantifiedstrategies.com/leveraged-etf-trading-strategy/),
[Brightwork Research](https://www.brightworkresearch.com/using-letfs-combined-with-the-200-day-moving-average-trading-approach/),
[Bogleheads — HFEA](https://www.bogleheads.org/forum/viewtopic.php?t=272007),
[Optimized Portfolio — sintesi HFEA](https://www.optimizedportfolio.com/hedgefundie-adventure/),
[Conditional Volatility Targeting](https://www.tandfonline.com/doi/full/10.1080/0015198X.2020.1790853).

### Risultato

**`sma_underlying_200` è nettamente il migliore, in modo consistente su tutti e 4
gli asset**, su tre dei quattro criteri di Fase 3:

| Asset | CAGR OOS | CAGR buy&hold | Max DD OOS | Max DD buy&hold | Sharpe OOS | Sharpe buy&hold |
|---|---|---|---|---|---|---|
| LQQ | 40.2% | 29.5% | -35.2% | -61.2% | 1.19 | 0.82 |
| QQQ3 | 61.6% | 34.2% | -43.7% | -81.3% | 1.19 | 0.78 |
| XS2D | 31.3% | 22.7% | -19.4% | -59.3% | 1.24 | 0.75 |
| 3USL | 44.3% | 23.8% | -27.9% | -76.7% | 1.19 | 0.67 |

Rendimento più alto, drawdown molto più piccolo, Sharpe migliore — su ogni singolo
asset testato, senza eccezioni.

**Ma fallisce il quarto criterio** (vince in almeno 3/5 sotto-periodi): vince
sempre esattamente negli stessi due — 2020 (crash) e 2021-2022 (bear) — e perde
negli altri tre (mercati in salita sostenuta, dove stare sempre dentro vince quasi
per definizione). Il criterio conta le vittorie per sotto-periodo, non la loro
entità: qui i due successi sono così ampi (in particolare nel 2021-2022, dove
trasforma una perdita del buy&hold in un guadagno su tutti e 4 gli asset) che il
CAGR composto sull'intero OOS resta comunque più alto del buy&hold nonostante il
conteggio 2/5. **Non ho deciso da solo di ignorare la soglia** — è il tipo di
aggiustamento a posteriori che la Fase 3 doveva impedire — ma la ragione del
fallimento è specifica e comprensibile, non un fallimento generico della logica.

**HFEA fallisce su tutti gli asset e criteri** — coerente con la lacuna nota
trovata in ricerca: nel 2022 la decorrelazione azioni/obbligazioni su cui si basa
si è rotta, ed è esattamente dentro la nostra finestra di test.

**Vol target non emerge**: né vantaggio di rendimento né di rischio consistente
rispetto al buy&hold.

Dettaglio completo in [`../backtest/report.md`](../backtest/report.md).

### Decisione da prendere con Marco

`sma_underlying_200` è l'unico candidato con un vantaggio grande e consistente su
rendimento, drawdown e Sharpe — ma tecnicamente non supera l'ultima soglia fissata
in anticipo. Da decidere: si considera comunque superata la Fase 3 per questo
motivo specifico (spiegato sopra, non un aggiustamento arbitrario), oppure si
tratta il fallimento come definitivo e si passa a un altro giro di ricerca?
