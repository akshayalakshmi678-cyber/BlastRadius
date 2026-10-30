from flask import Flask, request, render_template_string
from analyzer import analyze_source

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB upload limit

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BlastRadius | Code Impact Analyzer</title>
<style>
:root{--bg:#0b1020;--panel:#141c31;--line:#293653;--text:#eaf0ff;--muted:#9aa8c7;--accent:#7dd3fc;--good:#86efac;--warn:#fcd34d}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top right,#17264a,#0b1020 48%);color:var(--text);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1120px;margin:auto;padding:32px 20px 60px}.top{display:flex;gap:14px;align-items:center;margin-bottom:24px}.logo{display:grid;place-items:center;width:48px;height:48px;border:1px solid #426080;border-radius:14px;background:#142743;color:var(--accent);font-size:24px;font-weight:800}
h1{margin:0;font-size:clamp(26px,4vw,38px);letter-spacing:-.04em}.subtitle{margin:3px 0 0;color:var(--muted)}.pill{display:inline-block;border:1px solid #426080;border-radius:999px;padding:4px 10px;color:var(--accent);font-size:12px;margin-top:8px}
.grid{display:grid;grid-template-columns:1.05fr .95fr;gap:18px}.card{background:rgba(20,28,49,.92);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 16px 40px #0002}
h2{font-size:18px;margin:0 0 12px}label{display:block;color:#c6d2eb;font-weight:650;margin:12px 0 7px}textarea,input[type=text]{width:100%;border:1px solid #344363;background:#0b1326;color:var(--text);border-radius:10px;padding:12px;font:13px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}textarea{min-height:300px;resize:vertical}input[type=text]{font:14px system-ui}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.btn{background:var(--accent);border:0;border-radius:10px;padding:11px 16px;color:#07111f;font-weight:800;cursor:pointer;margin-top:14px}.btn.secondary{background:#263752;color:var(--text);border:1px solid #3a4e70}.hint,.muted{color:var(--muted);font-size:13px}.metricrow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0}.metric{background:#0b1326;border:1px solid #263653;border-radius:12px;padding:12px}.metric strong{font-size:24px;display:block}.metric span{font-size:12px;color:var(--muted)}.section{margin-top:18px}.tag{display:inline-block;background:#1d3150;border:1px solid #345171;border-radius:7px;padding:3px 7px;margin:3px;font:12px ui-monospace,monospace}.ok{color:var(--good)}.warn{color:var(--warn)}.error{border:1px solid #854d4d;background:#351c28;color:#fecaca;border-radius:10px;padding:12px;margin:12px 0}.empty{color:var(--muted);padding:20px 0}.list{margin:0;padding-left:20px}.list li{margin:7px 0;overflow-wrap:anywhere}.footer{margin-top:22px;color:var(--muted);font-size:12px}
@media(max-width:800px){.grid{grid-template-columns:1fr}.metricrow{grid-template-columns:repeat(3,1fr)}}
</style>
</head>
<body><main>
<div class="top"><div class="logo">B</div><div><h1>BlastRadius</h1><p class="subtitle">Understand what a code change may affect.</p><span class="pill">STATIC ANALYSIS · PYTHON AST</span></div></div>
<div class="grid">
<section class="card">
<h2>Analyze Python source</h2>
<p class="muted">Paste code or upload a small .py file. Choose the function you plan to change.</p>
<form method="post" enctype="multipart/form-data">
<label for="target">Function to change</label><input id="target" name="target" type="text" placeholder="e.g. calculate_total" value="{{ target|e }}">
<label for="source">Python code</label><textarea id="source" name="source" spellcheck="false" placeholder="Paste Python code here...">{{ source }}</textarea>
<label for="file">Or upload a .py file (takes priority over pasted code)</label><input id="file" name="file" type="file" accept=".py,text/x-python">
<div class="row"><button class="btn" type="submit">Analyze impact →</button><button class="btn secondary" type="button" onclick="document.getElementById('source').value=document.getElementById('sample').textContent;document.getElementById('target').value='calculate_total'">Load sample</button></div>
</form>
<pre id="sample" hidden>def get_price(item):
    return item["price"]

def apply_discount(price, rate):
    return price * (1 - rate)

def calculate_total(item, rate):
    price = get_price(item)
    discounted = apply_discount(price, rate)
    return discounted

def checkout(cart):
    return [calculate_total(item, 0.1) for item in cart]

def send_receipt(total):
    print("Receipt:", total)

def finalize_order(cart):
    total = sum(calculate_total(item, 0.1) for item in cart)
    send_receipt(total)
    return total
</pre>
</section>
<section class="card">
<h2>Impact report</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
{% if report %}
<div class="metricrow">
<div class="metric"><strong>{{ report.function_count }}</strong><span>Functions found</span></div>
<div class="metric"><strong>{{ report.edge_count }}</strong><span>Call relationships</span></div>
<div class="metric"><strong>{{ report.affected|length }}</strong><span>Potentially affected</span></div>
</div>
<div class="section"><h2>Selected function</h2><span class="tag">{{ report.target }}</span>
{% if report.target_exists %}<p class="ok">Function found in source.</p>{% else %}<p class="warn">Function name was not found. Showing all discovered relationships.</p>{% endif %}</div>
<div class="section"><h2>Direct callers</h2>
{% if report.direct_callers %}{% for name in report.direct_callers %}<span class="tag">{{ name }}</span>{% endfor %}{% else %}<p class="muted">No direct callers found for this function.</p>{% endif %}</div>
<div class="section"><h2>Potential impact chain</h2>
{% if report.affected %}<ul class="list">{% for item in report.affected %}<li><strong>{{ item.name }}</strong> <span class="muted">— {{ item.reason }}</span></li>{% endfor %}</ul>{% else %}<p class="muted">No callers found in the analyzed source.</p>{% endif %}</div>
<div class="section"><h2>Detected function calls</h2>
{% if report.edges %}<ul class="list">{% for edge in report.edges %}<li><code>{{ edge.caller }}</code> → <code>{{ edge.callee }}</code></li>{% endfor %}</ul>{% else %}<p class="muted">No function calls detected.</p>{% endif %}</div>
<div class="section"><h2>Suggested checks</h2><ul class="list">{% for item in report.test_suggestions %}<li>{{ item }}</li>{% endfor %}</ul></div>
<div class="section"><h2>Analysis limitations</h2><p class="muted">This first version uses static AST analysis. It detects direct calls whose names appear in the source, but may miss dynamic dispatch, aliases, reflection, decorators, imported functions, and runtime-generated calls. Results are suggestions, not a guarantee of all affected code.</p></div>
{% else %}<p class="empty">Paste code, choose a function, and run an analysis to see the report here.</p>{% endif %}
</section></div>
<p class="footer">BlastRadius MVP · Source code is analyzed in memory and is not saved by this app. Use only code you are authorized to analyze.</p>
</main></body></html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    source = ""
    target = ""
    report = None
    error = None
    if request.method == "POST":
        source = request.form.get("source", "")
        target = request.form.get("target", "").strip()
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            if not uploaded.filename.lower().endswith(".py"):
                error = "Please upload a .py file."
            else:
                try:
                    source = uploaded.read(1_000_001).decode("utf-8")
                    if len(source) > 1_000_000:
                        error = "File is too large. Maximum size is 1 MB."
                except UnicodeDecodeError:
                    error = "File must be UTF-8 encoded Python source."
        if not error:
            if not source.strip():
                error = "Please paste code or upload a Python file."
            else:
                try:
                    report = analyze_source(source, target)
                except SyntaxError as exc:
                    error = f"Python syntax error near line {exc.lineno or '?'}: {exc.msg}"
    return render_template_string(PAGE, source=source, target=target, report=report, error=error)

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
