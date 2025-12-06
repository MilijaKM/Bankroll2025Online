# app.py – tvoj online bankroll tracker
import csv
from datetime import datetime
import pandas as pd
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
FILENAME = "bankroll_history.csv"

HTML = '''
<!DOCTYPE html>
<html><head><title>Bankroll 2025</title><meta charset="utf-8">
<style>body{font-family:Arial;background:#121212;color:#0f0;text-align:center;padding:20px}
h1{color:#0f0;font-size:3em;}table{margin:20px auto;border-collapse:collapse;width:95%}
th,td{border:1px solid #0f0;padding:10px;color:#0f0}input,select,button{padding:12px;margin:10px;font-size:18px;width:90%;max-width:400px}
button{background:#0f0;color:#000;border:none;cursor:pointer}.win{color:#0f0}.loss{color:#f00}</style>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head><body>
<h1>BANKROLL {{ "%.0f" % bankroll }} Kč</h1>
<div id="graf" style="width:95%;height:500px;"></div>
<script>
var data=[{x:[{% for r in rows %}"{{ r[0] }}",{% endfor %}], y:[{% for r in rows %}{{ r[9] }},{% endfor %}],
type:'scatter', mode:'lines+markers', line:{color:'#0f0',width:4}}];
Plotly.newPlot('graf',data,{title:'Vývoj bankrollu',paper_bgcolor:'#121212',plot_bgcolor:'#121212',font:{color:'#0f0'}});
</script>
<h2>Nova oklada</h2><form method=post>
<input name=liga placeholder="Liga/Sport" required><br>
<input name=mec placeholder="Meč" required><br>
<input name=komentar placeholder="Komentar"><br>
<input name=proc type=number step=0.1 placeholder="% uloga" required><br>
<input name=kurz type=number step=0.01 placeholder="Kurz" required><br>
<select name=ishod><option>win</option><option>loss</option><option>half</option><option>void</option></select><br>
<button>UNESI TIKET</button></form>
<h2>Poslednjih 10</h2><table><tr><th>Datum</th><th>Liga</th><th>Meč</th><th>Ishod</th><th>Profit</th><th>Bankroll</th></tr>
{% for r in rows[-10:] %}
<tr class="{{ 'win' if r[7]=='win' else 'loss' if r[7]=='loss' else '' }}">
<td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td><td>{{ r[7] }}</td><td>{{ "%.0f" % r[8] }}</td><td>{{ "%.0f" % r[9] }}</td></tr>
{% endfor %}</table></body></html>
'''

@app.route("/", methods=["GET","POST"])
def index():
    df = pd.read_csv(FILENAME)
    rows = df.values.tolist()
    bankroll = float(df["bankroll_posle"].iloc[-1])

    if request.method == "POST":
        liga,mec,komentar = request.form["liga"],request.form["mec"],request.form["komentar"]
        proc,kurz,ishod = float(request.form["proc"]),float(request.form["kurz"]),request.form["ishod"]
        ulog = round(bankroll * proc / 100)
        profit = {"win":round(ulog*(kurz-1)),"loss":-ulog,"half":round(ulog*(kurz-1)/2),"void":0}[ishod]
        bankroll = round(bankroll + profit)
        with open(FILENAME,"a",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().strftime("%d.%m.%Y %H:%M"),liga,mec,komentar,proc,ulog,kurz,ishod,profit,bankroll])
        return redirect("/")

    return render_template_string(HTML, rows=rows, bankroll=bankroll)

if __name__ == "__main__":
    app.run()

    