# app.py – KONAČNA VERZIJA – sve radi 100%
import csv
from datetime import datetime
import pandas as pd
from flask import Flask, render_template_string, request, redirect, session, url_for
from functools import wraps
import requests

app = Flask(__name__)
app.secret_key = "tata_je_boss_2025"

FILENAME = "bankroll_history.csv"
PASSWORD = "tatajeboss123"
TOKEN = "8168519055:AAGT8HVra9dLF4MFsZXFcGnY6kpA11Lfhm8"
CHAT_ID = "8349297056"   # ← OVDE STAVI SVOJ BROJ IZ getUpdates (koji si kopirao)

# Telegram funkcija
def posalji(tekst):
    if not CHAT_ID or CHAT_ID == "123456789":
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": tekst})
    except:
        pass

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
        <h1> BANKROLL 2025</h1>
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
    global bankroll
    df = pd.read_csv(FILENAME)
    rows = df.values.tolist()
    bankroll = float(df["bankroll_posle"].iloc[-1])

    kelly_msg = ""
    if "kelly_kvota" in request.form:
        try:
            kvota = float(request.form["kelly_kvota"])
            p = float(request.form["kelly_procena"]) / 100
            b = kvota - 1
            full = (b * p - (1 - p)) / b
            if full > 0:
                kelly_msg = f"FULL {full*100:.2f}% → {round(bankroll*full):,} Kč | HALF {full*100/2:.2f}% → {round(bankroll*full/2):,} Kč"
            else:
                kelly_msg = "NEMA VALUE!"
        except:
            kelly_msg = "Greška u unosu!"

    if "liga" in request.form:
        liga = request.form["liga"]
        mec = request.form["mec"]
        komentar = request.form.get("komentar", "")
        proc = float(request.form["proc"])
        kurz = float(request.form["kurz"])
        ishod = request.form["ishod"]

        ulog = round(bankroll * proc / 100)
        profit = {"win": round(ulog*(kurz-1)), "loss": -ulog, "half": round(ulog*(kurz-1)/2), "void": 0}[ishod]
        old = bankroll
        bankroll = round(bankroll + profit)

        with open(FILENAME, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().strftime("%d.%m.%Y %H:%M"), liga, mec, komentar, proc, ulog, kurz, ishod, profit, bankroll])

        if old < 200000 <= bankroll:
            posalji(f"ČESTITAMO! PREŠAO SI 200.000 Kč!\nBankroll: {bankroll:,} Kč")

        return redirect("/")

    HTML = f"""<!DOCTYPE html>
<html><head><title>Bankroll 2025</title><meta charset="utf-8">
<style>body{{background:#121212;color:#0f0;text-align:center;padding:20px;font-family:Arial}}
h1{{color:#0f0;font-size:3em}}input,select,button{{padding:12px;margin:8px;width:90%;max-width:400px;font-size:18px}}
button{{background:#0f0;color:black;border:none;cursor:pointer}}</style>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head><body>
<h1><a href="/logout" style="float:right;color:#aaa;font-size:16px">Logout</a> BANKROLL {bankroll:,.0f} Kč</h1>
<div id="graf" style="width:95%;height:500px;"></div>
<script>
var x = [{', '.join(f'"{r[0]}"' for r in rows)}];
var y = [{', '.join(str(r[9]) for r in rows)}];
Plotly.newPlot('graf', [{{x:x,y:y,type:'scatter',mode:'lines+markers',line:{{color:'#0f0',width:4}}}}],
{{title:'Vývoj bankrollu',paper_bgcolor:'#121212',plot_bgcolor:'#121212',font:{{color:'#0f0'}}}});
</script>

<h2>KELLY KALKULATOR</h2>
<form method=post><input name=kelly_kvota placeholder="Kvota" type=number step=0.01 required>
<input name=kelly_procena placeholder="Procena %" type=number required><button>IZRAČUNAJ</button></form>
<h2 style="color:yellow">{kelly_msg}</h2>

<h2>NOVA OKLADA</h2>
<form method=post>
<input name=liga placeholder="Liga/Sport" required><br>
<input name=mec placeholder="Meč" required><br>
<input name=komentar placeholder="Komentar"><br>
<input name=proc type=number step=0.1 placeholder="% uloga" required><br>
<input name=kurz type=number step=0.01 placeholder="Kurz" required><br>
<select name=ishod><option>win</option><option>loss</option><option>half</option><option>void</option></select><br>
<button>UNESI TIKET</button>
</form>

<h2>Poslednjih 10</h2>
<table style="margin:auto;width:95%"><tr><th>Datum</th><th>Liga</th><th>Meč</th><th>Ishod</th><th>Profit</th><th>Bankroll</th></tr>
{"".join(f'<tr style=\"color:{\"lime\" if r[7]==\"win\" else \"red\" if r[7]==\"loss\" else \"white\"}\"><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[7]}</td><td>{r[8]:+.0f}</td><td>{r[9]:,.0f}</td></tr>' for r in rows[-10:])}
</table>
</body></html>"""
    return HTML

if __name__ == "__main__":
    app.run()




