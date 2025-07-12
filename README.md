# 🌍 GeoIP-MAXLON

**GeoIP-MAXLON** è un servizio ad alte prestazioni progettato per fornire **lookup quasi istantanei di indirizzi IP** in locale senza neccessità di connesione a internet grazie a  vari db pubblici come il DB ip.guide, il quale contiene informazioni geografiche e di rete come il **blocco CIDR**, il **numero di Sistema Autonomo (ASN)**, l'**organizzazione** e il **paese**.

La sua architettura è ottimizzata per la velocità, caricando **tutti i dati rilevanti direttamente in RAM** per garantire risposte quasi immediate.

---

## 🚀 Caratteristiche Principali

### ⚡ Lookup In-Memory ad Alta Velocità
- Il daemon carica **l'intero dataset GeoIP nella memoria** all'avvio.
- Nessuna necessità di accesso al disco per ogni query.
- Tempi di risposta estremamente rapidi per le richieste di lookup IP.

---

## 📦 Gestione Ottimizzata dei Dati

- **Libreria Polars**:
  - Utilizzata per il caricamento efficiente e la pulizia dei dati dal file CSV di origine.

- **Struttura dati precomputata (`PrecomputedNetwork`)**:
  - Rappresenta le reti IPv4 e IPv6 in un formato binario ottimizzato per i controlli di inclusione IP basati sull’aritmetica intera.

- **Caching avanzato**:
  - Salvataggio in file `.cache` che serializza le strutture dati ottimizzate.
  - Riduce significativamente i tempi di avvio successivi se il CSV non è stato modificato.
  - Cache dedicate per le reti IPv4 e IPv6, organizzate per intervalli di ottetti/blocchi per accelerare la ricerca.
  - CIDR associati a ciascun ASN vengono memorizzati per un recupero rapido di tutte le reti sotto una specifica organizzazione.

---

# GeoIP-MAXLON - Istruzioni d'Uso

## Installazione

### 1. Clona il repository:
```bash
git clone https://github.com/MaxlonPlay/GeoIP-MAXLON.git
cd GeoIP-MAXLON
```

### 2. Installa Python 3 e pip:

#### Debian / Ubuntu:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### Arch / Manjaro:
```bash
sudo pacman -S python python-pip
```

#### Fedora:
```bash
sudo dnf install python3 python3-pip
```

#### Alpine Linux:
```bash
sudo apk add python3 py3-pip
```

### 3. Installa le dipendenze Python:
```bash
pip install -r requirements.txt
```

### 4. Configura il file `.env`:
```bash
nano .env
```
> Modifica le variabili di configurazione secondo le tue necessità.

---

## Utilizzo

Per ottenere informazioni:
```bash
./main.py
```

Per avviare in modalità server (risposta quasi immediata):
```bash
./main.py --server
```

---

## Interfaccia Web

Apri il browser e accedi a:
```
http://<il-tuo-ip>:<porta-servizio>/<ip-da-analizzare>
```
> Sostituisci `<il-tuo-ip>` con l’indirizzo IP del tuo server e `<ip-da-analizzare>` con l’IP da analizzare.

---

## Comandi disponibili

### Uso:
```
./main.py --server            🔥 Avvia daemon (resta in background e abilita Web API)
./main.py <IP>                ⚡ Query istantanea (usa daemon CLI)
./main.py --standalone <IP>   🔧 Modalità standalone (non usa il daemon, caricamento dati al avvio modalità più lenta)
./main.py --status            📊 Stato daemon
./main.py --stop              🛑 Ferma daemon
./main.py --dbupdate          🔄 Aggiorna il file networks.csv e la cache
```

### Esempi:
```
./main.py --server
./main.py 8.8.8.8
curl http://<il-tuo-ip>:<porta-servizio>/8.8.8.8
```

> 💡 Il daemon carica tutto in RAM una volta e risponde istantaneamente!



## 🔌 Interfacce Flessibili

### 🖥️ Server CLI (Command Line Interface)
- Server socket dedicato.
- Consente ai client CLI di interrogare il daemon per:
  - Lookup IP.
  - Statistiche sullo stato del servizio.

### 🌐 Web API
- Server HTTP leggero che espone un'API **RESTful**.
- Facilita l’integrazione con applicazioni o servizi web.
- Query effettuabili tramite semplici richieste `GET`:
- Per futuri aggiornamenti sto pensando una WEBGUI completa


---

## ⚙️ Modalità Operative

- **Modalità Daemon (`--server`)**:
- Avvia il servizio in background.
- Abilita sia il server CLI che la Web API.
- Gestisce il proprio PID per consentire controllo da riga di comando (start/stop/status/dbupdate).

- **Modalità Client (`<IP>`)**:
- Se il daemon è in esecuzione, agisce da client.
- Invia una query IP al server CLI del daemon e mostra i risultati.

- **Modalità Standalone (`--standalone <IP>`)**:
- Esegue un lookup IP diretto **senza interagire con il daemon**.
- I dati vengono caricati al momento della richiesta quinti tempi di avvio maggiori a seconda della dimensione del DB.
- Ideale per test o usi occasionali **senza avviare un servizio persistente**.

---

## 🧾 Informazioni Dettagliate sui Risultati

Per ogni lookup IP, il servizio restituisce:

- Usando in locale il DB ip.guide, in future versione ho intensioni di espandelo ad altri DB
- Blocco CIDR corrispondente
- ASN
- Organizzazione
- Paese
- Elenco di tutti gli altri CIDR associati a quell'ASN

---

## 📊 Monitoraggio dello Stato

Il daemon fornisce **statistiche dettagliate** tra cui:

- Tempo di uptime
- Numero totale di reti caricate (IPv4 e IPv6)
- Numero totale di ASN
- Query totali elaborate
- Query al secondo
- Tempo impiegato per il caricamento iniziale dei dati

---

## ✅ In Sintesi

**GeoIP-MAXLON** è una soluzione **robusta e performante** per esigenze di lookup GeoIP selfhosted, ideale per applicazioni che richiedono:

- Risposte ultra rapide
- Elevata disponibilità dei dati
- Flessibilità nelle modalità di utilizzo
