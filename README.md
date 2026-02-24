# Pilvitutka

Telegram-botti joka seuraa pilvisyyttä Etelä-Suomessa ja ilmoittaa kun merellä on selkeämpää kuin mantereella.

Hyödyllinen erityisesti kesällä, kun mantereen päällä on usein pilviä mutta meren päällä selkeää.

## Toiminta

- Hakee pilvisyysdatan Open-Meteo API:sta (MET Nordic -malli, 1 km resoluutio)
- Seuraa 6 pistettä: avomeri, rannikko (Helsinki/Harmaja) ja sisämaa (Vantaa/Hyvinkää)
- Laskee keskiarvot alueittain (meri / rannikko / mantere)
- Lähettää Telegram-viestin kun meren ja mantereen pilvisyysero on merkittävä
- Näyttää 6h ennusteen

## Esimerkki Telegram-viestistä

```
PILVITUTKA 15.07. klo 14:00

  Avomeri (etelä)      ██░░░░░░░░  15% – Melko selkeää
  Avomeri (länsi)      █░░░░░░░░░  10% – Selkeää
  Harmaja              ████░░░░░░  40% – Puolipilvistä
  Helsinki             █████░░░░░  45% – Puolipilvistä
  Vantaa               ████████░░  80% – Melko pilvistä
  Hyvinkää             █████████░  90% – Pilvistä

Keskiarvot:
  Meri:       12% – Melko selkeää
  Rannikko:   42% – Puolipilvistä
  Mantere:    85% – Pilvistä

Merellä 73 prosenttiyksikköä selkeämpää kuin mantereella!
```

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

## Hälytyslogiikka

Telegram-viesti lähetetään kun:
- Mantereen ja meren pilvisyysero on yli **30 prosenttiyksikköä**
- Meren pilvisyys on alle **40%**

## Datalähde

[Open-Meteo](https://open-meteo.com/) – MET Nordic -malli (yhteistuotanto FMI & MET Norway). Ilmainen, ei vaadi API-avainta.

## Teknologia

- Python 3.9+
- Open-Meteo API
- Telegram Bot API
- Raspberry Pi

## Tunnukset

Telegram-tokenit ja muut API-avaimet löytyvät Macilta: 
