# ◈ Vedot – Vedonlyöntikirjanpito

Streamlit-pohjainen vedonlyöntikirjanpito jossa:
- Manuaalinen vetojen syöttö (peli, veto, panos, kerroin, ajankohta)
- **Tapahtumahaku** The Odds API:n kautta (jalkapallo, jääkiekko, koripallo, tennis)
- **Automaattinen tulostarkistus** päättyneille otteluille
- Tilastot: vedot, voitot, häviöt, tuotto-%, osuvuus
- Toimii täydellisesti sekä tietokoneella että puhelimella

---

## 🚀 Asennus ja käynnistys

### 1. Kloonaa / lataa tiedostot

```bash
git clone <repo-url>
cd vedot-app
```

### 2. Asenna riippuvuudet

```bash
pip install -r requirements.txt
```

### 3. Käynnistä

```bash
streamlit run app.py
```

Avaa selaimessa: **http://localhost:8501**

---

## 🔑 API-avain (valinnainen mutta suositeltava)

Hae **ilmainen** API-avain: https://the-odds-api.com/
- Ilmainen tili: **500 pyyntöä/kuukausi** (riittää hyvin)
- Syötä avain sovelluksen sivupalkissa **tai** aseta ympäristömuuttujana:

```bash
export ODDS_API_KEY="sinun_avaimesi_tahan"
streamlit run app.py
```

**Ilman API-avainta** sovellus toimii täysin manuaalisesti – voit silti lisätä vetoja, merkitä tulokset käsin ja seurata tilastoja.

---

## ☁️ Deploy Streamlit Cloudiin (ilmainen)

1. Laita koodi GitHubiin
2. Mene: https://share.streamlit.io/
3. Yhdistä GitHub-repo → valitse `app.py`
4. Lisää **Secrets**-osioon:
   ```toml
   ODDS_API_KEY = "sinun_avaimesi"
   ```
5. Deploy → saat julkisen URL:n

---

## 📂 Tiedostorakenne

```
vedot-app/
├── app.py           # Pääsovellus
├── requirements.txt # Python-riippuvuudet
├── bets.json        # Vetojen tallennustiedosto (luodaan automaattisesti)
└── README.md        # Tämä tiedosto
```

---

## 🏟️ Tuetut lajit ja sarjat

| Laji | Sarjat |
|------|--------|
| ⚽ Jalkapallo | Veikkausliiga, Premier League, Allsvenskan, Mestarien liiga, Eurooppa-liiga, Bundesliiga, La Liga, Serie A |
| 🏒 Jääkiekko | Liiga, SHL, NHL |
| 🏀 Koripallo | NBA, Euroleague |
| 🎾 Tennis | ATP / WTA |

---

## 💾 Tiedot

Vedot tallennetaan `bets.json`-tiedostoon paikallisesti. Varmuuskopioi tiedosto säännöllisesti tai käytä Git-versionhallintaa.

---

## 🔄 Automaattinen tulostarkistus

- Klikkaa sivupalkissa **"Tarkista tulokset nyt"**
- Päättyneet ottelut saavat tilan **"Tarkista"** (sininen)
- Vahvista tulos manuaalisesti: Voitto / Häviö
