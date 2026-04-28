import streamlit as st
import json, os, requests, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ── CONFIG ────────────────────────────────────────────────────
st.set_page_config(page_title="Vedot", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

STORAGE_FILE = "bets.json"
FI = ZoneInfo("Europe/Helsinki")

SPORT_KEYS = {
    "⚽ Jalkapallo": [
        "soccer_finland_veikkausliiga","soccer_epl","soccer_sweden_allsvenskan",
        "soccer_champions_league","soccer_uefa_europa_league",
        "soccer_germany_bundesliga","soccer_spain_la_liga","soccer_italy_serie_a",
    ],
    "🏒 Jääkiekko": ["icehockey_finland_liiga","icehockey_sweden_hockey_league","icehockey_nhl"],
    "🏀 Koripallo": ["basketball_nba","basketball_euroleague"],
    "🎾 Tennis":    ["tennis_atp_french_open","tennis_wta_french_open"],
}

# ── STORAGE ───────────────────────────────────────────────────
def load_bets():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_bets(bets):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(bets, f, ensure_ascii=False, indent=2)

# ── SESSION STATE ─────────────────────────────────────────────
if "bets" not in st.session_state:
    st.session_state.bets = load_bets()
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("ODDS_API_KEY", "")
if "last_autocheck" not in st.session_state:
    st.session_state.last_autocheck = 0

def persist():
    save_bets(st.session_state.bets)

# ── API CALLS ─────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_events(sport_key: str, api_key: str):
    if not api_key:
        return []
    try:
        r = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",
            params={"apiKey": api_key, "regions": "eu", "markets": "h2h", "dateFormat": "iso"},
            timeout=8,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=120, show_spinner=False)
def fetch_scores(sport_key: str, api_key: str):
    if not api_key:
        return []
    try:
        r = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/",
            params={"apiKey": api_key, "daysFrom": 3},
            timeout=8,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

# ── AUTO-CHECK RESULTS ────────────────────────────────────────
def auto_check_results(silent=False):
    if not st.session_state.api_key:
        return 0
    now = datetime.now(timezone.utc)
    pending = [
        b for b in st.session_state.bets
        if b["status"] == "pending"
        and b.get("sport_key")
        and b.get("event_id")
        and b.get("start_time")
        and datetime.fromisoformat(b["start_time"].replace("Z", "+00:00")) < now
    ]
    if not pending:
        return 0

    sports = {}
    for b in pending:
        sports.setdefault(b["sport_key"], []).append(b)

    updated = 0
    for sport_key, sport_bets in sports.items():
        scores = fetch_scores(sport_key, st.session_state.api_key)
        for ev in scores:
            if not ev.get("completed"):
                continue
            for bet in sport_bets:
                if bet.get("event_id") != ev.get("id"):
                    continue
                score_parts = ev.get("scores") or []
                if score_parts:
                    bet["final_score"] = " – ".join(f"{s['name']} {s['score']}" for s in score_parts)
                bet["status"] = "needs_confirmation"
                updated += 1

    if updated:
        persist()
    return updated

# Automaattinen tarkistus 5 min välein sivun latautuessa
now_ts = time.time()
if now_ts - st.session_state.last_autocheck > 300:
    auto_check_results(silent=True)
    st.session_state.last_autocheck = now_ts

# ── STATS ─────────────────────────────────────────────────────
def stats(bets):
    total  = len(bets)
    won    = sum(1 for b in bets if b["status"] == "won")
    lost   = sum(1 for b in bets if b["status"] == "lost")
    open_  = sum(1 for b in bets if b["status"] in ("pending","needs_confirmation"))
    profit = sum(
        b["stake"]*b["odds"] - b["stake"] if b["status"] == "won"
        else -b["stake"]                  if b["status"] == "lost"
        else 0
        for b in bets
    )
    settled = won + lost
    rate   = f"{won/settled*100:.0f} %" if settled else "—"
    return total, won, lost, open_, profit, rate

# ── STYLES ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#0e0e10;color:#f0eff4;}
#MainMenu,footer,header{visibility:hidden;}

.vedot-header{background:#161618;border-bottom:1px solid rgba(255,255,255,0.08);padding:1.1rem 0;margin:-1rem -1rem 2rem -1rem;text-align:center;}
.vedot-title{font-size:26px;font-weight:700;letter-spacing:0.15em;color:#f0eff4;}
.vedot-title span{color:#c8f04a;}

.stat-box{background:#161618;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:1rem 1.25rem;text-align:center;}
.stat-label{font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#5e5d6e;margin-bottom:4px;}
.stat-value{font-family:'IBM Plex Mono',monospace;font-size:24px;font-weight:500;color:#f0eff4;}
.stat-value.win{color:#4ade80;}.stat-value.loss{color:#f87171;}.stat-value.acc{color:#c8f04a;}

.bet-card{background:#161618;border:1px solid rgba(255,255,255,0.08);border-left:3px solid rgba(255,255,255,0.1);border-radius:12px;padding:1.1rem 1.25rem;margin-bottom:10px;}
.bet-card.won{border-left-color:#4ade80;}.bet-card.lost{border-left-color:#f87171;}
.bet-card.pending{border-left-color:#fbbf24;}.bet-card.needs_confirmation{border-left-color:#60a5fa;}
.bet-game{font-size:15px;font-weight:600;color:#f0eff4;margin-bottom:3px;}
.bet-desc{font-size:13px;color:#9998a8;margin-bottom:10px;}
.bet-nums{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:8px;}
.bet-num-label{font-size:10px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#5e5d6e;}
.bet-num-val{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:500;color:#f0eff4;}
.bet-time{font-size:11px;color:#5e5d6e;font-family:'IBM Plex Mono',monospace;}

.badge{display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;letter-spacing:0.04em;}
.badge-won{background:rgba(74,222,128,0.12);color:#4ade80;}
.badge-lost{background:rgba(248,113,113,0.12);color:#f87171;}
.badge-pending{background:rgba(251,191,36,0.1);color:#fbbf24;}
.badge-blue{background:rgba(96,165,250,0.12);color:#60a5fa;}

.profit-pos{color:#4ade80;font-family:'IBM Plex Mono',monospace;}
.profit-neg{color:#f87171;font-family:'IBM Plex Mono',monospace;}
.section-title{font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#5e5d6e;margin-bottom:1rem;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.06);}

div[data-testid="stTextInput"]>div>div>input,
div[data-testid="stNumberInput"]>div>div>input{background:#1e1e21!important;border-color:rgba(255,255,255,0.1)!important;color:#f0eff4!important;}
.stButton>button{background:#c8f04a!important;color:#0e0e10!important;border:none!important;font-family:'Syne',sans-serif!important;font-weight:600!important;border-radius:8px!important;}
.stButton>button:hover{opacity:0.85!important;}
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────
st.markdown('<div class="vedot-header"><div class="vedot-title"><span>◈</span> VEDOT</div><div style="font-size:12px;color:#5e5d6e;margin-top:4px;">Vedonlyöntikirjanpito</div></div>', unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Asetukset")
    api_key_input = st.text_input("The Odds API -avain", value=st.session_state.api_key, type="password",
        help="Hae ilmainen avain: the-odds-api.com (500 req/kk)")
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
    if st.session_state.api_key:
        st.success("API-avain asetettu ✓")
    else:
        st.info("Ilman API-avainta tapahtumahaku ei toimi. Manuaalinen kirjaus toimii aina.")
    st.divider()
    st.markdown("**🔄 Automaattinen tulostarkistus**")
    st.caption("Tarkistaa avoimet vedot joilla on tapahtuma-ID (haun kautta lisätyt). Ajautuu myös automaattisesti 5 min välein.")
    if st.button("Tarkista tulokset nyt", use_container_width=True):
        with st.spinner("Tarkistetaan..."):
            n = auto_check_results()
        st.success(f"{n} vedon tulos päivitetty!") if n else st.info("Ei uusia tuloksia.")
    st.divider()
    if st.button("🗑️ Poista kaikki vedot", use_container_width=True):
        if st.session_state.bets:
            st.session_state.bets = []
            persist()
            st.rerun()

# ── STATS ─────────────────────────────────────────────────────
total, won, lost, open_, profit, rate = stats(st.session_state.bets)
ps = "+" if profit > 0 else ""
pc = "win" if profit > 0 else "loss" if profit < 0 else ""

cols = st.columns(6)
for col, label, value, cls in [
    (cols[0],"Vedot",   str(total),                ""),
    (cols[1],"Voitot",  str(won),                  "win"),
    (cols[2],"Häviöt",  str(lost),                 "loss"),
    (cols[3],"Avoimet", str(open_),                ""),
    (cols[4],"Tuotto",  f"{ps}{profit:.2f} €",     pc),
    (cols[5],"Osuvuus", rate,                      "acc"),
]:
    col.markdown(f'<div class="stat-box"><div class="stat-label">{label}</div><div class="stat-value {cls}">{value}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────
tab_add, tab_search, tab_bets = st.tabs(["➕ Lisää veto", "🔍 Hae tapahtuma", "📋 Kaikki vedot"])

# ════════════════════════════════════════════
# TAB 1 — Manuaalinen lisäys
# ════════════════════════════════════════════
with tab_add:
    st.markdown('<div class="section-title">Uusi veto</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        game  = st.text_input("Peli / tapahtuma", placeholder="esim. Chelsea – Arsenal")
        bet   = st.text_input("Veto", placeholder="esim. Chelsea voittaa")
    with c2:
        stake = st.number_input("Panos (€)", min_value=0.01, value=None, step=0.5, format="%.2f")
        odds  = st.number_input("Kerroin",   min_value=1.01, value=None, step=0.05, format="%.2f")

    dc, tc, potc = st.columns(3)
    with dc: start_date = st.date_input("Alkamispäivä", value=None)
    with tc: start_time = st.time_input("Alkamisaika",  value=None)
    with potc:
        if stake and odds:
            pot = stake * odds
            st.markdown(f'<div style="margin-top:28px;background:#1e1e21;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:12px 16px;"><div class="stat-label">Potentiaalinen voitto</div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:20px;font-weight:500;color:#c8f04a;">{pot:.2f} €</div><div style="font-size:11px;color:#5e5d6e;">Netto: +{pot-stake:.2f} €</div></div>', unsafe_allow_html=True)

    if st.button("Lisää veto ✓", use_container_width=True):
        if not game or not bet or not stake or not odds:
            st.error("Täytä kaikki kentät.")
        else:
            start_iso = None
            if start_date and start_time:
                start_iso = datetime.combine(start_date, start_time, tzinfo=FI).isoformat()
            st.session_state.bets.insert(0, {
                "id": int(time.time()*1000), "game": game, "bet": bet,
                "stake": stake, "odds": odds, "status": "pending",
                "date": datetime.now(FI).strftime("%d.%m.%Y"),
                "start_time": start_iso, "sport_key": None, "event_id": None, "source": "manual",
            })
            persist()
            st.success(f"Lisätty: {game}")
            st.rerun()

# ════════════════════════════════════════════
# TAB 2 — Tapahtumahaku
# ════════════════════════════════════════════
with tab_search:
    st.markdown('<div class="section-title">Hae tapahtumaa</div>', unsafe_allow_html=True)
    if not st.session_state.api_key:
        st.warning("⚠️ Lisää The Odds API -avain sivupalkista.")
        st.markdown("Hae ilmainen avain: **[the-odds-api.com](https://the-odds-api.com/)** — 500 pyyntöä/kk ilmaiseksi")
    else:
        sport_choice = st.selectbox("Laji", list(SPORT_KEYS.keys()))
        query = st.text_input("Hae joukkuetta tai tapahtumaa", placeholder="esim. HJK, Chelsea...")
        if query:
            with st.spinner("Haetaan..."):
                all_events = []
                for sk in SPORT_KEYS[sport_choice]:
                    for ev in fetch_events(sk, st.session_state.api_key):
                        name = f"{ev['home_team']} – {ev['away_team']}"
                        if query.lower() in name.lower():
                            all_events.append({"id":ev["id"],"name":name,"sport_key":ev["sport_key"],"start":ev["commence_time"]})
            if not all_events:
                st.info(f"Ei tuloksia haulle '{query}'.")
            else:
                st.markdown(f"**{len(all_events)} tapahtumaa**")
                for ev in all_events[:20]:
                    dt = datetime.fromisoformat(ev["start"].replace("Z","+00:00")).astimezone(FI)
                    with st.expander(f"🏟 {ev['name']}  ·  {dt.strftime('%d.%m. %H:%M')}"):
                        st.markdown(f"**Alkaa:** {dt.strftime('%d.%m.%Y %H:%M')} (Helsinki)")
                        b_desc = st.text_input("Veto", placeholder="esim. Kotijoukkue voittaa", key=f"b_{ev['id']}")
                        cs, co = st.columns(2)
                        with cs: b_stake = st.number_input("Panos (€)", min_value=0.01, value=None, step=0.5, format="%.2f", key=f"s_{ev['id']}")
                        with co: b_odds  = st.number_input("Kerroin",   min_value=1.01, value=None, step=0.05, format="%.2f", key=f"o_{ev['id']}")
                        if b_stake and b_odds:
                            pot = b_stake * b_odds
                            st.markdown(f"**Pot. voitto: {pot:.2f} € (netto +{pot-b_stake:.2f} €)**")
                        if st.button("Lisää tämä veto", key=f"add_{ev['id']}"):
                            if not b_desc or not b_stake or not b_odds:
                                st.error("Täytä kaikki kentät.")
                            else:
                                st.session_state.bets.insert(0, {
                                    "id": int(time.time()*1000), "game": ev["name"], "bet": b_desc,
                                    "stake": b_stake, "odds": b_odds, "status": "pending",
                                    "date": datetime.now(FI).strftime("%d.%m.%Y"),
                                    "start_time": ev["start"], "sport_key": ev["sport_key"],
                                    "event_id": ev["id"], "source": "search",
                                })
                                persist()
                                st.success(f"Lisätty: {ev['name']}")
                                st.rerun()

# ════════════════════════════════════════════
# TAB 3 — Kaikki vedot
# ════════════════════════════════════════════
with tab_bets:
    filt = st.radio("Näytä", ["Kaikki","Avoimet","Voitot","Häviöt"], horizontal=True)
    filt_map = {"Kaikki":None,"Avoimet":["pending","needs_confirmation"],"Voitot":["won"],"Häviöt":["lost"]}
    filtered = [b for b in st.session_state.bets if filt_map[filt] is None or b["status"] in filt_map[filt]]

    if not filtered:
        st.markdown('<div style="text-align:center;color:#5e5d6e;padding:3rem;"><div style="font-size:36px;margin-bottom:1rem;">◈</div><p>Ei vetoja tässä kategoriassa</p></div>', unsafe_allow_html=True)
    else:
        for bet in filtered:
            status = bet["status"]
            badge_cls = {"won":"badge-won","lost":"badge-lost","pending":"badge-pending","needs_confirmation":"badge-blue"}.get(status,"badge-pending")
            badge_lbl = {"won":"✓ Voitto","lost":"✗ Häviö","pending":"⏳ Avoin","needs_confirmation":"🔵 Tarkista"}.get(status,"Avoin")
            pot = bet["stake"] * bet["odds"]
            profit_val = pot - bet["stake"] if status=="won" else -bet["stake"] if status=="lost" else None

            time_str = ""
            if bet.get("start_time"):
                try:
                    dt = datetime.fromisoformat(bet["start_time"].replace("Z","+00:00")).astimezone(FI)
                    time_str = dt.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    pass

            score_html = f'<div style="font-size:12px;color:#60a5fa;margin-top:4px;">📊 Lopputulos: {bet["final_score"]}</div>' if bet.get("final_score") else ""
            profit_html = ""
            if profit_val is not None:
                cls = "profit-pos" if profit_val > 0 else "profit-neg"
                sign = "+" if profit_val > 0 else ""
                profit_html = f'<div><div class="bet-num-label">Tulos</div><div class="bet-num-val"><span class="{cls}">{sign}{profit_val:.2f} €</span></div></div>'

            st.markdown(f"""
            <div class="bet-card {status}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;gap:12px;">
                <div style="flex:1;min-width:0;">
                  <div class="bet-game">{bet['game']}</div>
                  <div class="bet-desc">{bet['bet']}</div>
                </div>
                <span class="badge {badge_cls}">{badge_lbl}</span>
              </div>
              <div class="bet-nums">
                <div><div class="bet-num-label">Panos</div><div class="bet-num-val">{bet['stake']:.2f} €</div></div>
                <div><div class="bet-num-label">Kerroin</div><div class="bet-num-val">{bet['odds']:.2f}</div></div>
                <div><div class="bet-num-label">Pot. voitto</div><div class="bet-num-val">{pot:.2f} €</div></div>
                {profit_html}
              </div>
              {score_html}
              <div class="bet-time">{"⏱ "+time_str+"  ·  " if time_str else ""}Lisätty {bet['date']}</div>
            </div>""", unsafe_allow_html=True)

            bid = bet["id"]
            if status == "pending":
                a1,a2,a3,_ = st.columns([1,1,1,5])
                with a1:
                    if st.button("✓ Voitto", key=f"w_{bid}"): bet["status"]="won"; persist(); st.rerun()
                with a2:
                    if st.button("✗ Häviö",  key=f"l_{bid}"): bet["status"]="lost"; persist(); st.rerun()
                with a3:
                    if st.button("🗑 Poista", key=f"d_{bid}"):
                        st.session_state.bets=[b for b in st.session_state.bets if b["id"]!=bid]; persist(); st.rerun()

            elif status == "needs_confirmation":
                st.info(f"🔵 Ottelu päättynyt. Lopputulos: **{bet.get('final_score','ei saatavilla')}** — vahvista tulos:")
                a1,a2,a3,_ = st.columns([1,1,1,5])
                with a1:
                    if st.button("✓ Voitto", key=f"w_{bid}"): bet["status"]="won"; persist(); st.rerun()
                with a2:
                    if st.button("✗ Häviö",  key=f"l_{bid}"): bet["status"]="lost"; persist(); st.rerun()
                with a3:
                    if st.button("🗑 Poista", key=f"d_{bid}"):
                        st.session_state.bets=[b for b in st.session_state.bets if b["id"]!=bid]; persist(); st.rerun()

            elif status in ("won","lost"):
                b1,b2,_ = st.columns([1.5,1,5])
                with b1:
                    if st.button("↩ Palauta avoimeksi", key=f"r_{bid}"): bet["status"]="pending"; persist(); st.rerun()
                with b2:
                    if st.button("🗑 Poista", key=f"d_{bid}"):
                        st.session_state.bets=[b for b in st.session_state.bets if b["id"]!=bid]; persist(); st.rerun()

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

st.markdown('<div style="text-align:center;padding:2rem 0 1rem;color:#5e5d6e;font-size:12px;border-top:1px solid rgba(255,255,255,0.06);margin-top:2rem;">Vedot · Tiedot tallennetaan paikallisesti bets.json-tiedostoon</div>', unsafe_allow_html=True)
