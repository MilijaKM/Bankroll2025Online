# app.py – sa password zaštitom
import csv
from datetime import datetime
import pandas as pd
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = "ovo_je_tvoja_tajna_kljuc_12345"   # ne menjaj

FILENAME = "bankroll_history.csv"
PASSWORD = "kralj2025"      # ← OVO PROMENI U ŠTA HOĆEŠ (npr. tvoj nadimak+godina)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("logged_in") != True:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        else:
            return '<h1 style="color:red;text-align:center">Pogrešan password!</h1>'
    return '''
    <form method="post" style="text-align:center;margin-top:200px">
        <h1>🔒 BANKROLL 2025</h1>
        <input type="password" name="password" placeholder="Unesi password" style="padding:15px;font-size:20px;width:300px"><br><br>
        <button type="submit" style="padding:15px 30px;font-size:20px">Uloguj se</button>
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
        liga,mec,komentar = request.form["liga"],request.form["mec"],request.form["komentar"]
        proc,kurz,ishod = float(request.form["proc"]),float(request.form["kurz"]),request.form["ishod"]
        ulog = round(bankroll * proc / 100)
        profit = {"win":round(ulog*(kurz-1)),"loss":-ulog,"half":round(ulog*(kurz-1)/2),"void":0}[ishod]
        bankroll = round(bankroll + profit)
        with open(FILENAME,"a",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().strftime("%d.%m.%Y %H:%M"),liga,mec,komentar,proc,ulog,kurz,ishod,profit,bankroll])
        return redirect("/")

    HTML = f'''
    <h1><a href="/logout" style="float:right;font-size:16px;color:#aaa">Logout</a> BANKROLL {{ "%.0f" % bankroll }} Kč</h1>
    <!-- ostatak HTML-a je isti kao pre (grafikon + forma) -->
    <div id="graf" style="width:95%;height:500px;"></div>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
    var data=[{{x:[{% for r in rows %}"{{ r[0] }}",{% endfor %}], y:[{% for r in rows %}{{ r[9] }},{% endfor %}],
    type:'scatter', mode:'lines+markers', line:{{color:'#0f0',width:4}}}}];
    Plotly.newPlot('graf',data,{{title:'Vývoj bankrollu',paper_bgcolor:'#121212',plot_bgcolor:'#121212',font:{{color:'#0f0'}}}});
    </script>
    <h2>Nova oklada</h2><form method=post>
    <input name=liga placeholder="Liga" required><br>
    <input name=mec placeholder="Meč" required><br>
    <input name=komentar placeholder="Komentar"><br>
    <input name=proc type=number step=0.1 placeholder="% uloga" required><br>
    <input name=kurz type=number step=0.01 placeholder="Kurz" required><br>
    <select name=ishod><option>win</option><option>loss</option><option>half</option><option>void</option></select><br>
    <button>UNESI</button></form>
    <h2>Poslednjih 10</h2><table><tr><th>Datum</th><th>Liga</th><th>Meč</th><th>Ishod</th><th>Profit</th><th>Bankroll</th></tr>
    {% for r in rows[-10:] %}
    <tr class="{{ 'win' if r[7]=='win' else 'loss' if r[7]=='loss' else '' }}">
    <td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td><td>{{ r[7] }}</td><td>{{ "%.0f" % r[8] }}</td><td>{{ "%.0f" % r[9] }}</td></tr>
    {% endfor %}</table>
    '''
    return render_template_string(HTML, rows=rows, bankroll=bankroll)

if __name__ == "__main__":
    app.run()

    