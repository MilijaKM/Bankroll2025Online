# app.py – sa passwordom + ispravljen JS (100% radi na Renderu)
import csv
from datetime import datetime
import pandas as pd
from flask import Flask, render_template_string, request, redirect, session, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = "super_tajna_12345"

FILENAME = "bankroll_history.csv"
PASSWORD = "tatajeboss123"        # ← tvoj password

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
        <h1>BANKROLL 2025</h1>
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
    df = pd.read_csv(FILENAME)
    rows = df.values.tolist()
    bankroll = float(df["bankroll_posle"].iloc[-1])

    if request.method == "POST":
        liga = request.form["liga"]
        mec = request.form["mec"]
        komentar = request.form["komentar"]
        proc = float(request.form["proc"])
        kurz = float(request.form["kurz"])
        ishod = request.form["ishod"]
        ulog = round(bankroll * proc / 100)
        profit = {"win":round(ulog*(kurz-1)),"loss":-ulog,"half":round(ulog*(kurz-1)/2),"void":0}[ishod]
        bankroll = round(bankroll + profit)
        with open(FILENAME,"a",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().strftime("%d.%m.%Y %H:%M"),liga,mec,komentar,proc,ulog,kurz,ishod,profit,bankroll])
        return redirect("/")

    # Koristimo raw string da izbegnemo {{ problem
    HTML = f"""<!DOCTYPE html>
<html><head><title>Bankroll 2025</title><meta charset="utf-8">
<style>body{{background:#121212;color:#0f0;text-align:center;padding:20px;font-family:Arial}}
h1{{color:#0f0;font-size:3em}}table{{margin:20px auto;border-collapse:collapse;width:95%}}
th,td{{border:1px solid #0f0;padding:10px}}input,select,button{{padding:12px;margin:10px;width:90%;max-width:400px;font-size:18px}}
button{{background:#0f0;color:#000;border:none;cursor:pointer}}.win{{color:#0f0}}.loss{{color:#f00}}</style>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head><body>
<h1><a href="/logout" style="float:right;font-size:16px;color:#aaa">Logout</a> BANKROLL {bankroll:,.0f} Kč</h1>
<div id="graf" style="width:95%;height:500px;"></div>
<script>
var x = [{', '.join(f'"{r[0]}"' for r in rows)}];
var y = [{', '.join(str(r[9]) for r in rows)}];
Plotly.newPlot('graf', [{{x:x, y:y, type:'scatter', mode:'lines+markers', line:{{color:'#0f0',width:4}}}}],
{{title:'Vývoj bankrollu', paper_bgcolor:'#121212', plot_bgcolor:'#121212', font:{{color:'#0f0'}}}});
</script>
<h2>Nova oklada</h2><form method=post>
<input name=liga placeholder="Liga" required><br>
<input name=mec placeholder="Meč" required><br>
<input name=komentar placeholder="Komentar"><br>
<input name=proc type=number step=0.1 placeholder="% uloga" required><br>
<input name=kurz type=number step=0.01 placeholder="Kurz" required><br>
<select name=ishod><option>win</option><option>loss</option><option>half</option><option>void</option></select><br>
<button>UNESI TIKET</button></form>
<h2>Poslednjih 10</h2><table><tr><th>Datum</th><th>Liga</th><th>Meč</th><th>Ishod</th><th>Profit</th><th>Bankroll</th></tr>
{"".join(f'<tr class=\"{"win" if r[7]=="win" else "loss" if r[7]=="loss" else ""}\"><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[7]}</td><td>{r[8]:,.0f}</td><td>{r[9]:,.0f}</td></tr>' for r in rows[-10:])}
</table></body></html>"""
    return HTML

if __name__ == "__main__":
    app.run()

    

