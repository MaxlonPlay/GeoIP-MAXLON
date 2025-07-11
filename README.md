# 🌍 GeoIP-MAXLON

**GeoIP-MAXLON** è un servizio ad alte prestazioni progettato per fornire **lookup istantanei di indirizzi IP**, associandoli a informazioni geografiche e di rete come il **blocco CIDR**, il **numero di Sistema Autonomo (ASN)**, l'**organizzazione** e il **paese**.

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
  - Utilizzata per il caricamento efficiente e la pulizia dei dati dal file CSV di origine (`networks.csv`).

- **Struttura dati precomputata (`PrecomputedNetwork`)**:
  - Rappresenta le reti IPv4 e IPv6 in un formato binario ottimizzato per i controlli di inclusione IP basati sull’aritmetica intera.

- **Caching avanzato**:
  - Salvataggio in file `.cache` che serializza le strutture dati ottimizzate.
  - Riduce significativamente i tempi di avvio successivi se il CSV non è stato modificato.
  - Cache dedicate per le reti IPv4 e IPv6, organizzate per intervalli di ottetti/blocchi per accelerare la ricerca.
  - CIDR associati a ciascun ASN vengono memorizzati per un recupero rapido di tutte le reti sotto una specifica organizzazione.

---

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


---

## ⚙️ Modalità Operative

- **Modalità Daemon (`--server`)**:
- Avvia il servizio in background.
- Abilita sia il server CLI che la Web API.
- Gestisce il proprio PID per consentire controllo da riga di comando (start/stop/status).

- **Modalità Client (`<IP>`)**:
- Se il daemon è in esecuzione, agisce da client.
- Invia una query IP al server CLI del daemon e mostra i risultati.

- **Modalità Standalone (`--standalone <IP>`)**:
- Esegue un lookup IP diretto **senza interagire con il daemon**.
- I dati vengono caricati al momento della richiesta.
- Ideale per test o usi occasionali **senza avviare un servizio persistente**.

---

## 🧾 Informazioni Dettagliate sui Risultati

Per ogni lookup IP, il servizio restituisce:

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

**GeoIP-MAXLON** è una soluzione **robusta e performante** per esigenze di lookup GeoIP, ideale per applicazioni che richiedono:

- Risposte ultra rapide
- Elevata disponibilità dei dati
- Flessibilità nelle modalità di utilizzo
