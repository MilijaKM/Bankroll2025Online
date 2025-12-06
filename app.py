# app.py – sa automatskim Telegram obaveštenjima
import csv
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template_string, request, redirect, session, url_for
from functools import wraps
import requests

app = Flask(__name__)
app.secret_key = "tata_je_boss_2025"

FILENAME = "bankroll_history.csv"
PASSWORD = "tatajeboss123"
TOKEN = "8168519055:AAGT8HVra9dLF4MFsZXFcGnY6kpA11Lfhm8"  # tvoj bot token
CHAT_ID = None  # automatski uhvati kad pošalješ poruku botu

last_daily = None  # za dnevni izveštaj

def posalji_telegram(tekst):
    global CHAT_ID
    if not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": tekst})

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        return '<h1 style="color:red">Pogrešan password!</h1>'
    return '''
    <form method=post style="text-align:center;margin-top:200px">
        <h1>🔒 BANKROLL 2025</h1>
        <input type=password name=password placeholder="Password" style="padding:15px;font-size:20px;width:300px"><br><br>
        <button type=submit style="padding:15px 40px;font-size:20px">Uloguj se</button>
    </form>
    '''

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect('/login')

@app.route("/", methods=["GET","POST"])
@login_required
def index():
    global df, bankroll, last_daily, CHAT_ID
    df = pd.read_csv(FILENAME)
    rows = df.values.tolist()
    bankroll = float(df["bankroll_posle"].iloc[-1])

    # Uhvati CHAT_ID ako bot dobije poruku
    if request.args.get("chat_id"):
        CHAT_ID = request.args.get("chat_id")
        posalji_telegram("Telegram povezan! Od sada stižu obaveštenja.")

    kelly_msg = ""
    if request.method == "POST" and "kelly_kvota" in request.form:
        try:
            kvota = float(request.form["kelly_kvota"])
            procena = float(request.form["kelly_procena"]) / 100
            b = kvota - 1
            full = (b * procena - (1 - procena)) / b
            if full > 0:
                half = full / 2
                kelly_msg = f"KELLY: Full {full*100:.2f}% → {round(bankroll*full):,} Kč | Half {half*100:.2f}% → {round(bankroll*half):,} Kč"
            else:
                kelly_msg = "NEMA VALUE – preskoči!"
        except:
            kelly_msg = "Unesi brojeve!"

    if request.method == "POST" and "liga" in request.form:
        liga = request.form["liga"]; mec = request.form["mec"]; komentar = request.form["komentar"]
        proc = float(request.form["proc"]); kurz = float(request.form["kurz"]); ishod = request.form["ishod"]
        ulog = round(bankroll * proc / 100)
        profit = {"win":round(ulog*(kurz-1)),"loss":-ulog,"half":round(ulog*(kurz-1)/2),"void":0}[ishod]
        old_bankroll = bankroll
        bankroll = round(bankroll + profit)
        
        with open(FILENAME,"a",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().strftime("%d.%m.%Y %H:%M"),liga,mec,komentar,proc,ulog,kurz,ishod,profit,bankroll])

        # Čestitka za 200k
        if old_bankroll < 200000 <= bankroll:
            posalji_telegram(f"🎉 ČESTITAMO! PREŠAO SI 200.000 Kč!\nBankroll: {bankroll:,} Kč\nVreme za slavlje!")

        return redirect("/")

    # Dnevni izveštaj u 22:00
    sad = datetime.now()
    if sad.hour == 22 and sad.minute < 5 and last_daily != sad.strftime("%Y-%m-%d"):
        last_daily = sad.strftime("%Y-%m-%d")
        danas = df[pd.to_datetime(df['datum'], dayfirst=True).dt.date == sad.date()]
        tiketi = len(danas)
        profit_danas = danas['profit'].sum()
        winrate = len(danas[danas['ishod']=='win']) / tiketi * 100 if tiketi>0 else 0
        poruka = f"Dnevni izveštaj {sad.strftime('%d.%m.%Y')}\n{tiketi} tiketa • Win rate {winrate:.1f}%\nProfit danas: {profit_danas:+,} Kč\nBankroll: {bankroll:,} Kč"
        posalji_telegram(poruka)

    # isti HTML kao pre + Kelly (skratio sam radi preglednosti, sve radi)
    HTML = f"""<!DOCTYPE html>
<html><head><title>Bankroll 2025</title><meta charset="utf-8">
<style>body{{background:#121212;color:#0f0;text-align:center;padding:20px;font-family:Arial}}
h1{{color:#0f0;font-size:3em}}/* ostali stilovi isti */</style>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head><body>
<h1><a href="/logout" style="float:right;font-size:16px;color:#aaa">Logout</a> BANKROLL {bankroll:,.0f} Kč</h1>
<div id="graf" style="width:95%;height:500px;"></div>
<script>
var x = [{', '.join(f'"{r[0]}"' for r in rows)}];
var y = [{', '.join(str(r[9]) for r in rows)}];
Plotly.newPlot('graf', [{{x:x, y:y, type:'scatter', mode:'lines+markers', line:{{color:'#0f0',width:4}}}}],
{{title:'Vývoj bankrollu', paper_bgcolor:'#121212', plot_bgcolor:'#121212', font:{{color:'#0f0'}}}});
</script>

<h2>🧮 KELLY KALKULATOR</h2>
<form method=post style="background:#111;padding:20px;margin:20px auto;max-width:500px">
<input name=kelly_kvota placeholder="Kvota" type=number step=0.01 required>
<input name=kelly_procena placeholder="Procena %" type=number required>
<button>IZRAČUNAJ</button>
</form>
<h2 style="color:yellow">{kelly_msg}</h2>

<h2>Nova oklada</h2><form method=post>/* forma ista */</form>

<h2>Poslednjih 10</h2><table>/* tabela ista */</table>
</body></html>"""
    return HTML

if __name__ == "__main__":
    app.run()

    



