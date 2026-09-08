# Piano Fase 4 — Paper trading di sma_underlying_200 su XS2D

Stato: bozza da approvare, nessun codice scritto.

## Obiettivo

Eseguire in demo, su Trading212, la strategia `sma_underlying_200` (investito in
XS2D solo quando l'S&P 500 è sopra la sua media mobile a 200 giorni) per un
periodo di mesi, per validare l'**esecuzione reale** — non la matematica, già
validata in Fase 2/3 — prima di considerare soldi veri (Fase 5).

## Criteri di successo/stop, fissati ORA (stessa disciplina di Fase 3)

Da controllare ogni settimana, non a sensazione:

- **Nessun bug di esecuzione ripetuto**: un errore isolato (rete, rate limit) è
  normale; lo stesso errore che si ripete per più di 2 cicli consecutivi è uno
  STOP e si indaga prima di andare avanti.
- **Il segnale calcolato dal bot deve combaciare con un calcolo indipendente**
  (verifica manuale mensile: ricalcolo a mano se S&P 500 è sopra/sotto la SMA-200
  quel giorno, confronto col log del bot).
- **Il kill-switch non deve mai scattare per un bug** (es. lettura sbagliata del
  saldo) — se scatta, verifica se il motivo è un vero drawdown o un errore.
- **Nessun criterio di "deve guadagnare X"**: la Fase 4 valida l'esecuzione, non
  il rendimento — quello lo ha già validato la Fase 2/3 nei limiti di un backtest.

Se dopo 2-3 mesi l'esecuzione è pulita e il segnale combacia sempre, si passa a
discutere la Fase 5. Se emergono bug ripetuti, si fermano e si correggono prima
di allungare il periodo di prova, non si passa avanti "tanto funziona quasi".

## Cosa riusare del bot esistente, cosa si riscrive

Ho riletto `main.py` del pac-bot attuale. Riusabile:

- `Trading212Broker.get_headers/get_free_cash/resolve_tickers/get_portfolio`:
  autenticazione e lettura dati già funzionanti, nessun motivo di riscriverli.
- `execute_market_order`: invio ordine generico, funziona già per un acquisto;
  riusabile anche per la vendita passando una quantità negativa (è la
  convenzione dell'API T212, vedi `api.yaml`), nessuna modifica necessaria alla
  funzione stessa.
- Struttura del loop (`schedule`, log su file, lettura `.env`): riusabile.

**Da scrivere da zero** — ho verificato che non esiste già:

- **La vendita non è mai stata implementata davvero.** `check_take_profits` la
  *logga* come opportunità ma il commento nel codice dice esplicitamente che la
  vendita vera va ancora scritta. Per `sma_underlying_200` la vendita è il cuore
  della strategia (deve uscire quando il segnale si spegne) — va scritta.
- **Tutta la logica di sizing e di decisione**: quella attuale (allocazione
  dinamica su `free_cash`, conviction multi-asset, safety valve) è esattamente
  il pattern che ha causato il bug diagnosticato all'inizio di questo progetto.
  Va sostituita, non adattata.
- **Il fetch del segnale sull'indice sottostante** (S&P 500): il bot attuale
  legge solo i prezzi degli asset che vuole comprare, mai un sottostante esterno
  per un segnale.
- **Il kill-switch**: non esiste nulla di simile oggi.
- **L'invio Telegram**: non presente nel pac-bot; da collegare al bot Telegram
  già configurato sul Pi (altri progetti usano `TELEGRAM_BOT_TOKEN`).

## Decisioni di design — la mia raccomandazione su ognuna

### 1. Da dove arriva il prezzo dell'S&P 500 per il segnale?

**Raccomando: VUSA** (Vanguard S&P 500 UCITS ETF, non a leva), letto dalla
stessa API Trading212 già in uso — non l'indice ^GSPC via Yahoo Finance usato nel
backtest.

- Vantaggio: un'unica fonte dati per tutto il bot (niente dipendenza esterna da
  Yahoo, che nei log del vecchio bot ha già dato errori di rete/DNS).
- Costo: VUSA non è identico all'indice puro (piccola differenza di tracking,
  dividendi trattati diversamente) — il segnale sarà leggermente diverso da
  quello testato in backtest, non identico. Differenza attesa minima (VUSA è un
  ETF passivo a replica fisica, tracking error tipicamente sotto lo 0.1%/anno),
  ma è un'assunzione, non un fatto verificato — la verifica mensile del segnale
  (sopra) serve anche a controllare che questa differenza resti trascurabile.

### 2. Quanto capitale gestisce il bot?

**Raccomando: budget nozionale fisso** (es. 350€, a scelta di Marco dentro il
range 300-400€ già deciso), non una percentuale del saldo demo disponibile.

- Motivo: il saldo demo attuale (~5000€, dopo un reset non richiesto) non
  rispecchia l'importo reale che Marco è disposto a rischiare. Se il bot investe
  "una % del saldo demo", la Fase 4 valida l'esecuzione a una scala diversa da
  quella reale — taglie di ordine diverse possono comportarsi diversamente
  (arrotondamenti, importo minimo per operazione).
- Il bot terrà un contatore interno ("capitale allocato residuo") invece di
  guardare `free_cash` per decidere quanto investire — esattamente l'inverso
  del bug originale.

### 3. Con che frequenza gira il bot?

**Raccomando: una volta al giorno, dopo la chiusura del mercato USA** (il
segnale usa chiusure giornaliere, calcolarlo più spesso non aggiunge
informazione, aggiunge solo chiamate API e superficie di bug). Il bot attuale
gira ogni 6 ore senza motivo legato alla logica.

### 4. Come funziona esattamente il kill-switch?

**Raccomando**: tracciare il picco storico del valore della posizione dedicata
(capitale allocato + P&L). Se il valore scende oltre il 30% sotto quel picco,
il bot si ferma (non vende necessariamial, si ferma dal fare altre azioni) e
manda un messaggio Telegram che richiede conferma manuale per far ripartire.
30% è una proposta, non ho un modo oggettivo di calcolarla dal backtest — è una
soglia di sicurezza operativa, da discutere.

### 5. Si sostituisce il bot attuale o se ne crea uno nuovo?

**Raccomando: si sostituisce.** Stesso container/credenziali (già funzionanti),
nuova logica. Far girare due bot sullo stesso conto demo contemporaneamente
farebbe scontrare le loro operazioni sullo stesso saldo, rendendo entrambi i
test inaffidabili. Il vecchio codice non va perso: resta nella storia git.

## Aspetti operativi

- **Telegram**: uso l'API HTTP di Telegram direttamente (`requests.post` verso
  `api.telegram.org`), non la libreria più pesante già usata da corrispettiviBot
  (quella gestisce messaggi in entrata, a noi serve solo mandarli). Serve solo
  il token del bot (già esistente) e l'ID della chat di Marco — se non è già
  salvato da qualche parte sul Pi, va recuperato una volta (istruzioni nel
  runbook, non lo faccio io: richiede che Marco scriva al bot per ottenere il
  suo chat ID).
- **Git**: nuovo branch dedicato (`feature/fase4-paper-trading`), PR quando il
  codice è pronto e testato.
- **Nessuna azione richiesta a Marco su dashboard esterne** per questa fase —
  le credenziali T212 demo sono già configurate e funzionanti.

## Timeline

- Scrittura e test locale: qualche giorno.
- Deploy e primo avvio: quando il codice è pronto.
- Paper trading attivo: minimo 2-3 mesi, con verifica manuale mensile del
  segnale e controllo settimanale delle notifiche.
- Nessuna data per la Fase 5: si decide solo dopo aver visto l'esecuzione reale
  per un periodo sufficiente.

## Decisioni finali (2026-09-08)

1. **Budget**: 350€.
2. **Kill-switch**: -30% dal picco.
3. **Telegram**: bot e chat ID già disponibili da Marco, credenziali salvate nel
   `.env` del Pi (non nel repo). Verificate con un messaggio di prova.
