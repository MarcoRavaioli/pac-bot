# Piano: strategia ad alto rischio su Trading212

Stato: **bozza da validare**, nessuna fase eseguita al momento della stesura (2026-09-05).

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

## Punti aperti da chiudere con Marco

- Cadenza di monitoraggio/notifiche (giornaliera vs settimanale via Telegram).
- Conferma definitiva su ETF a leva come asset, o valutare un'alternativa prima di iniziare
  il backtest.
- Elenco esatto degli ETF a leva disponibili su Trading212 da includere come candidati.
