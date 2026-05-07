# Istruzioni Setup iMessage Bot (da zero, per chi non ha mai usato terminale)

Guida completa per configurare e lanciare il bot su un Mac che non ha **niente** installato. Segui le fasi in ordine. Copia-incolla i comandi senza modificarli (tranne dove indicato esplicitamente con `TUO_NUMERO` o simili).

Numero mittente di riferimento in questa guida: `+19172870380`. Se cambia, sostituiscilo ovunque appare.

---

## Fase 0 — Verifica iMessage attivo

Prima di toccare il terminale, controlla che Messages.app sia configurato col numero mittente.

1. Apri **Messages.app** (Spotlight: `⌘ + Space` → digita `Messages` → Invio).
2. Dal menu in alto: **Messages** → **Settings...** (`⌘ + ,`).
3. Vai sul tab **iMessage**.
4. Verifica che l'Apple ID corretto sia loggato. Se serve login: inserisci Apple ID + password + codice 2FA che arriva su iPhone.
5. Sezione **You can be reached for messages at**: spunta `+1 (917) 287-0380`.
6. Sezione **Start new conversations from**: dal dropdown seleziona `+1 (917) 287-0380`.
7. **Messages in iCloud**: lascia OFF (non serve sincronizzare lo storico).
8. Chiudi la finestra.

Se il numero non compare nella lista "You can be reached at": l'Apple ID non ha quel numero associato. Vai su iPhone con quel numero → Settings → Messages → Send & Receive → aggiungi lo stesso Apple ID. Aspetta 1 minuto, ricontrolla sul Mac.

---

## Fase 1 — Apri Terminale

Spotlight (`⌘ + Space`) → digita `Terminal` → Invio.

Si apre una finestra. Da qui in poi tutti i comandi vanno copiati e incollati lì dentro, premendo **Invio** dopo ogni blocco.

---

## Fase 2 — Installa strumenti base (Xcode Command Line Tools)

Questo installa `git` e `python3`. Comando:

```bash
xcode-select --install
```

Compare un popup macOS → click su **Install** → accetta la licenza → aspetta 5-15 minuti (mostra una progress bar).

Quando finisce, verifica con:

```bash
git --version
python3 --version
```

Output atteso: qualcosa come `git version 2.x.x` e `Python 3.9.x` (o superiore). Se uno dei due dà errore "command not found", ripeti `xcode-select --install`.

---

## Fase 3 — Clona il repository

```bash
cd ~
git clone https://github.com/Leonardo-Corte/imessage-bot.git
cd imessage-bot
```

Se il repo è privato, git chiede credenziali GitHub. Tre alternative:

**A. Repo pubblico temporaneo (più semplice):** chi possiede il repo lo rende pubblico per 10 minuti su `github.com → repo → Settings → Change visibility → Public`. Cloni, poi torna privato.

**B. Personal Access Token GitHub:** quando git chiede password, incolla un token generato su `github.com → Settings → Developer settings → Personal access tokens → generate token (classic)` con permesso `repo`.

**C. AirDrop / chiavetta USB:** chi ha già il repo zippa la cartella `imessage-bot` (escludendo `.venv` se presente), la passa via AirDrop. Sul Mac di destinazione: scompatta in `~/imessage-bot`. Salta il `git clone` e fai solo `cd ~/imessage-bot`.

---

## Fase 4 — Setup ambiente Python

```bash
cd ~/imessage-bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Aspetta circa 1-2 minuti. Output finale deve contenere `Successfully installed ...`.

**Importante:** il prefisso `(.venv)` deve apparire all'inizio del prompt del terminale. Se chiudi il terminale e lo riapri, devi rifare:

```bash
cd ~/imessage-bot
source .venv/bin/activate
```

prima di lanciare qualsiasi comando del bot.

Se `pip` dà errore `command not found`:

```bash
python3 -m ensurepip --upgrade
python3 -m pip install -r requirements.txt
```

---

## Fase 5 — Permesso Full Disk Access (CRITICO)

Il bot legge `~/Library/Messages/chat.db` per rilevare lingua dei contatti. macOS blocca questo accesso di default.

1. Apri **System Settings** (mela Apple in alto a sinistra → System Settings).
2. Nella sidebar: **Privacy & Security**.
3. Scrolla fino a **Full Disk Access**.
4. Click sul pulsante `+` (potrebbe chiedere la password del Mac).
5. Si apre una finestra Finder. Premi `⌘ + Shift + G`, digita `/System/Applications/Utilities/`, premi Invio.
6. Seleziona **Terminal.app** → click **Open**.
7. Verifica che il toggle accanto a Terminal sia **ON** (verde).
8. **Chiudi completamente Terminale** con `⌘ + Q` (non basta chiudere la finestra).
9. Riapri Terminale.

Senza questo passo, lo smoke test fallirà con errore di permessi.

---

## Fase 6 — Riapri ambiente bot

Dopo aver riavviato Terminale:

```bash
cd ~/imessage-bot
source .venv/bin/activate
```

---

## Fase 7 — Verifica numero mittente disponibile

```bash
python list_senders.py
```

Output deve contenere una riga tipo:

```
iMessage;-;+19172870380
```

Se il numero non appare:
- Aspetta 30 secondi e riprova (Apple impiega tempo a registrare i device).
- Verifica di nuovo Fase 0 (Messages.app → Settings → iMessage → numero spuntato).
- Riavvia Mac se necessario.

---

## Fase 8 — Configura mittente di default

Apri il file di config con un editor da terminale:

```bash
nano config.yaml
```

Cerca la riga:

```
from_id: ""
```

Cambiala in:

```
from_id: "iMessage;-;+19172870380"
```

Salva: `Ctrl + O` → Invio → `Ctrl + X`.

Verifica:

```bash
grep from_id config.yaml
```

Deve stampare: `from_id: "iMessage;-;+19172870380"`.

---

## Fase 9 — Smoke test (PROVA OBBLIGATORIA)

Manda un messaggio reale al **tuo numero personale** (sostituisci `+39TUONUMERO` col tuo numero italiano completo di prefisso).

```bash
python smoke_test.py +39TUONUMERO --from "iMessage;-;+19172870380"
```

Al primo invio macOS mostra un popup: **"Terminal vuole controllare Messages"** → click **OK**.

Aspetta 30 secondi. Controlla il tuo iPhone:

- Il messaggio è arrivato?
- Il mittente è `+1 917 287 0380` (NON il numero del Mac)?

Se entrambe sì: setup OK, prosegui.

Se il messaggio non arriva o arriva da un altro mittente:
- Verifica che `Start new conversations from` in Messages.app sia impostato sul numero giusto (Fase 0).
- Verifica che `python list_senders.py` mostri il numero corretto.
- Riprova il comando smoke_test.

---

## Fase 10 — Scansione rubrica e generazione lista

```bash
python scan.py
```

Al primo lancio macOS chiede accesso ai **Contatti** → click **OK**.

Lo script applica il filtro keywords da `config.yaml` (di default: NY, NYC, New York, ecc.) e genera il file `output/preview.csv`.

Output finale stampa quanti contatti sono stati selezionati.

---

## Fase 11 — Review della lista (CSV)

Apri il file `output/preview.csv` con Numbers o Excel:

```bash
open output/preview.csv
```

Colonne principali:
- `name`, `last_name`, `phone` — identità contatto
- `language` — lingua rilevata (it/en)
- `skip_reason` — vuoto = verrà inviato; riempi con qualsiasi testo per **escludere** quella riga

Per ogni contatto che NON vuoi contattare, scrivi una motivazione in `skip_reason` (es. "duplicato", "non target", "fuori lista").

Salva il CSV mantenendo formato CSV (no .xlsx, no .numbers).

---

## Fase 12 — Personalizza messaggio (opzionale)

I template di default sono in `config.yaml`:

```
templates:
  it: "Ciao {first_name}, come stai?"
  en: "Hey {first_name}, how are you?"
```

Per cambiare:

```bash
nano config.yaml
```

Modifica le stringhe (mantieni `{first_name}` per inserire il nome). Salva con `Ctrl + O`, `Ctrl + X`.

Esempio più naturale:

```
templates:
  it: "Ciao {first_name}! Quanto tempo, come va?"
  en: "Hey {first_name}! Long time no see, how's it going?"
```

---

## Fase 13 — Dry run (simulazione senza invio)

```bash
python send.py --dry-run
```

Stampa cosa farebbe (numero contatti, ordine, template scelto per ognuno) senza inviare nulla. Verifica che i numeri totali e l'ordine abbiano senso.

---

## Fase 14 — Warmup primo giorno (max 50 messaggi)

```bash
python send.py --warmup
```

Inizia l'invio reale con cap di 50 messaggi (invece dei 80 standard). Delay automatico di 8-20 secondi tra un messaggio e l'altro. Solo orario business 9-21.

**Monitora i primi 5-10 invii:**
- Apri Messages.app sul Mac → controlla che le conversazioni partano davvero.
- Chiedi a 2-3 destinatari di confermare ricezione (AppleScript a volte ritorna successo anche senza consegna effettiva).

Se qualcosa va male, ferma con `Ctrl + C`.

Lo script è **riprendibile**: i contatti già contattati vengono salvati in `output/sent.json` e saltati ai run successivi.

---

## Fase 15 — Giorni successivi (cap 80)

```bash
python send.py
```

Riprende da dove ha lasciato. Salta automaticamente quelli già in `sent.json`.

---

## Comandi utili extra

**Invio puntuale a uno o più nomi specifici:**
```bash
python send_to.py "Testo del messaggio" Nome1 "Nome Due"
python send_to.py --dry-run "Testo" Mazza
```

**Verifica account mittenti disponibili:**
```bash
python list_senders.py
```

**Riavvia ambiente in nuova sessione terminale:**
```bash
cd ~/imessage-bot
source .venv/bin/activate
```

---

## Troubleshooting

**Errore: `Operation not permitted` o `permission denied` su chat.db**
→ Full Disk Access non attivo. Ripeti Fase 5 e riavvia Terminale completamente con `⌘ + Q`.

**`python list_senders.py` non mostra il numero**
→ Messages.app non ha il numero abilitato. Ripeti Fase 0. Aspetta 1-2 minuti dopo aver spuntato il numero (Apple sincronizza lentamente).

**Smoke test invia da numero sbagliato**
→ `Start new conversations from` in Messages Settings non punta a `+19172870380`. Cambialo. Oppure il flag `--from` è scritto male: deve essere esattamente `iMessage;-;+19172870380`.

**`pip install` fallisce su `pyobjc-framework-Contacts`**
→ Xcode Command Line Tools incompleti. Esegui di nuovo `xcode-select --install` e accetta licenza. Poi:
```bash
sudo xcodebuild -license accept
pip install -r requirements.txt
```

**Errore `unable to find Messages` o popup "non è permesso controllare Messages"**
→ Permesso Automation non concesso. Vai su System Settings → Privacy & Security → Automation → trova Terminal nella lista → spunta Messages.

**Voglio fermare campagna in corso**
→ `Ctrl + C` nel terminale dove gira `send.py`. Si interrompe pulito. Rilancia quando vuoi: riprende dove si era fermato.

**Voglio rifare la scan da zero**
→ Cancella `output/preview.csv` e rilancia `python scan.py`. Il file `sent.json` conserva la storia degli invii — non cancellarlo se vuoi mantenere idempotenza.

**Reset completo invii (PERICOLOSO: rimanderà a tutti)**
→ Cancella `output/sent.json`. Solo se vuoi ripartire da zero davvero.

---

## Cleanup finale (dopo campagna)

Se hai usato un Apple ID diverso dal tuo, ricordati di fare logout:

1. Messages.app → Settings → iMessage → **Sign Out**.
2. Sign In con il tuo Apple ID normale.

Per chiudere l'ambiente bot in un terminale:

```bash
deactivate
```

---

## Note importanti

- AppleScript ritorna successo anche se Apple poi blocca/spamma il messaggio. Verifica sempre con campioni umani prima di scalare.
- Cap giornalieri (80) e orari (30/h) sono studiati per evitare profili spam Apple. NON alzarli.
- `safety.skip_cold_contacts: true` salta i contatti senza storico iMessage. Se molti contatti vengono saltati, è normale (non hai mai chattato con loro prima).
- Il flag `--from` non "spoofa" il numero: seleziona solo tra account già loggati su Messages.app. Senza login del numero corrispondente, non funziona.
