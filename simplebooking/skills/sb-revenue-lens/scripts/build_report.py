#!/usr/bin/env python3
"""
sb-revenue-lens — branded SimpleBooking report generator.

Turns an analysis JSON (produced by the lenses) into the approved branded
HTML layout: header, question, summary, demand/LOS charts (Chart.js),
per-lens signals with evidence tables + callouts, date/restriction calendar
map, limits block, events space, options.

Usage:
    python build_report.py input.json -o report.html

No external dependencies (stdlib only). Chart.js is loaded from a CDN in the
resulting file. See scripts/sample_hotel_d.json for the full input schema.
"""
import argparse, html, json, calendar as _cal

# --------------------------------------------------------------------------- CSS
CSS = """
:root{--navy:#0f2e4d;--navy2:#1b4f7a;--accent:#13a89e;--ink:#1f2a37;--muted:#64748b;
--line:#e4e9f0;--bg:#f6f8fb;--red:#e1485c;--orange:#f0992b;--yellow:#f4c542;--green:#2fa36b;--soft:#f0f4f9;}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg);line-height:1.5;font-size:15px}
.wrap{max-width:920px;margin:0 auto;background:#fff}
header{background:linear-gradient(120deg,var(--navy),var(--navy2));color:#fff;padding:30px 40px}
.brand{font-size:13px;letter-spacing:3px;text-transform:uppercase;opacity:.85}.brand b{font-weight:800}
header h1{margin:8px 0 4px;font-size:26px}header .meta{font-size:13px;opacity:.9;margin-top:10px}
header .pill{display:inline-block;background:rgba(255,255,255,.15);border-radius:20px;padding:3px 12px;margin:3px 6px 0 0;font-size:12px}
.pad{padding:26px 40px}
h2{font-size:14px;letter-spacing:1.5px;text-transform:uppercase;color:var(--navy2);border-bottom:2px solid var(--line);padding-bottom:6px;margin:34px 0 14px}
.lead{background:var(--soft);border-left:4px solid var(--accent);padding:14px 18px;border-radius:6px;font-size:16px}.lead b{color:var(--navy)}
.q{font-style:italic;color:var(--muted);margin:2px 0 0}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:14px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
th{background:#f1f5fa;color:var(--navy);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.tag{display:inline-block;border-radius:5px;padding:2px 9px;font-size:12px;font-weight:600;color:#fff}
.t-red{background:var(--red)}.t-or{background:var(--orange)}.t-gr{background:var(--green)}
.lens{border:1px solid var(--line);border-radius:10px;padding:6px 18px 16px;margin:14px 0}
.lens h3{color:var(--navy);font-size:16px;margin:14px 0 6px}.lens .rule{font-size:13px;color:var(--muted);margin:0 0 10px}
.chartbox{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px}
.two{display:flex;gap:16px;flex-wrap:wrap}.two .chartbox{flex:1;min-width:280px}
.cal{display:inline-block;width:48%;vertical-align:top;margin:0 1% 14px}.cal h4{margin:6px 0;color:var(--navy2);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px}
.grid div{aspect-ratio:1;display:flex;align-items:center;justify-content:center;border-radius:5px;font-size:12px;background:#eef2f7;color:#4b5563}
.grid .dow{background:transparent;color:#94a3b8;font-size:10px;font-weight:700}
.grid .past{background:#f3f4f6;color:#cbd5e1}
.grid .y{background:var(--yellow);color:#5b4708;font-weight:700}
.grid .or{background:var(--orange);color:#fff;font-weight:700}
.grid .red{background:var(--red);color:#fff;font-weight:700}
.grid .gr{background:var(--green);color:#fff;font-weight:700}
.legend span{display:inline-block;margin-right:14px;font-size:12px;color:var(--muted)}
.dot{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:middle;margin-right:4px}
.limits{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:14px 18px;font-size:13px}.limits b{color:#b45309}
.ev{background:#eef7f6;border:1px dashed var(--accent);border-radius:10px;padding:14px 18px;font-size:14px}
.opts{font-size:14px}.opts li{margin:4px 0}
.callout{background:#fef2f4;border:1px solid #f5c2cb;border-radius:10px;padding:14px 18px}.callout b{color:#b3344a}
footer{background:var(--navy);color:#c8d6e5;font-size:12px;padding:18px 40px;text-align:center}
.small{font-size:12px;color:var(--muted)}
"""

def esc(s): return html.escape(str(s), quote=True)

def cell(c):
    """A table cell: a plain string or {'tag':'t-or','text':'...'}."""
    if isinstance(c, dict):
        return f'<span class="tag {esc(c.get("tag",""))}">{esc(c.get("text",""))}</span>'
    return esc(c)

def table(headers, rows):
    out = ['<table><tr>'] + [f'<th>{esc(h)}</th>' for h in headers] + ['</tr>']
    for r in rows:
        out.append('<tr>' + ''.join(f'<td>{cell(c)}</td>' for c in r) + '</tr>')
    out.append('</table>')
    return ''.join(out)

def pills(items): return ''.join(f'<span class="pill">{esc(p)}</span>' for p in items)

def lens_block(l):
    h = [f'<div class="lens"><h3>{esc(l["title"])}</h3>']
    if l.get('rule'): h.append(f'<p class="rule">{esc(l["rule"])}</p>')
    if l.get('table'): h.append(table(l['table']['headers'], l['table']['rows']))
    if l.get('callout'): h.append(f'<div class="callout">{l["callout"]}</div>')  # HTML allowed
    if l.get('note'): h.append(f'<p class="small">{l["note"]}</p>')              # HTML allowed
    h.append('</div>')
    return ''.join(h)

def calendar_grid(cal_id, year, month, colors):
    """colors: {day(int): class('red'|'or'|'y'|'gr'|'past')}. first_dow/days computed."""
    first_weekday, days = _cal.monthrange(year, month)  # Mon=0
    first_dow = first_weekday + 1                        # 1..7
    out = [f'<div class="grid" id="{cal_id}">']
    for d in ['M','T','W','T','F','S','S']:
        out.append(f'<div class="dow">{d}</div>')
    for _ in range(1, first_dow):
        out.append('<div></div>')
    for d in range(1, days+1):
        cls = colors.get(str(d), colors.get(d, ''))
        out.append(f'<div class="{cls}">{d}</div>')
    out.append('</div>')
    return ''.join(out)

def legend(items):
    sp = ''.join(f'<span><i class="dot" style="background:{c}"></i>{esc(t)}</span>' for t, c in items)
    return f'<div class="legend" style="margin-bottom:10px">{sp}</div>'

def chart_js(canvas_id, labels, values, label, color_rule=None, title=None):
    """color_rule: list of (threshold, color) in descending order; below -> last color."""
    import json as _j
    colors_js = "ctx=>{const v=ctx.raw;" + "".join(
        f"if(v>={t})return '{c}';" for t, c in (color_rule or [])
    ) + ("return '#9bd3cd';}" if color_rule else "return '#1b4f7a';}")
    t = f",title:{{display:true,text:{_j.dumps(title)}}}" if title else ""
    return f"""
new Chart(document.getElementById('{canvas_id}'),{{
 type:'bar',
 data:{{labels:{_j.dumps(labels)},datasets:[{{label:{_j.dumps(label)},
   data:{_j.dumps(values)},backgroundColor:{colors_js},borderRadius:5}}]}},
 options:{{plugins:{{legend:{{display:false}}{t}}},
   scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>v>=1000?v/1000+'k':v}}}}}}}}
}});"""

def build(data):
    P, scripts = [], []
    P.append(f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">')
    P.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    P.append(f'<title>SimpleBooking · Revenue Lens — {esc(data["hotel_name"])}</title>')
    P.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>')
    P.append(f'<style>{CSS}</style></head><body><div class="wrap">')

    # header
    P.append('<header><div class="brand"><b>Simple</b>Booking · Revenue Lens</div>')
    P.append(f'<h1>{esc(data["hotel_name"])}{(" " + esc(data["stars"])) if data.get("stars") else ""}</h1>')
    P.append(f'<div class="meta">{pills(data.get("pills", []))}</div></header>')
    P.append('<div class="pad">')

    # the question
    P.append('<h2>The question</h2>')
    P.append(f'<p class="q">"{esc(data["question"])}"</p>')
    if data.get('lenses_active'):
        P.append(f'<p class="small">Triggered lenses: {data["lenses_active"]}</p>')

    # summary
    P.append('<h2>Summary</h2>')
    P.append(f'<div class="lead">{data["summary"]}</div>')  # HTML allowed

    # period overview + charts
    P.append('<h2>Period overview — destination demand</h2>')
    charts = data.get('charts', {})
    if charts.get('los'):
        P.append('<div class="two"><div class="chartbox"><canvas id="demand" height="170"></canvas></div>')
        P.append('<div class="chartbox"><canvas id="los" height="170"></canvas></div></div>')
    else:
        P.append('<div class="chartbox"><canvas id="demand" height="150"></canvas></div>')
    if charts.get('caption'):
        P.append(f'<p class="small">{charts["caption"]}</p>')
    dm = charts['demand']
    scripts.append(chart_js('demand', dm['labels'], dm['values'], dm.get('label','Searches / week'),
                            dm.get('color_rule'), dm.get('title')))
    if charts.get('los'):
        lo = charts['los']
        scripts.append(chart_js('los', lo['labels'], lo['values'], lo.get('label','Searches per LOS'),
                                lo.get('color_rule'), lo.get('title')))

    # signals per lens
    P.append('<h2>Signals per lens</h2>')
    for l in data.get('lenses', []):
        P.append(lens_block(l))

    # date map
    dmap = data.get('date_map')
    if dmap:
        P.append(f'<h2>{esc(dmap.get("heading","Date map"))}</h2>')
        P.append(legend(dmap['legend']))
        for c in dmap['calendars']:
            P.append(f'<div class="cal"><h4>{esc(c["title"])}</h4>')
            P.append(calendar_grid(c['id'], c['year'], c['month'], c['colors']))
            P.append('</div>')
        if dmap.get('note'):
            P.append(f'<p class="small">{dmap["note"]}</p>')

    # limits
    P.append('<h2>What this analysis does NOT see</h2>')
    P.append(f'<div class="limits">{data["limits"]}</div>')  # HTML allowed

    # events
    if data.get('events'):
        P.append('<h2>Events — over to the hotel</h2>')
        P.append(f'<div class="ev">{data["events"]}</div>')

    # options
    if data.get('options'):
        P.append('<h2>Next steps (options)</h2><ul class="opts">')
        for o in data['options']:
            P.append(f'<li>{o}</li>')  # HTML allowed
        P.append('</ul>')

    P.append('</div>')  # .pad
    P.append(f'<footer>{esc(data.get("footer","SimpleBooking · Revenue Lens — generated by sb-revenue-lens · SimpleBooking MCP data"))}</footer>')
    P.append('</div>')  # .wrap
    P.append('<script>' + '\n'.join(scripts) + '</script>')
    P.append('</body></html>')
    return ''.join(P)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='analysis JSON')
    ap.add_argument('-o', '--output', default='report.html')
    a = ap.parse_args()
    with open(a.input, encoding='utf-8') as f:
        data = json.load(f)
    htmlout = build(data)
    with open(a.output, 'w', encoding='utf-8') as f:
        f.write(htmlout)
    print(f'Report written to {a.output} ({len(htmlout)} bytes)')

if __name__ == '__main__':
    main()
