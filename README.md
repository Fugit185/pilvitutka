# Pilvitutka

Telegram-botti joka seuraa pilvisyyttä Etelä-Suomessa ja ilmoittaa kun merellä on selkeämpää kuin mantereella. Hyödyllinen kesällä kun mantereen päällä on usein pilviä mutta meren päällä selkeää.

## Toiminta

- Hakee pilvisyysdatan Open-Meteo API:sta (MET Nordic -malli, 1 km resoluutio)
- Seuraa 6 pistettä: avomeri, rannikko (Helsinki/Harmaja) ja sisämaa (Vantaa/Hyvinkää)
- Laskee keskiarvot alueittain (meri / rannikko / mantere)
- Lähettää Telegram-viestin kun meren ja mantereen pilvisyysero on merkittävä (>30%-yksikköä)
- Näyttää 6h ennusteen

### Esimerkki Telegram-viestistä

```
PILVITUTKA 15.07. klo 14:00

  Avomeri (etelä)      ██░░░░░░░░  15%
  Avomeri (länsi)      █░░░░░░░░░  10%
  Harmaja              ████░░░░░░  40%
  Helsinki             █████░░░░░  45%
  Vantaa               ████████░░  80%
  Hyvinkää             █████████░  90%

Merellä 73 prosenttiyksikköä selkeämpää kuin mantereella!
```

## Teknologia

- **Datanlähde**: Open-Meteo (MET Nordic, FMI & MET Norway, ilmainen, ei API-avainta)
- Python 3.9+, requests
- Telegram Bot API
- Raspberry Pi

## Asennus

```bash
cd ~/pythonohjelmia/pilvitutka
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Luo `.env`-tiedosto:

```
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
```

## Käyttö

```bash
# Tarkista kerran (lähettää viestin vain jos ero on merkittävä)
.venv/bin/python3 pilvitutka.py

# Pakota Telegram-viesti
.venv/bin/python3 pilvitutka.py --force

# Jatkuva seuranta (tarkistaa tunnin välein)
.venv/bin/python3 pilvitutka.py --loop
```

### Cron-esimerkki (kesäkuukaudet, tunnin välein klo 8–21)

```cron
0 8-21 * 5-8 * cd ~/pythonohjelmia/pilvitutka && .venv/bin/python3 pilvitutka.py
```

## Hakemistorakenne

```
pilvitutka/
├── pilvitutka.py        # Pääohjelma
├── .env                 # Telegram-tunnukset (ei versionhallinnassa)
└── requirements.txt
```

## Tunnukset

Telegram-tokenit ja muut API-avaimet löytyvät Macilta: `~/Documents/raspi_bot_credentials.txt`
