# 🌍 GeoIP-MAXLON

Un **servizio di geolocalizzazione IP** veloce e efficiente, containerizzato con Docker. Utilizza un database GeoIP per localizzare indirizzi IP e fornire informazioni geografiche.

![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## ✨ Features

- 🚀 **API Web REST** per la geolocalizzazione di indirizzi IP
- 📊 **Database GeoIP** aggiornabile automaticamente
- 🐳 **Containerizzato con Docker** per deployment facile
- 🌐 **Interfaccia Web** intuitiva per le ricerche
- ⚡ **Performante** grazie a Polars per la gestione dati
- 🔄 **Auto-updater** del database GeoIP

## 🚀 Quick Start

### Con Docker Compose (Consigliato)

```bash
docker compose up -d
```

L'API sarà disponibile su `http://tuoip:8881`

### Manuale

```bash
# Installa dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python GeoIP-MAXLON.py
```

## 📝 Utilizzo

### Via API REST

```bash
# Lookup di un IP
curl http://tuoip:8881/8.8.8.8
```

### Via Web Interface

Apri il browser e vai su: `http://tuoip:8881`

## 🔧 Configurazione

Le seguenti variabili d'ambiente possono essere configurate:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DAEMON_WEB_HOST` | `0.0.0.0` | Host del server web |
| `DAEMON_WEB_PORT` | `8881` | Porta del server web |
| `DATA_FILENAME` | `/app/data/geoip/networks.csv` | Percorso database GeoIP |

### Esempio con Docker Compose

```yaml
services:
  geolocate:
    image: maxlonplay/geoip-maxlon:latest
    container_name: geoip-maxlon
    ports:
      - "8881:8881"
    volumes:
      - /data/geoip:/app/data/geoip
    restart: unless-stopped
```

## 📦 Dipendenze

- **Python 3.11+**
- **python-dotenv** - Gestione variabili d'ambiente
- **requests** - Client HTTP
- **polars** - Data manipulation ad alte prestazioni


### Esecuzione

```bash
docker run -p 8881:8881 -v /data/geoip:/app/data/geoip maxlonplay/geoip-maxlon:latest
```

### Con Docker Compose

```bash
# Avvio
docker compose up -d

# Stop
docker compose down

# Log
docker compose logs -f
```

## 📋 Requisiti di Sistema

- **OS**: Linux, macOS, Windows (con WSL2)
- **Memoria**: Min 2048MB RAM
- **Spazio**: Min 500MB per il database GeoIP
- **CPU**: 1+ core

## 🚦 API Endpoints

### GET /{ip}

Restituisce le informazioni geografiche per un indirizzo IP.

**Parametri:**
- `ip` (string): Indirizzo IP da cercare

**Risposta Success (200):**
```json
{
  "success": true,
  "ip": "8.8.8.8",
  "country": "US",
  "city": "Mountain View",
  "latitude": 37.4192,
  "longitude": -122.0574
}
```

**Risposta Error (400):**
```json
{
  "success": false,
  "error": "Invalid IP address"
}
```

## 🔄 Aggiornamento Database

Il database GeoIP viene scaricato automaticamente da:
```
https://ip.guide/bulk/networks.csv
```

Per aggiornare manualmente:
```bash
python -m core.db_updater
```

---

**Made with Python 🐍 & Docker 🐳**
