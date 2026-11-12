"""
Build the project 11 website: docs/index.html

It shows interactive (plotly) versions of the graphs from
notebooks/11_mars_organics_prototype.ipynb, each with a plain-language
explanation. GitHub Pages can publish the docs/ folder as a website.

Run it from the repo root:
    python3 website/build_website.py

Data: NASA Planetary Data System (Curiosity SAM experiment 25387) and the
NIST Chemistry WebBook. Downloads are cached in data/ (never committed).
"""
from pathlib import Path
import html
import re

import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import get_plotlyjs_version

AUTHOR = ''   # put your name here to show "by <name>" at the top of the page
REPO_URL = 'https://github.com/JadaPL/astro85'

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
OUT = ROOT / 'docs' / 'index.html'

# Colors: the same one-color-per-mass scheme as the notebook
COLORS = {78: '#2a78d6', 91: '#eb6834', 50: '#1baf7a', 77: '#eda100',
          92: '#e87ba4', 112: '#008300', 69: '#6250d6', 127: '#e34948'}
NAMES = {78: "m/z 78 · benzene's weight", 91: "m/z 91 · toluene's main piece", 50: 'm/z 50',
         77: 'm/z 77 · benzene piece', 92: "m/z 92 · toluene's weight", 112: "m/z 112 · chlorobenzene's weight",
         69: 'm/z 69 · mystery substance', 127: 'm/z 127 · mystery substance'}
INK, INK2, GRAY, GRID, AXIS, SHADE = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#f0efec'


# ---------------------------------------------------------------------------
# 1. Download (once) and load the data, exactly as in the notebook
# ---------------------------------------------------------------------------
EID, SOL = 25387, 1546
PDS = f'https://pds-geosciences.wustl.edu/msl/msl-m-sam-2-rdr-l0-v1/mslsam_1xxx/data/eid{EID}/'
FILES = {
    'mass_spec':  f'level1b/sm{EID}f{SOL}rdr1b_spyr_qms_massdtc_2.tab',
    'gc_notes':   f'level2/sm{EID}f{SOL}rdr2__spyr_gc__notesxx_2.txt',
    'gc_species': f'level2/sm{EID}f{SOL}rdr2__spyr_gc__species_2.csv',
}


def download(url, save_as):
    # Download a file once and keep it; later runs reuse the saved copy.
    save_as = Path(save_as)
    if not save_as.exists():
        save_as.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        save_as.write_bytes(response.content)
        print('downloaded', save_as.name)
    return save_as


local = {key: download(PDS + path, DATA / f'sam_eid{EID}' / path) for key, path in FILES.items()}

ms = pd.read_csv(local['mass_spec'], skipinitialspace=True, header=0,
                 names=['time', 'mass', 'oven_T', 'gc_T', 'cps'], usecols=range(5))
ms['cps'] = pd.to_numeric(ms['cps'], errors='coerce')
ms['minutes'] = (ms['time'] - ms['time'].min()) / 60
ms = ms[ms['mass'] % 1 == 0].copy()          # whole-number masses only
t0 = ms['time'].min()

# The team's results: GC start times, peak list and peak sizes
notes = local['gc_notes'].read_text()
gc_start = {int(c): float(t) for t, c in re.findall(r'([\d.]+) s \(sclk\) for GC (\d)', notes)}
rows, column = [], None
for line in notes.splitlines():
    if line.startswith('GC column'):
        column = int(line.split()[2])
    match = re.match(r'peak (\d+) ;(.*);\s*(\d+)', line)
    if match:
        rows.append({'peak': int(match[1]), 'team_name': match[2].strip(),
                     'gc_column': column, 'team_time_s': float(match[3])})
team = pd.DataFrame(rows)
sizes = pd.read_csv(local['gc_species'])
sizes['peak'] = sizes['SPECIES'].str.replace('Peak ', '').astype(int)
team = team.merge(sizes[['peak', 'ABUNDANCE']], on='peak').rename(columns={'ABUNDANCE': 'team_area'})
team['event'] = team['team_name'].str.contains('INJECTION|FLASH')

RUN_LENGTH = {1: 2100, 4: 1500}
WINDOW = {1: 15, 4: 8}


def gc_run(column):
    start = gc_start[column]
    run = ms[(ms['time'] >= start - 60) & (ms['time'] <= start + RUN_LENGTH[column])].copy()
    run['rt'] = run['time'] - start
    return run


runs = {column: gc_run(column) for column in gc_start}


def spectrum_at(column, time_s):
    run = runs[column]
    near = run[(run['rt'] - time_s).abs() <= WINDOW[column]]
    before = run[(run['rt'] >= time_s - 60) & (run['rt'] <= time_s - 20)]
    spectrum = near.groupby('mass')['cps'].max() - before.groupby('mass')['cps'].median()
    return spectrum.dropna().clip(lower=0)


def nist_spectrum(nist_id):
    url = f'https://webbook.nist.gov/cgi/cbook.cgi?JCAMP={nist_id}&Index=0&Type=Mass'
    text = download(url, DATA / 'nist' / f'{nist_id}.jdx').read_text()
    table = text.split('##PEAK TABLE=(XY..XY)')[1].split('##END')[0]
    return pd.Series({int(m): float(i) for m, i in re.findall(r'(\d+),(\d+)', table)})


REFERENCE = {'benzene': nist_spectrum('C71432'), 'toluene': nist_spectrum('C108883')}


def similarity(a, b, lightest=35):
    masses = sorted(m for m in set(a.index) | set(b.index) if m >= lightest)
    x = a.reindex(masses, fill_value=0).to_numpy()
    y = b.reindex(masses, fill_value=0).to_numpy()
    return float(x @ y / np.sqrt((x @ x) * (y @ y)))


# Compare every peak in the team's table with the raw data
comparison = []
for _, p in team[~team['event']].iterrows():
    column, team_time = p['gc_column'], p['team_time_s']
    spectrum = spectrum_at(column, team_time)
    heavy = spectrum[spectrum.index >= 45]
    strongest = heavy.idxmax()
    run = runs[column]
    near = run[(run['mass'] == strongest) & ((run['rt'] - team_time).abs() <= WINDOW[column])]
    our_time = near.loc[near['cps'].idxmax(), 'rt']
    comparison.append({'peak': p['peak'], 'column': column, 'name': p['team_name'].title(),
                       'team_time': team_time, 'our_time': round(our_time, 1),
                       'difference': round(our_time - team_time, 1),
                       'masses': ', '.join(str(int(m)) for m in heavy.nlargest(3).index),
                       'benzene': round(similarity(spectrum, REFERENCE['benzene']), 2),
                       'toluene': round(similarity(spectrum, REFERENCE['toluene']), 2),
                       'spectrum': spectrum})
comparison = pd.DataFrame(comparison)
scan_time = {c: runs[c].loc[runs[c]['mass'] == 78, 'rt'].diff().median() for c in runs}
within = int((comparison['difference'].abs() <= comparison['column'].map(scan_time)).sum())


def peak_area(column, mass, time_s, before=20, after=40):
    run = runs[column]
    used = run[(run['mass'] == mass) & (run['rt'] >= time_s - before) & (run['rt'] <= time_s + after)]
    return np.trapezoid(used['cps'], used['rt']), used


# ---------------------------------------------------------------------------
# 2. The interactive figures
# ---------------------------------------------------------------------------
def tidy(fig, height):
    # The same calm look for every chart: light gridlines, readable fonts, legend on top
    fig.update_layout(template='plotly_white', height=height, margin=dict(l=70, r=24, t=56, b=56),
                      font=dict(family='system-ui, -apple-system, Segoe UI, sans-serif', size=14, color=INK),
                      legend=dict(orientation='h', x=0, y=1.02, yanchor='bottom'),
                      hoverlabel=dict(font_size=13), paper_bgcolor='white', plot_bgcolor='white')
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False)
    return fig


def overview_figure():
    oven_peak = ms.loc[ms['oven_T'].idxmax()]
    heating = ms[ms['minutes'] <= oven_peak['minutes']].iloc[::200]   # every 200th reading is plenty
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.3, 0.7], vertical_spacing=0.05)
    fig.add_trace(go.Scatter(x=heating['minutes'].round(2), y=heating['oven_T'].round(1), name='Oven temperature',
                             line=dict(color=INK2, width=2), showlegend=False,
                             hovertemplate='minute %{x:.1f}<br>oven %{y:.0f} °C<extra></extra>'), row=1, col=1)
    for mass in (78, 91):
        trace = ms[(ms['mass'] == mass) & (ms['cps'] > 0)].copy()
        trace.loc[trace['time'].diff() > 60, 'cps'] = np.nan     # break the line at gaps in the data
        fig.add_trace(go.Scatter(x=trace['minutes'].round(3), y=trace['cps'].round(0), name=NAMES[mass],
                                 line=dict(color=COLORS[mass], width=1.2),
                                 hovertemplate='minute %{x:.1f}<br>%{y:,.0f} counts/s<extra>m/z ' + str(mass) + '</extra>'),
                      row=2, col=1)
    stages = [('Oven heats the rock', 0, oven_peak['minutes']),
              ('Sorting run 1 (tube 1)', (gc_start[1] - t0) / 60, (gc_start[1] - t0 + RUN_LENGTH[1]) / 60),
              ('Sorting run 2 (tube 4)', (gc_start[4] - t0) / 60, ms['minutes'].max())]
    for name, start, end in stages:
        fig.add_vrect(x0=start, x1=end, fillcolor=SHADE, line_width=0, layer='below', row='all', col=1)
        fig.add_annotation(x=(start + end) / 2, y=1.0, xref='x', yref='paper', yanchor='bottom',
                           text=name, showarrow=False, font=dict(color=INK2, size=13))
    fig.update_yaxes(title_text='Oven (°C)', row=1, col=1)
    fig.update_yaxes(title_text='Counts per second', type='log', dtick=1, row=2, col=1)   # gridlines at 1000, 10k, 100k...
    fig.update_xaxes(title_text='Minutes since the start of the experiment', row=2, col=1)
    tidy(fig, 560)
    fig.update_layout(legend=dict(y=-0.2, yanchor='top'), margin=dict(t=40, b=90))
    return fig


def chromatogram_figure(column):
    run = runs[column]
    fig = go.Figure()
    shown_by_default = (50, 78, 91)
    for mass in (78, 91, 50, 77, 92, 112, 69, 127):
        trace = run[run['mass'] == mass]
        fig.add_trace(go.Scatter(x=trace['rt'].round(1), y=(trace['cps'] / 1e6).round(4), name=NAMES[mass],
                                 line=dict(color=COLORS[mass], width=1.8),
                                 visible=True if mass in shown_by_default else 'legendonly',
                                 hovertemplate='%{x:.0f} s<br>%{y:.3f} million counts/s<extra>m/z ' + str(mass) + '</extra>'))
    # The team's peaks: triangles with numbers, staggered where peaks are close together
    top = run.loc[run['mass'].isin(shown_by_default), 'cps'].max() / 1e6 * 1.05
    details = comparison.set_index('peak')
    xs, ys, labels, hovers, level, last = [], [], [], [], 0, -1e9
    for _, p in team[team['gc_column'] == column].sort_values('team_time_s').iterrows():
        level = level + 1 if p['team_time_s'] - last < 30 else 0
        last = p['team_time_s']
        xs.append(p['team_time_s'])
        ys.append(top * (1 + 0.11 * level))
        named = p['team_name'] != '' and not p['event']
        labels.append(f"<b>{p['peak']} {p['team_name'].title()}</b>" if named else str(p['peak']))
        if p['event']:
            hovers.append(f"<b>Peak {p['peak']}</b>: instrument event, not a chemical<br>"
                          f"({p['team_name'].title()}: gas pushed into the tube)")
        else:
            d = details.loc[p['peak']]
            hovers.append(f"<b>Peak {p['peak']}</b> {('· ' + d['name']) if d['name'] else '· no name from NASA'}<br>"
                          f"NASA's time: {d['team_time']:.0f} s · our time: {d['our_time']:.1f} s<br>"
                          f"strongest masses: {d['masses']}<br>"
                          f"looks like benzene: {d['benzene']:.2f} · toluene: {d['toluene']:.2f}")
    fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers+text', text=labels, textposition='top center',
                             marker=dict(symbol='triangle-down', size=11, color=GRAY),
                             textfont=dict(size=12, color=INK2), name="NASA's numbered peaks",
                             hovertext=hovers, hovertemplate='%{hovertext}<extra></extra>'))
    fig.update_yaxes(title_text='Counts per second (millions)', range=[0, top * 1.55])
    fig.update_xaxes(title_text='Seconds since the gas entered the tube', range=[-40, RUN_LENGTH[column]])
    tidy(fig, 520)
    fig.update_layout(legend=dict(y=-0.18, yanchor='top'), margin=dict(t=20, b=110))
    return fig


def mirror_figure():
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=[f'Peak 13 vs. benzene: similarity {comparison.set_index("peak").loc[13, "benzene"]:.2f}',
                                        f'Peak 14 vs. toluene: similarity {comparison.set_index("peak").loc[14, "toluene"]:.2f}'])
    for col, (peak, molecule, mass) in enumerate([(13, 'benzene', 78), (14, 'toluene', 91)], start=1):
        measured = comparison.set_index('peak').loc[peak, 'spectrum']
        measured = measured[(measured.index >= 10) & (measured.index <= 135)]
        measured = 100 * measured / measured.max()
        reference = 100 * REFERENCE[molecule] / REFERENCE[molecule].max()
        fig.add_trace(go.Bar(x=measured.index, y=measured.round(1), marker_color=COLORS[mass], width=0.8,
                             name=f'Curiosity, peak {peak}',
                             hovertemplate='mass %{x}: %{y:.0f}% of the tallest bar<extra>Curiosity</extra>'), row=1, col=col)
        fig.add_trace(go.Bar(x=reference.index, y=-reference.round(1), customdata=reference.round(1), marker_color=GRAY,
                             width=0.8, name=f'NIST lab: {molecule}',
                             hovertemplate='mass %{x}: %{customdata:.0f}% of the tallest bar<extra>NIST lab</extra>'), row=1, col=col)
        fig.add_vrect(x0=10, x1=35, fillcolor=SHADE, line_width=0, layer='below', row=1, col=col)
        fig.update_xaxes(title_text='Mass (m/z)', range=[10, 135], row=1, col=col)
    fig.update_yaxes(title_text='Measured ↑   ·   lab ↓', range=[-112, 112],
                     tickvals=[-100, -50, 0, 50, 100], ticktext=['100', '50', '0', '50', '100'], row=1, col=1)
    tidy(fig, 460)
    fig.update_layout(barmode='overlay', bargap=0, legend=dict(y=-0.25, yanchor='top'), margin=dict(t=60, b=110))
    return fig


def explorer_figure():
    # One bar chart per peak; a dropdown picks which one is visible
    fig = go.Figure()
    buttons = []
    start = comparison.index[comparison['peak'] == 13][0]
    for i, d in comparison.iterrows():
        spectrum = d['spectrum']
        spectrum = spectrum[(spectrum.index >= 10) & (spectrum.index <= 160)]
        spectrum = 100 * spectrum / spectrum.max()
        fig.add_trace(go.Bar(x=spectrum.index, y=spectrum.round(1), width=0.8, marker_color=COLORS[78],
                             visible=(i == start), showlegend=False,
                             hovertemplate='mass %{x}: %{y:.0f}% of the tallest bar<extra></extra>'))
        visible = [j == i for j in range(len(comparison))]
        buttons.append(dict(label=f"Peak {d['peak']}" + (f" · {d['name']}" if d['name'] else ''),
                            method='update', args=[{'visible': visible}, {'title.text': explorer_title(d)}]))
    # Title (two lines) at the very top, the dropdown menu just above the chart
    fig.update_layout(updatemenus=[dict(buttons=buttons, active=int(start), x=0, xanchor='left', y=1.04, yanchor='bottom',
                                        bgcolor='white', bordercolor=AXIS)],
                      title=dict(text=explorer_title(comparison.loc[start]), x=0.01, xanchor='left',
                                 y=0.98, yanchor='top', font=dict(size=14)))
    fig.update_xaxes(title_text='Mass (m/z)', range=[10, 160])
    fig.update_yaxes(title_text='% of the tallest bar', range=[0, 105])
    tidy(fig, 480)
    fig.update_layout(margin=dict(t=140, b=56))
    return fig


def explorer_title(d):
    name = d['name'] if d['name'] else 'no name from NASA'
    return (f"<b>Peak {d['peak']}</b> · {name} · tube {d['column']}, {d['team_time']:.0f} s<br>"
            f"looks like benzene: {d['benzene']:.2f} · looks like toluene: {d['toluene']:.2f}")


def areas_figure():
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08,
                        subplot_titles=['Peak 13, benzene (m/z 78)', 'Peak 14, toluene (m/z 91)'])
    results = []
    for col, (peak, molecule, mass) in enumerate([(13, 'benzene', 78), (14, 'toluene', 91)], start=1):
        p = team.set_index('peak').loc[peak]
        area, used = peak_area(4, mass, p['team_time_s'])
        run = runs[4]
        around = run[(run['mass'] == mass) & run['rt'].between(p['team_time_s'] - 40, p['team_time_s'] + 80)]
        fig.add_trace(go.Scatter(x=used['rt'].round(1), y=(used['cps'] / 1e6).round(4), fill='tozeroy', mode='none',
                                 fillcolor='rgba(42,120,214,0.18)' if mass == 78 else 'rgba(235,104,52,0.18)',
                                 name='area we add up', showlegend=(col == 1), hoverinfo='skip'), row=1, col=col)
        fig.add_trace(go.Scatter(x=around['rt'].round(1), y=(around['cps'] / 1e6).round(4), mode='lines+markers',
                                 line=dict(color=COLORS[mass], width=1.8), marker=dict(size=8), name=NAMES[mass],
                                 hovertemplate='%{x:.1f} s<br>%{y:.3f} million counts/s<extra>one measurement</extra>'),
                      row=1, col=col)
        axis = '' if col == 1 else str(col)     # plotly calls the first subplot's axes "x" and "y"
        fig.add_annotation(x=0.98, y=0.6, xref=f'x{axis} domain', yref=f'y{axis} domain', xanchor='right', showarrow=False,
                           align='right', text=f"our area: {area / 1e6:.1f} million<br>NASA's area: {p['team_area'] / 1e6:.1f} million",
                           font=dict(color=INK, size=14))
        fig.update_xaxes(title_text='Seconds since the gas entered the tube', row=1, col=col)
        results.append((molecule, area / p['team_area']))
    fig.update_yaxes(title_text='Counts per second (millions)', row=1, col=1)
    tidy(fig, 420)
    fig.update_layout(legend=dict(y=-0.28, yanchor='top'), margin=dict(t=60, b=110))
    return fig, results


# ---------------------------------------------------------------------------
# 3. The web page
# ---------------------------------------------------------------------------
CONFIG = {'displaylogo': False, 'responsive': True,
          'modeBarButtonsToRemove': ['lasso2d', 'select2d']}


def chart(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CONFIG)


areas_fig, area_ratio = areas_figure()
benzene_score = comparison.set_index('peak').loc[13, 'benzene']
toluene_score = comparison.set_index('peak').loc[14, 'toluene']
ratio = dict(area_ratio)

table_rows = []
for _, d in comparison.iterrows():
    row_start = '<tr class="named">' if d['name'] else '<tr>'
    name = html.escape(d['name']) if d['name'] else '–'
    table_rows.append(f"{row_start}<td>{d['peak']}</td><td>{d['column']}</td><td>{name}</td>"
                      f"<td>{d['team_time']:.0f}</td><td>{d['our_time']:.1f}</td><td>{(d['difference'] or 0.0):+.1f}</td>"
                      f"<td>{d['masses']}</td><td>{d['benzene']:.2f}</td><td>{d['toluene']:.2f}</td></tr>")
table_rows = '\n'.join(table_rows)

byline = f' · by {html.escape(AUTHOR)}' if AUTHOR else ''

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Benzene on Mars</title>
<meta name="description" content="Checking NASA's chemistry results with the Curiosity rover's raw data: interactive graphs with plain-language explanations.">
<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" charset="utf-8"></script>
<style>
  :root {{ color-scheme: light; --ink: #1e1b24; --body: #4a4550; --muted: #6b6570; --accent: #b5410f;
          --page: #fbfaf7; --card: #ffffff; --sand: #f1ece4; --line: #e2dbd0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--page); color: var(--body);
         font: 17px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  header {{ background: #1e1b24; color: #f4efe9; padding: 56px 16px 48px; }}
  header .wrap, main {{ max-width: 1040px; margin: 0 auto; }}
  main {{ padding: 8px 16px 64px; }}
  .eyebrow {{ font-size: 13px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #e8794a; margin: 0 0 8px; }}
  h1 {{ font-size: clamp(40px, 7vw, 72px); line-height: 1.05; margin: 0 0 16px; letter-spacing: -1px; }}
  header p.sub {{ font-size: 20px; color: #cfc8d6; margin: 0; max-width: 720px; }}
  h2 {{ color: var(--ink); font-size: 28px; line-height: 1.2; margin: 56px 0 8px; }}
  h2 .num {{ color: var(--accent); }}
  h3 {{ color: var(--ink); font-size: 18px; margin: 20px 0 4px; }}
  p {{ margin: 0 0 12px; max-width: 760px; }}
  .tip {{ background: var(--sand); border-radius: 12px; padding: 16px 20px; margin: 32px 0 0; }}
  .tip b {{ color: var(--ink); }}
  .steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 16px 0; }}
  .step {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px 20px; }}
  .step b {{ color: var(--accent); font-size: 22px; }}
  .chart {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 8px; margin: 16px 0; overflow: hidden; }}
  .result {{ border-left: 4px solid var(--accent); padding: 4px 0 4px 16px; margin: 16px 0; }}
  .big {{ display: flex; flex-wrap: wrap; gap: 16px; margin: 16px 0; }}
  .big div {{ flex: 1 1 200px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px 20px; }}
  .big strong {{ display: block; color: var(--accent); font-size: 36px; line-height: 1.1; }}
  .table-wrap {{ overflow-x: auto; background: var(--card); border: 1px solid var(--line); border-radius: 12px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 15px; font-variant-numeric: tabular-nums; }}
  th, td {{ padding: 8px 12px; text-align: right; border-bottom: 1px solid var(--line); white-space: nowrap; }}
  th:nth-child(3), td:nth-child(3), th:nth-child(7), td:nth-child(7) {{ text-align: left; }}
  th {{ color: var(--ink); background: var(--sand); position: sticky; top: 0; }}
  tr.named td {{ color: var(--ink); font-weight: 600; }}
  ul {{ max-width: 760px; padding-left: 22px; }}
  li {{ margin-bottom: 6px; overflow-wrap: anywhere; }}   /* long links and file names wrap on phones */
  a {{ color: #1c5cab; }}
  footer {{ color: var(--muted); font-size: 14px; border-top: 1px solid var(--line); margin-top: 56px; padding-top: 16px; }}
</style>
</head>
<body>
<header><div class="wrap">
  <p class="eyebrow">CS85 · Project 11{byline}</p>
  <h1>Benzene on Mars</h1>
  <p class="sub">Checking NASA’s chemistry results with the Curiosity rover’s raw data. Every graph on this page is interactive.</p>
</div></header>
<main>

<div class="tip"><b>How to use the graphs:</b> hover over a line or bar to see its numbers · drag across a graph to zoom in ·
double-click to zoom back out · click a name in a legend to hide or show that line.</div>

<h2>The question</h2>
<p>Living things on Earth are built from carbon-based chemicals, which chemists call <i>organic</i> molecules. Mars once had
liquid water, so scientists want to know whether its old rocks contain carbon-based chemicals too. Finding them would
<b>not</b> mean Mars had life (flour and sugar are ingredients, not a cake), but it tells us whether the raw materials were there.</p>
<p>NASA publishes the rover’s raw measurements online. This project takes one experiment, rebuilds NASA’s results from
those raw numbers, and checks whether they match what NASA’s science team reported.</p>

<h2>How the rover’s lab works</h2>
<p>Curiosity carries a small chemistry lab called SAM (Sample Analysis at Mars). It works in three steps:</p>
<div class="steps">
  <div class="step"><b>1 · Bake</b><br>Rock powder goes into a tiny oven. Heating it releases gases.</div>
  <div class="step"><b>2 · Sort</b><br>The gases race through a long, thin tube, so each chemical comes out at its own time. This is called <i>gas chromatography</i>.</div>
  <div class="step"><b>3 · Weigh</b><br>Each chemical is broken into pieces that are weighed. The pattern of weights is its fingerprint. This is called <i>mass spectrometry</i>.</div>
</div>
<p>The weights are written as <b>m/z</b> numbers. A whole benzene molecule weighs 78, so benzene shows up strongly at m/z 78.
Toluene, a close relative of benzene, breaks mostly into a piece that weighs 91.</p>

<h2><span class="num">Graph 1</span> · The whole experiment</h2>
<h3>What you’re looking at</h3>
<p>A timeline of the whole four-hour experiment. The top panel is the oven temperature: the rock is baked up to 831 °C.
The bottom panel shows how much of two weights the instrument detected: blue is 78 (benzene) and orange is 91 (toluene).
Higher means more. The scale goes up 10 times at each gridline, so small and huge signals both fit. The gray bands are
the three stages: baking, then two sorting runs through two different tubes. Gaps in the lines are times with no data.</p>
<div class="chart">{chart(overview_figure())}</div>
<h3>What it tells us</h3>
<p>This is the map of the experiment. The tall, thin spikes on the right are single chemicals coming out of the second tube,
and that’s where NASA’s team found benzene and toluene. Try dragging across the spikes to zoom in.</p>

<h2><span class="num">Graph 2</span> · The sorting runs (chromatograms)</h2>
<h3>What you’re looking at</h3>
<p>A zoom into each sorting run, rebuilt from the raw numbers. Left to right is the number of seconds since the gas entered
the tube. Each bump is one chemical coming out, like a runner crossing a finish line. The gray triangles with numbers are
the bumps on NASA’s own list: <b>hover over a triangle</b> to see NASA’s time, our time and the bump’s fingerprint scores.
More weights are hidden in the legend below each graph: click them to switch them on.</p>
<h3>Sorting run 1 (tube 1)</h3>
<div class="chart">{chart(chromatogram_figure(1))}</div>
<h3>Sorting run 2 (tube 4), where NASA named benzene and toluene</h3>
<div class="chart">{chart(chromatogram_figure(4))}</div>
<h3>What it tells us</h3>
<p>The bumps in the raw data sit in the same places as on NASA’s list. Bump 13 is benzene and bump 14 is toluene, the only
two the team named.</p>
<div class="result"><b>{within} of {len(comparison)}</b> of NASA’s bumps show up in the raw data at the same moment, to within
one measurement (the instrument measures each weight only every {scan_time[4]:.1f} to {scan_time[1]:.1f} seconds). The others
are wide or overlapping bumps that are hard to pin down. The full list is in the table further down.</div>

<h2><span class="num">Graph 3</span> · Chemical fingerprints</h2>
<h3>What you’re looking at</h3>
<p>Each bar is one weight that a chemical breaks into, and its height is how many pieces of that weight were counted. The top
half is what Curiosity measured at a bump. The bottom half, flipped upside down, is the same chemical measured in a lab on
Earth by NIST, the US standards agency. If the bars line up, it’s the same chemical. The similarity score runs from 0
(nothing in common) to 1 (the same pattern). Weights below 35 (the gray band) are left out of the score, because air and
water are always in the instrument.</p>
<div class="chart">{chart(mirror_figure())}</div>
<h3>What it tells us</h3>
<p><b>Benzene (left):</b> the bars line up almost perfectly, a score of {benzene_score:.2f}. This bump really is benzene.<br>
<b>Toluene (right):</b> toluene’s own bars, 91 and 92, are there. But the tallest bars, 15 and 69, are not toluene: a second,
unidentified chemical came out of the tube at the same moment, so the score is only {toluene_score:.2f}.</p>
<h3>Explore any bump</h3>
<p>Pick any bump on NASA’s list from the menu to see its fingerprint and how much it looks like benzene or toluene.
For example, bumps 21 to 23 look a lot like benzene but have no name, and bumps 15 to 19 share the weights 91 and 106,
which might mean a heavier cousin of toluene such as xylene. Those are open questions, not results.</p>
<div class="chart">{chart(explorer_figure())}</div>

<h2><span class="num">Graph 4</span> · How much</h2>
<h3>What you’re looking at</h3>
<p>Close-ups of the benzene bump and the toluene bump. Each dot is one measurement. The shaded area under a bump measures
how much of that chemical there was, and NASA’s team measures it the same way.</p>
<div class="chart">{chart(areas_fig)}</div>
<h3>What it tells us</h3>
<div class="big">
  <div><strong>{ratio['benzene']:.0%}</strong>our benzene amount, compared with NASA’s</div>
  <div><strong>{ratio['toluene']:.0%}</strong>our toluene amount, compared with NASA’s</div>
</div>
<p>Starting from the raw numbers, we get the same amounts NASA reported. These areas measure the size of the signal, not
grams: turning them into an actual amount needs the instrument’s calibration.</p>

<h2>Every bump, NASA vs. the raw data</h2>
<p>Times are seconds after the gas entered the tube. “Strongest masses” are the weights that rise most at that moment
(45 and up). The two bumps NASA named are in bold.</p>
<div class="table-wrap"><table>
<tr><th>Bump</th><th>Tube</th><th>NASA’s name</th><th>NASA’s time</th><th>Our time</th><th>Difference</th><th>Strongest masses</th><th>Benzene score</th><th>Toluene score</th></tr>
{table_rows}
</table></div>

<h2>What this does not show</h2>
<ul>
  <li><b>Not proof of life.</b> Carbon-based chemicals also form without life, for example inside meteorites.</li>
  <li><b>Maybe not from Mars.</b> In this instrument some benzene can come from the rover’s own equipment. Proving a chemical
      is Martian takes more evidence.</li>
  <li><b>Some bumps come from Earth.</b> A lab chemical the rover carries (MTBSTFA) had soaked into this sample and makes bumps of its own.</li>
  <li><b>One rock, one test.</b> This is a single experiment on a single rock sample.</li>
</ul>

<h2>Sources and code</h2>
<ul>
  <li>Rover data: Curiosity SAM experiment 25387 (sol 1546), NASA Planetary Data System, Geosciences Node.
      <a href="https://pds-geosciences.wustl.edu/missions/msl/sam.htm">pds-geosciences.wustl.edu/missions/msl/sam.htm</a></li>
  <li>Lab fingerprints: NIST Chemistry WebBook, Standard Reference Database 69 (benzene and toluene).
      <a href="https://webbook.nist.gov/chemistry/">webbook.nist.gov/chemistry</a></li>
  <li>Background: Freissinet, C. et al. (2015). Organic molecules in the Sheepbed Mudstone, Gale Crater, Mars.
      <i>Journal of Geophysical Research: Planets</i>, 120, 495–514.</li>
  <li>Code: the analysis notebook (<code>notebooks/11_mars_organics_prototype.ipynb</code>) and this page’s builder
      (<code>website/build_website.py</code>) are in the <a href="{REPO_URL}">project’s GitHub repository</a>.</li>
</ul>
<footer>Made with Python (pandas, plotly) for CS85. Graphs are built directly from NASA’s public data.</footer>
</main>
</body>
</html>
"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(page, encoding='utf-8')
(OUT.parent / '.nojekyll').touch()     # tells GitHub Pages to serve the files as they are
print(f'wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB)')
print(f'{within} of {len(comparison)} peaks within one reading; benzene score {benzene_score:.2f}, '
      f'toluene score {toluene_score:.2f}; areas {ratio}')
