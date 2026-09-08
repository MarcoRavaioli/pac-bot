# Runbook — interventi manuali richiesti

Passi che richiedono una console esterna o una credenziale e che quindi non posso
eseguire da qui. Aggiornare questo file ogni volta che se ne trova uno nuovo.

## Rigenerare la API key di Trading212 (demo)

**Quando serve**: rilevato il 2026-09-06 — l'API key attuale nel bot risponde `401
Unauthorized` su tutti gli endpoint (`/api/v0/equity/account/cash` e
`/api/v0/equity/metadata/instruments`), verificato lanciando le stesse chiamate del
bot dentro il container `t212-bot` sul Pi. L'ultima chiamata riuscita nei log risale
al 2026-09-04 23:31 (venerdì); nel weekend il bot salta la valutazione per mercato
chiuso, quindi non è chiaro se la chiave si sia invalidata nel weekend o per un
motivo lato Trading212 (i conti demo di T212 a volte si resettano periodicamente,
invalidando le chiavi). Non verificato: la causa esatta — solo il sintomo (401).

**Passi indicativi** (non verificati da me in questa sessione — non ho accesso al
tuo account Trading212; conferma/correggi la sequenza mentre la segui):

1. Apri [trading212.com](https://www.trading212.com) e fai login.
2. Passa all'account **Practice/Demo** (selettore account in alto, di solito vicino
   al saldo).
3. Vai su **Impostazioni** (icona profilo) → cerca la sezione **API (Beta)**.
4. Se esiste già una chiave, **revocala**; poi genera una **nuova API key**.
5. Copia subito la chiave: viene mostrata una sola volta.
6. Sul Pi, aggiorna il valore su una riga sola, senza aprire un editor interattivo:
   ```bash
   ssh rpi-ts "sed -i 's/^T212_API_KEY=.*/T212_API_KEY=LA_TUA_NUOVA_CHIAVE/' /home/mamo/docker-data/pac-bot/.env"
   ```
7. Riavvia il container perché rilegga il `.env`:
   ```bash
   ssh rpi-ts "docker restart t212-bot"
   ```
8. Verifica che funzioni di nuovo:
   ```bash
   ssh rpi-ts "docker logs t212-bot --tail 5"
   ```
   (il prossimo giro di log utile arriva al prossimo slot di valutazione, ogni 6 ore).

**Risolto il 2026-09-07 — causa reale diversa da quella ipotizzata sopra**: non era
la chiave scaduta lato Trading212. Il vero problema era che **`docker restart` non
rilegge `.env`** — le variabili d'ambiente vengono fissate alla creazione del
container e restano quelle anche dopo un restart. Ho aggiornato il `.env` tre volte
durante il debug e testato sempre contro la stessa chiave di maggio, ottenendo 401
in ogni caso, finché non ho confrontato l'hash delle credenziali in memoria nel
container con quelle nel file e ho trovato la discrepanza.

Per far rileggere `.env` a un container serve **ricrearlo**, non solo riavviarlo:
```bash
ssh rpi-ts "cd /home/mamo/docker-data/pac-bot && docker compose up -d --no-build --force-recreate t212_bot"
```
(`--no-build` evita un rebuild dell'immagine, che con questo progetto fallisce
comunque per un problema separato: `requirements.txt` non pinna le versioni,
`pandas-ta` non è compatibile con l'ultima `pandas` risolta al momento del build —
da sistemare separatamente se in futuro serve rifare la build da zero.)

**Vale per tutti i bot su questo Pi** che usano `env_file` in docker-compose
(corrispettivi-bot, fondo-cassa-bot, ecc.): un cambio a `.env` senza ricreare il
container non ha alcun effetto, anche se il container si riavvia senza errori.

Passi da seguire aggiornati:
1. Genera la nuova API key da Trading212 (Impostazioni → API Beta → account
   INVEST Practice) — vedi sezione sopra per i dettagli su IP restriction e
   permessi.
2. Aggiorna `.env` sul Pi con `sed` (comando sopra) o manualmente.
3. **Ricrea il container** (non `docker restart`):
   ```bash
   ssh rpi-ts "docker stop t212-bot && docker rm t212-bot && cd /home/mamo/docker-data/pac-bot && docker compose up -d --no-build t212_bot"
   ```
4. Verifica che il container nuovo abbia le credenziali giuste confrontando
   `docker inspect t212-bot --format '{{.Created}}'` con l'ora attuale, prima di
   fidarti di qualunque test di autenticazione.

---

## Fase 4 — cose che devi fare tu (aggiornato 2026-09-08)

### Allineare la chiave API sul Mac (per provare il bot in locale)

Il `.env` locale ha una chiave vecchia che risponde 401; quella buona è solo sul
Pi. Copiarla richiede un permesso che non ho, quindi il comando è tuo:

```bash
ssh rpi-ts 'grep "^T212_API_KEY=" /home/mamo/docker-data/pac-bot/.env'
```

Incolla la riga risultante al posto di `T212_API_KEY=...` nel `.env` locale.

**Come si autentica il bot** — verificato l'8/9/2026 contro il conto demo:
`Authorization: <chiave>` risponde **401**, Basic con `TRADING212_ID:T212_API_KEY`
risponde **200**. Servono quindi entrambe le variabili, non solo la chiave.

### Ripulire il conto demo prima di far partire la Fase 4

L'8/9/2026 il conto demo aveva ancora una posizione aperta dal bot vecchio:
**VUSAa_EQ, ~7.96 quote, ~1000€**, comprata la mattina stessa. Non disturba il
bot nuovo (che guarda solo il proprio ticker e il proprio contatore), ma sporca
la lettura del conto quando controlli i numeri a mano. Per chiuderla, dalla app
Trading212 sul conto Practice: posizione VUSA → **Chiudi posizione**.

### Deploy della Fase 4 sul Pi

Il codice nuovo richiede dipendenze nuove (`requirements.txt` ora è pinnato e
`pandas-ta` è stato rimosso — era la causa della build che falliva), quindi qui
il rebuild dell'immagine **serve**:

```bash
ssh rpi-ts "cd /home/mamo/docker-data/pac-bot && git pull && docker compose build t212_bot"
```

Poi aggiungi al `.env` sul Pi le variabili nuove (`T212_TICKER`, `YF_ASSET_TICKER`,
`YF_SIGNAL_TICKER`, `BUDGET_EUR`, `KILL_SWITCH_DRAWDOWN`, `RUN_AT`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) — vedi `.env.example` — e **ricrea** il
container, non riavviarlo:

```bash
ssh rpi-ts "cd /home/mamo/docker-data/pac-bot && docker compose up -d --no-build --force-recreate t212_bot"
```

Prima di lasciarlo operare, un giro a vuoto che non invia ordini:

```bash
ssh rpi-ts "docker exec t212-bot python main.py --once --dry-run"
```

### Riattivare il bot dopo il kill-switch

Quando scatta, il bot smette di operare e lascia la posizione aperta. Riparte
solo con una conferma manuale:

```bash
ssh rpi-ts "docker exec t212-bot python main.py --status"
ssh rpi-ts "docker exec t212-bot python main.py --resume"
```

`--resume` riporta il picco di riferimento all'equity attuale: senza quello il
bot ripartirebbe già in drawdown e si fermerebbe di nuovo al primo giro.

### Verifica mensile del segnale (criterio di Fase 4)

Una volta al mese, controlla a mano che il bot non stia sbagliando il segnale:

```bash
ssh rpi-ts "docker logs t212-bot --tail 50 | grep 'Segnale'"
```

La riga riporta chiusura dell'S&P 500, SMA-200 e decisione. Confrontala con un
grafico dell'S&P 500 con media a 200 giorni (per esempio su TradingView): devono
dire la stessa cosa.

### Variante EUR dello stesso ETF (da valutare per la Fase 5)

`XS2Dl_EQ` è la linea LSE dell'ETF, quotata in **USD**. Su Trading212 esiste la
stessa ISIN (LU0411078552) quotata in **EUR** su Xetra: `DBPGd_EQ`. Stesso fondo,
stessa esposizione; con un conto in euro la linea EUR evita la commissione di
cambio che T212 applica sugli strumenti in valuta diversa (0,15% per operazione
sul conto reale — irrilevante in demo, non in Fase 5). Per passare alla linea EUR
bastano due righe nel `.env`:

```
T212_TICKER=DBPGd_EQ
YF_ASSET_TICKER=DBPG.DE
```
