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
