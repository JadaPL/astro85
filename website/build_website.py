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
import json
import math
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

# Colors: the same one-color-per-mass scheme as the notebook, in the darker steps made for a dark background
# (checked for colorblind safety against the chart panel color, #15121e)
COLORS = {78: '#3987e5', 91: '#d95926', 50: '#199e70', 77: '#c98500',
          92: '#d55181', 112: '#008300', 69: '#9085e9', 127: '#e66767'}
NAMES = {78: "m/z 78 · benzene's weight", 91: "m/z 91 · toluene's main piece", 50: 'm/z 50',
         77: 'm/z 77 · benzene piece', 92: "m/z 92 · toluene's weight", 112: "m/z 112 · chlorobenzene's weight",
         69: 'm/z 69 · mystery substance', 127: 'm/z 127 · mystery substance'}
# Chart ink on the dark "space" panels: text, secondary text, reference gray, gridlines, axis lines, shaded bands
INK, INK2, GRAY, GRID, AXIS, SHADE = '#f3eef8', '#b9b2c6', '#8f8a99', 'rgba(255,255,255,0.07)', 'rgba(255,255,255,0.22)', 'rgba(255,255,255,0.05)'
MUTED_BAR, MENU_BG = '#4d475e', '#1d1828'


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
    # The same look for every chart: transparent background (the dark page panel shows through),
    # faint gridlines, readable fonts, legend on top
    fig.update_layout(template='plotly_dark', height=height, margin=dict(l=70, r=24, t=56, b=56),
                      font=dict(family='Inter, system-ui, -apple-system, Segoe UI, sans-serif', size=14, color=INK),
                      legend=dict(orientation='h', x=0, y=1.02, yanchor='bottom'),
                      hoverlabel=dict(font_size=13, bgcolor=MENU_BG, bordercolor='rgba(255,255,255,0.25)', font_color=INK),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      modebar=dict(bgcolor='rgba(0,0,0,0)', color='#8f8a99', activecolor='#e8794a'))
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
                                        bgcolor=MENU_BG, bordercolor=AXIS, font=dict(color=INK))],
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
                                 fillcolor='rgba(57,135,229,0.25)' if mass == 78 else 'rgba(217,89,38,0.25)',
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
# 2b. Bonus section: the substance that comes out with toluene
#     (the same analysis as section 9 of the notebook)
# ---------------------------------------------------------------------------
MYSTERY_COLORS = {91: '#d95926', 58: '#9085e9', 69: '#008300', 127: '#d55181'}
MYSTERY_NAMES = {91: 'm/z 91 (toluene)', 58: 'm/z 58', 69: 'm/z 69', 127: 'm/z 127'}
MYSTERY_WINDOW = (912, 935)   # tube 4 seconds: after toluene, and after the overload has passed
highest_reading = ms['cps'].max()

# The mystery fingerprint, from the tail of the peak
run4 = runs[4]
in_window = run4[run4['rt'].between(*MYSTERY_WINDOW)].groupby('mass')['cps'].mean()
background = run4[run4['rt'].between(850, 896)].groupby('mass')['cps'].median()
mystery = (in_window - background.reindex(in_window.index).fillna(0)).clip(lower=0)
mystery_pct = 100 * mystery / mystery[mystery.index >= 35].max()
heavy = mystery_pct[mystery_pct.index > 100]
heaviest = int(heavy[heavy > 1].index.max())
echo1, echo2 = mystery[128] / mystery[127], mystery[129] / mystery[127]
tube1_top = runs[1][runs[1]['rt'].between(836, 852)].groupby('mass')['cps'].max()

# The suspect lineup (NIST IDs come from CAS numbers)
SUSPECTS = {
    'N-methyl-trifluoroacetamide': 'C815065',   # reagent by-product; in the team's oven-run table
    'trifluoroiodomethane (CF3I)': 'C2314978',  # has 127 and 69
    'acetone': 'C67641',                        # has 58
    'iodomethane (CH3I)': 'C74884',             # has 127 and 15
    'benzene': 'C71432',
    'trifluoroacetamide': 'C354381',            # reagent-like, has 69
    'chloromethane': 'C74873',                  # in the team's oven-run table
    'dichloromethane': 'C75092',                # in the team's oven-run table
    'toluene': 'C108883',
}
lineup = pd.Series({name: similarity(mystery, nist_spectrum(nist_id)) for name, nist_id in SUSPECTS.items()}).sort_values()
best, runner_up = lineup.index[-1], lineup.index[-2]


def overload_figure(column):
    # One sorting run: the key weights around the mystery chemical, with the file's highest reading as a gray line
    start, end, masses, note_text, note_at, note_from = {
        4: (885, 945, (91, 69, 127, 58), '58 reads<br>almost 0 here', (903, 0.05), (889, 2.7)),
        1: (770, 930, (127, 58), '58 drops to 0 just as<br>127 reaches its top', (838, 0.05), (815, 6.1)),
    }[column]
    run = runs[column]
    fig = go.Figure()
    for mass in masses:
        trace = run[(run['mass'] == mass) & run['rt'].between(start, end)]
        fig.add_trace(go.Scatter(x=trace['rt'].round(1), y=(trace['cps'] / 1e6).round(4), mode='lines+markers',
                                 name=MYSTERY_NAMES[mass], line=dict(color=MYSTERY_COLORS[mass], width=2), marker=dict(size=7),
                                 hovertemplate='%{x:.1f} s<br>%{y:.2f} million counts/s<extra>' + MYSTERY_NAMES[mass] + '</extra>'))
    fig.add_hline(y=highest_reading / 1e6, line_color=GRAY, line_width=1)
    fig.add_annotation(x=start + 1, y=highest_reading / 1e6, yshift=10, xanchor='left', text='highest reading in the file',
                       showarrow=False, font=dict(color=INK2, size=12))
    fig.add_annotation(x=note_at[0], y=note_at[1], ax=note_from[0], ay=note_from[1], axref='x', ayref='y',
                       text=note_text, showarrow=True, arrowhead=2, arrowcolor=INK2, font=dict(color=INK2, size=12))
    fig.update_xaxes(title_text='Time in the tube (seconds)', range=[start - 2, end + 2])   # short title fits phones
    fig.update_yaxes(title_text='Counts per second (millions)', range=[0, highest_reading / 1e6 + 0.8])
    tidy(fig, 400)
    fig.update_layout(legend=dict(y=-0.25, yanchor='top'), margin=dict(t=20, b=100))
    return fig


def mystery_mirror_figure():
    shown = mystery[(mystery.index >= 10) & (mystery.index <= 135)]
    shown = 100 * shown / shown.max()
    reference = nist_spectrum(SUSPECTS[best])
    reference = 100 * reference / reference.max()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=shown.index, y=shown.round(1), marker_color=MYSTERY_COLORS[58], width=0.8,
                         name=f'Mystery chemical ({MYSTERY_WINDOW[0]}–{MYSTERY_WINDOW[1]} s)',
                         hovertemplate='mass %{x}: %{y:.0f}% of the tallest bar<extra>mystery</extra>'))
    fig.add_trace(go.Bar(x=reference.index, y=-reference.round(1), customdata=reference.round(1), marker_color=GRAY,
                         width=0.8, name=f'NIST lab: {best}',
                         hovertemplate='mass %{x}: %{customdata:.0f}% of the tallest bar<extra>NIST lab</extra>'))
    fig.add_vrect(x0=10, x1=35, fillcolor=SHADE, line_width=0, layer='below')
    for mass in (58, 69, 127):
        fig.add_annotation(x=mass, y=-reference.get(mass, 0), yshift=-12, text=str(mass), showarrow=False,
                           font=dict(size=12, color=INK2))
    fig.update_xaxes(title_text='Mass (m/z)', range=[10, 135])
    fig.update_yaxes(title_text='Mystery ↑   ·   lab ↓', range=[-112, 112],
                     tickvals=[-100, -50, 0, 50, 100], ticktext=['100', '50', '0', '50', '100'])
    tidy(fig, 420)
    fig.update_layout(barmode='overlay', bargap=0, legend=dict(y=-0.25, yanchor='top'), margin=dict(t=30, b=110),
                      title=dict(text=f'Mystery vs. {best}: similarity {lineup[best]:.2f}', x=0.01, font=dict(size=15)))
    return fig


def lineup_figure():
    colors = [MYSTERY_COLORS[58] if name == best else MUTED_BAR for name in lineup.index]
    fig = go.Figure(go.Bar(x=lineup.values.round(3), y=lineup.index, orientation='h', marker_color=colors,
                           text=[f'{v:.2f}' for v in lineup.values], textposition='outside', width=0.6,
                           hovertemplate='%{y}<br>similarity %{x:.3f}<extra></extra>'))
    fig.update_xaxes(title_text='Similarity to the mystery fingerprint (1 = the same pattern)', range=[0, 1.15])
    fig.update_yaxes(automargin=True, showgrid=False)
    tidy(fig, 380)
    fig.update_layout(showlegend=False, margin=dict(t=20, b=60))
    return fig


clue_rows = [
    ('Heaviest piece', f'{heaviest}', 'The whole molecule probably weighs 127. An odd weight means it contains nitrogen (the “nitrogen rule”).'),
    ('Echo at 128', f'{echo1:.1%} of 127', f'About {echo1 / 0.011:.0f} carbon atoms (each one adds about 1.1%).'),
    ('Echo at 129', f'{echo2:.1%} of 127', 'No chlorine (would be ~32%), sulfur (~4%) or bromine (~97%).'),
    ('Piece 69', f'{mystery_pct[69]:.0f}% of the biggest piece', 'The weight of a CF₃ piece (one carbon, three fluorine): a hint of fluorine.'),
    ('Pieces 73 and 75', f'{mystery_pct[73]:.1f}% and {mystery_pct[75]:.1f}%',
     'Almost absent, so probably not one of the reagent’s silicon chemicals (they usually make these pieces).'),
    ('Tube 1, peak 4', f'126÷127 = {tube1_top[126] / tube1_top[127]:.2f} (mystery {mystery[126] / mystery[127]:.2f}), '
                       f'78÷127 = {tube1_top[78] / tube1_top[127]:.2f} (mystery {mystery[78] / mystery[127]:.2f})',
     'Same piece ratios, so NASA’s unnamed peak 4 in tube 1 looks like the same chemical.'),
]
clue_table = '\n'.join(f'<tr><td><b>{a}</b></td><td>{html.escape(b)}</td><td>{c}</td></tr>' for a, b, c in clue_rows)


# ---------------------------------------------------------------------------
# 2c. "Try it yourself" boxes: each section's information in an interactive,
#     non-graph form. Python works out the numbers (all from the real data);
#     the JavaScript in TRY_JS (further down) makes the boxes interactive.
# ---------------------------------------------------------------------------
def top_pieces(spectrum, n=5):
    # The n biggest pieces of a fingerprint (weights 35 and up), as % of the biggest
    s = spectrum[spectrum.index >= 35]
    s = 100 * s / s.max()
    return [[int(m), int(round(v))] for m, v in s.nlargest(n).items()]


oven_peak = ms.loc[ms['oven_T'].idxmax()]
heating = ms[ms['minutes'] <= oven_peak['minutes']]
comparison['within'] = comparison['difference'].abs() <= comparison['column'].map(scan_time)
by_peak = comparison.set_index('peak')

# The lab: oven, a race through tube 4, and benzene's pieces
tube4 = runs[4]
near_toluene = tube4[(tube4['mass'] == 127) & tube4['rt'].between(890, 920)]
runners = [{'name': 'Unnamed bump 9', 't': float(by_peak.loc[9, 'team_time'])},
           {'name': 'Benzene (bump 13)', 't': float(by_peak.loc[13, 'team_time'])},
           {'name': 'Toluene (bump 14)', 't': float(by_peak.loc[14, 'team_time'])},
           {'name': 'Mystery chemical', 't': round(float(near_toluene.loc[near_toluene['cps'].idxmax(), 'rt']), 1)}]
race_end = max(r['t'] for r in runners) + 30
lab_data = {'oven_min': round(float(heating['oven_T'].min())), 'oven_max': round(float(oven_peak['oven_T'])),
            'runners': runners, 'race_end': race_end, 'benzene_pieces': top_pieces(by_peak.loc[13, 'spectrum'])}


# Finish-line replay: every entry on NASA's list, in time order, for each tube
race = {}
for column in (1, 4):
    entries = []
    for _, p in team[team['gc_column'] == column].sort_values('team_time_s').iterrows():
        if p['event']:
            label = ('Start: gas is pushed into the tube' if p['team_time_s'] == 0
                     else f"Instrument event (NASA’s bump {p['peak']}): the trap is flash-heated again")
            entries.append({'t': float(p['team_time_s']), 'event': True, 'label': label})
        else:
            d = by_peak.loc[p['peak']]
            entries.append({'t': float(d['team_time']), 'event': False, 'peak': int(p['peak']), 'name': d['name'],
                            'our': float(d['our_time']), 'diff': float(d['difference']) or 0.0,
                            'within': bool(d['within']), 'masses': d['masses']})
    race[column] = {'length': RUN_LENGTH[column], 'entries': entries}

# Fingerprint game: three bumps, two lab fingerprints
game = {'bumps': {str(p): {'name': by_peak.loc[p, 'name'], 'pieces': top_pieces(by_peak.loc[p, 'spectrum']),
                           'scores': {'benzene': float(by_peak.loc[p, 'benzene']), 'toluene': float(by_peak.loc[p, 'toluene'])}}
                  for p in (13, 14, 21)},
        'refs': {m: top_pieces(REFERENCE[m]) for m in ('benzene', 'toluene')}}

# Bump cards
cards = [{'peak': int(d['peak']), 'tube': int(d['column']), 'name': d['name'], 'team': float(d['team_time']),
          'our': float(d['our_time']), 'diff': float(d['difference']) or 0.0, 'within': bool(d['within']),
          'masses': d['masses'], 'benzene': float(d['benzene']), 'toluene': float(d['toluene'])}
         for _, d in comparison.iterrows()]
card_filters = [('all', 'All', len(cards)), ('within', 'Matched within one reading', int(comparison['within'].sum())),
                ('off', 'Further off', int((~comparison['within']).sum())),
                ('named', 'Named by NASA', int((comparison['name'] != '').sum())),
                ('benzene', 'Looks like benzene (0.8+)', int((comparison['benzene'] >= 0.8).sum()))]

# Solve the case: each suspect's formula, weight (most common isotopes), carbon count and nitrogen
SUSPECT_FACTS = {
    'N-methyl-trifluoroacetamide': ('C₃H₄F₃NO', 127, 3, True),
    'trifluoroiodomethane (CF3I)': ('CF₃I', 196, 1, False),
    'acetone': ('C₃H₆O', 58, 3, False),
    'iodomethane (CH3I)': ('CH₃I', 142, 1, False),
    'benzene': ('C₆H₆', 78, 6, False),
    'trifluoroacetamide': ('C₂H₂F₃NO', 113, 2, True),
    'chloromethane': ('CH₃Cl', 50, 1, False),
    'dichloromethane': ('CH₂Cl₂', 84, 1, False),
    'toluene': ('C₇H₈', 92, 7, False),
}
carbons = int(round(echo1 / 0.011))
case = {'heaviest': heaviest, 'carbons': carbons, 'best': best, 'best_score': float(lineup[best]),
        'suspects': [{'name': name, 'formula': f, 'mw': mw, 'carbons': c, 'has_n': n, 'score': float(lineup[name])}
                     for name, (f, mw, c, n) in SUSPECT_FACTS.items()],
        'clues': [f'The heaviest piece is {heaviest}, so the chemical weighs at least {heaviest}.',
                  f'Nothing heavier shows up: the pieces at 142 and 196 (the whole weights of iodomethane and CF₃I) are '
                  f'{mystery_pct[142]:.1f}% and {mystery_pct[196]:.1f}% of the biggest piece. So it weighs exactly {heaviest}.',
                  'An odd weight means the chemical contains nitrogen (the “nitrogen rule”).',
                  f'The echo at 128 is {echo1:.1%} of 127: about {carbons} carbon atoms.',
                  f'Fingerprint lineup: {best} scores {lineup[best]:.3f}; the next best scores {lineup[runner_up]:.2f}.']}

try_data = {'lab': lab_data, 'race': race, 'game': game, 'cards': cards, 'case': case}


def try_box(box_id, title, intro, body):
    return (f'<section class="try" id="{box_id}" aria-label="Try it yourself: {html.escape(title)}">\n'
            f'<p class="label">Try it yourself</p>\n<h3>{title}</h3>\n<p>{intro}</p>\n{body}\n</section>')


lanes = '\n'.join(f'<div class="lane"><span>{html.escape(r["name"])}</span><div class="lane-track">'
                  f'<span class="runner" aria-hidden="true">●</span></div></div>' for r in runners)
try_lab = try_box('try-lab', 'Run the rover’s lab', 'Step through the three stages. The numbers come from the real experiment.', f'''
<div class="row" role="group" aria-label="Steps"><button class="step-tab">1 · Bake</button><button class="step-tab">2 · Sort</button><button class="step-tab">3 · Weigh</button></div>
<div class="panel step-panel">
  <p>The oven heated the rock powder from about {lab_data["oven_min"]} °C to {lab_data["oven_max"]} °C, over about {oven_peak["minutes"]:.0f} minutes.</p>
  <div class="row"><button id="heat">Heat the oven</button> <span class="big-number" id="oven-temp" aria-live="polite">{lab_data["oven_min"]} °C</span></div>
  <div class="meter" aria-hidden="true"><div id="oven-bar"></div></div>
</div>
<div class="panel step-panel" hidden>
  <p>In tube 4, chemicals race to the finish line. Each runner arrives at its real time, sped up about {race_end / 6:.0f} times.</p>
  <div class="row"><button id="race">Start the race</button> <span>Clock: <b id="race-clock">0 s</b></span></div>
  {lanes}
  <p>Finish order:</p><ol id="finish-order" aria-live="polite"></ol>
</div>
<div class="panel step-panel" hidden>
  <p>As each chemical comes out, it is smashed into pieces and the pieces are weighed. These are the biggest pieces counted when benzene came out (bump 13).</p>
  <div class="row"><button id="smash">Smash a benzene molecule</button></div>
  <div id="pieces" aria-live="polite"></div>
  <p class="small">Together, these piece weights are benzene’s fingerprint.</p>
</div>''')

try_race = try_box('try-replay', 'Finish-line replay',
    'Replay a sorting run. As the clock passes each bump on NASA’s list, a card shows when NASA saw it and when the raw data shows it.', '''
<div class="row" role="group" aria-label="Sorting run"><span>Run:</span><button data-tube="1">Tube 1</button><button data-tube="4" class="on">Tube 4</button></div>
<div class="row" role="group" aria-label="Speed"><span>Speed:</span><button data-speed="25">25×</button><button data-speed="50" class="on">50×</button><button data-speed="150">150×</button></div>
<div class="row"><button id="rp-play">▶ Play</button><button id="rp-reset">Reset</button><button id="rp-end">Skip to the end</button><span>Clock: <b id="rp-clock">0 s</b></span></div>
<p id="rp-count" aria-live="polite"></p>
<ol id="rp-list" class="feed"></ol>''')

try_fingerprint = try_box('try-finger', 'Match the fingerprint',
    'Pick a bump and look at the pieces the raw data shows. Then guess which lab fingerprint it matches. '
    '(Pieces lighter than 35 are left out, as in the similarity score.)', '''
<div class="row" role="group" aria-label="Bump"><span>Bump:</span><button data-bump="13">13</button><button data-bump="14">14</button><button data-bump="21">21</button></div>
<div class="panel"><b>Pieces in the raw data</b><div id="fg-pieces"></div></div>
<p>Which lab fingerprint does it match?</p>
<div class="guess-row"><button class="card" data-guess="benzene"><b>Benzene</b><span class="refpieces"></span></button><button class="card" data-guess="toluene"><b>Toluene</b><span class="refpieces"></span></button></div>
<p id="fg-verdict" aria-live="polite"></p>''')

try_cards = try_box('try-cards', 'Bump cards', 'Filter NASA’s bumps, then tap a card to see its details.',
    '<div class="row" role="group" aria-label="Filter">'
    + ''.join(f'<button data-filter="{key}">{label} ({count})</button>' for key, label, count in card_filters)
    + '</div>\n<div class="cards"></div>\n<p id="bc-detail" class="panel" aria-live="polite"></p>')

try_case = try_box('try-case', 'Solve the case',
    f'{len(SUSPECT_FACTS)} suspects. Reveal the clues one at a time and watch the suspects get ruled out.', f'''
<div class="cards"></div>
<div class="row"><button id="cs-next">Reveal clue 1 of {len(case["clues"])}</button></div>
<ol id="cs-clues" aria-live="polite"></ol>''')



# ---------------------------------------------------------------------------
# 3. The web page
# ---------------------------------------------------------------------------
CONFIG = {'displaylogo': False, 'responsive': True,
          'modeBarButtonsToRemove': ['lasso2d', 'select2d']}


def chart(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CONFIG)


PAGE_CSS = """
  :root { color-scheme: dark;
          --space: #07060d; --panel: #15121e; --glass: rgba(255,255,255,0.035); --line: rgba(255,255,255,0.09);
          --ink: #f6f0ea; --body: #d6cfdf; --muted: #a39cb2;
          --mars: #e8794a; --mars-soft: #f2a27a; --dust: #f3c98b; --link: #8ecbff; --ok: #5fd38d;
          --display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
          --text: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
          --mono: 'JetBrains Mono', ui-monospace, Menlo, Consolas, monospace; }
  * { box-sizing: border-box; }
  html { background: var(--space); }
  body { margin: 0; color: var(--body); font: 17px/1.65 var(--text); -webkit-font-smoothing: antialiased; }
  /* A starfield and faint Mars and nebula glows, fixed behind the whole page */
  body::before { content: ''; position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background-image:
      radial-gradient(1px 1px at 23px 41px, rgba(255,255,255,0.85), transparent 60%),
      radial-gradient(1px 1px at 141px 97px, rgba(255,255,255,0.5), transparent 60%),
      radial-gradient(1.6px 1.6px at 233px 173px, rgba(255,226,200,0.8), transparent 60%),
      radial-gradient(1px 1px at 317px 29px, rgba(255,255,255,0.45), transparent 60%),
      radial-gradient(1.2px 1.2px at 389px 251px, rgba(200,220,255,0.7), transparent 60%),
      radial-gradient(1px 1px at 71px 283px, rgba(255,255,255,0.4), transparent 60%),
      radial-gradient(1px 1px at 191px 331px, rgba(255,255,255,0.6), transparent 60%),
      radial-gradient(1.4px 1.4px at 57px 113px, rgba(255,255,255,0.75), transparent 60%),
      radial-gradient(1px 1px at 263px 59px, rgba(255,240,225,0.6), transparent 60%),
      radial-gradient(1.8px 1.8px at 409px 167px, rgba(255,255,255,0.9), transparent 60%),
      radial-gradient(1px 1px at 487px 401px, rgba(200,215,255,0.6), transparent 60%),
      radial-gradient(1.2px 1.2px at 131px 467px, rgba(255,255,255,0.55), transparent 60%),
      radial-gradient(1px 1px at 557px 281px, rgba(255,255,255,0.5), transparent 60%),
      radial-gradient(1.5px 1.5px at 331px 487px, rgba(255,220,195,0.7), transparent 60%),
      radial-gradient(ellipse 60% 45% at 100% 0%, rgba(232,121,74,0.15), transparent 70%),
      radial-gradient(ellipse 50% 40% at 0% 55%, rgba(110,90,210,0.10), transparent 70%),
      radial-gradient(ellipse 60% 40% at 100% 100%, rgba(232,121,74,0.07), transparent 70%);
    background-size: 420px 360px, 420px 360px, 420px 360px, 420px 360px, 420px 360px, 420px 360px, 420px 360px,
                     610px 530px, 610px 530px, 610px 530px, 610px 530px, 610px 530px, 610px 530px, 610px 530px,
                     100% 100%, 100% 100%, 100% 100%;
    background-repeat: repeat, repeat, repeat, repeat, repeat, repeat, repeat,
                       repeat, repeat, repeat, repeat, repeat, repeat, repeat, no-repeat, no-repeat, no-repeat; }

  /* The hero: title, a glowing Mars, its orbit and a benzene molecule */
  .hero { position: relative; overflow: hidden; padding: 104px 16px 88px; border-bottom: 1px solid var(--line);
          background: radial-gradient(ellipse 70% 90% at 85% 35%, rgba(232,121,74,0.20), transparent 60%),
                      linear-gradient(180deg, rgba(14,11,24,0.7), rgba(7,6,13,0)); }
  .hero .wrap { position: relative; z-index: 2; }
  .planet { position: absolute; z-index: 1; width: 440px; height: 440px; right: max(0px, calc(50% - 640px)); top: 48px;
            border-radius: 50%;
            background:
              radial-gradient(ellipse 22% 9% at 50% 7%, rgba(255,246,236,0.75), transparent 70%),
              radial-gradient(ellipse 30% 14% at 62% 42%, rgba(95,30,10,0.55), transparent 70%),
              radial-gradient(ellipse 22% 16% at 36% 64%, rgba(100,32,12,0.5), transparent 70%),
              radial-gradient(circle at 72% 70%, rgba(80,24,10,0.45) 0 5%, transparent 12%),
              radial-gradient(circle at 28% 40%, rgba(255,200,160,0.25) 0 4%, transparent 10%),
              radial-gradient(circle at 32% 30%, #f3a772 0%, #d0592b 34%, #93331a 66%, #3b1207 100%);
            box-shadow: inset -50px -40px 90px rgba(8,3,2,0.9), inset 10px 8px 30px rgba(255,190,150,0.15),
                        0 0 70px rgba(232,121,74,0.35), 0 0 180px rgba(232,121,74,0.18); }
  .orbit { position: absolute; z-index: 1; width: 640px; height: 190px; right: max(-100px, calc(50% - 740px)); top: 178px;
           border: 1px solid rgba(255,255,255,0.14); border-radius: 50%; transform: rotate(-16deg); }
  .orbit::after { content: ''; position: absolute; width: 9px; height: 9px; border-radius: 50%; background: #f6f0ea;
                  box-shadow: 0 0 12px rgba(255,255,255,0.8); top: 14px; left: 130px; }
  .molecule { position: absolute; z-index: 1; width: 200px; height: 200px; right: max(250px, calc(50% - 390px)); top: 330px;
              filter: drop-shadow(0 0 10px rgba(243,201,139,0.35)); animation: spin 160s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .wrap, main { max-width: 1040px; margin: 0 auto; }
  main { padding: 8px 16px 72px; }
  .eyebrow { font: 600 13px/1.4 var(--mono); letter-spacing: 3px; text-transform: uppercase; color: var(--mars-soft); margin: 0 0 14px; }
  h1 { font: 700 clamp(46px, 8.5vw, 92px)/0.98 var(--display); letter-spacing: -0.03em; color: var(--ink); margin: 0 0 22px; max-width: 640px; }
  h1 .mars { background: linear-gradient(100deg, #f3c98b 0%, #e8794a 45%, #c4471f 100%);
             -webkit-background-clip: text; background-clip: text; color: transparent; }
  .hero p.sub { font-size: 20px; line-height: 1.55; color: #e7e0ee; margin: 0 0 22px; max-width: 600px;
                text-shadow: 0 1px 14px rgba(7,6,13,0.9); }
  .readout { font: 500 12.5px/1.5 var(--mono); letter-spacing: 2.5px; color: var(--muted); margin: 0 0 16px; }
  .stats { display: flex; flex-wrap: wrap; gap: 10px; max-width: 600px; }
  .stats span { font: 13px/1.3 var(--mono); color: var(--body); padding: 7px 12px; border: 1px solid var(--line);
                border-radius: 999px; background: rgba(10,8,18,0.65); }
  .stats b { color: var(--dust); font-weight: 600; }

  /* Section headings: a small benzene-ring icon, and a badge for the graph number */
  h2 { font: 600 30px/1.2 var(--display); letter-spacing: -0.01em; color: var(--ink); margin: 72px 0 10px;
       padding-top: 32px; border-top: 1px solid var(--line); }
  h2::before { content: ''; display: inline-block; width: 26px; height: 26px; margin-right: 12px; vertical-align: -4px;
               background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e8794a' stroke-width='1.7'%3E%3Cpath d='M12 2.5L20.23 7.25V16.75L12 21.5L3.77 16.75V7.25Z'/%3E%3Ccircle cx='12' cy='12' r='4.3'/%3E%3C/svg%3E") center / contain no-repeat; }
  h2 .num { font: 600 13px/1 var(--mono); letter-spacing: 1.5px; text-transform: uppercase; color: var(--mars-soft);
            background: rgba(232,121,74,0.12); border: 1px solid rgba(232,121,74,0.35); padding: 6px 10px;
            border-radius: 999px; vertical-align: 5px; }
  h3 { font: 600 19px/1.3 var(--display); color: var(--ink); margin: 26px 0 6px; }
  p { margin: 0 0 14px; max-width: 760px; }
  b, strong { color: var(--ink); }
  i { color: var(--dust); }
  a { color: var(--link); text-underline-offset: 3px; }
  code { font: 14px var(--mono); color: var(--dust); background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 6px; }
  ::selection { background: rgba(232,121,74,0.35); color: #fff; }

  /* Panels: tips, lab steps, charts, results, big numbers and tables */
  .tip { background: var(--glass); border: 1px solid var(--line); border-left: 3px solid var(--mars); border-radius: 12px;
         padding: 16px 20px; margin: 36px 0 0; }
  .steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 18px 0; }
  .step { background: linear-gradient(160deg, rgba(232,121,74,0.12), rgba(21,18,30,0.92) 55%); border: 1px solid var(--line);
          border-radius: 16px; padding: 18px 20px; }
  .step b { font: 700 22px/1.3 var(--display); color: var(--mars-soft); }
  .chart { background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 10px; margin: 18px 0;
           overflow: hidden; box-shadow: 0 24px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04); }
  .result { border-left: 3px solid var(--mars); background: linear-gradient(90deg, rgba(232,121,74,0.11), rgba(232,121,74,0.02));
            border-radius: 0 14px 14px 0; padding: 14px 18px; margin: 18px 0; }
  .big { display: flex; flex-wrap: wrap; gap: 16px; margin: 18px 0; }
  .big div { flex: 1 1 220px; background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; }
  .big strong { display: block; font: 700 48px/1.05 var(--display); margin-bottom: 4px;
                background: linear-gradient(100deg, #f3c98b, #e8794a); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .table-wrap { overflow-x: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 16px; }
  table { border-collapse: collapse; width: 100%; font-size: 15px; font-variant-numeric: tabular-nums; }
  th, td { padding: 9px 12px; text-align: right; border-bottom: 1px solid var(--line); white-space: nowrap; }
  table:not(.clues) td { font: 14px/1.4 var(--mono); }
  th:nth-child(3), td:nth-child(3), th:nth-child(7), td:nth-child(7) { text-align: left; }
  th { font: 600 13px/1.3 var(--text); color: var(--ink); background: #1b1726; position: sticky; top: 0; }
  tr.named td { color: var(--dust); font-weight: 600; }
  tr:hover td { background: rgba(255,255,255,0.025); }
  table.clues th, table.clues td { text-align: left; white-space: normal; vertical-align: top; }
  table.clues td:first-child { white-space: nowrap; }
  ul { max-width: 760px; padding-left: 22px; }
  li { margin-bottom: 8px; overflow-wrap: anywhere; }   /* long links and file names wrap on phones */
  li::marker { color: var(--mars); }
  footer { font: 13px/1.6 var(--mono); color: var(--muted); border-top: 1px solid var(--line); margin-top: 64px; padding-top: 18px; }

  /* Smaller screens: shrink Mars behind the text, hide the orbit and molecule */
  @media (max-width: 1100px) {
    .planet { width: 340px; height: 340px; right: -90px; top: 40px; opacity: 0.6; }
    .orbit, .molecule { display: none; }
  }
  @media (max-width: 700px) {
    .hero { padding: 72px 16px 56px; }
    .planet { width: 240px; height: 240px; right: -90px; top: 16px; opacity: 0.45; }
    h2 { font-size: 25px; }
  }
  @media (prefers-reduced-motion: reduce) { .molecule { animation: none; } }
"""

TRY_CSS = """
  /* "Try it yourself" boxes: a glowing mission-console look */
  .try { position: relative; border: 1px solid rgba(232,121,74,0.30); border-radius: 20px; padding: 20px 22px; margin: 30px 0 10px;
         background: linear-gradient(150deg, rgba(232,121,74,0.11), rgba(110,90,210,0.07) 55%, rgba(21,18,30,0.92));
         box-shadow: 0 20px 50px rgba(0,0,0,0.35); }
  .try [hidden] { display: none !important; }
  .try .label { font: 600 12px/1.4 var(--mono); letter-spacing: 2.5px; text-transform: uppercase; color: var(--dust); margin: 0 0 4px; }
  .try .label::before { content: '◆  '; color: var(--mars); }
  .try h3 { margin: 0 0 6px; font-size: 22px; }
  .try button { font: 500 15px/1.3 var(--text); padding: 8px 15px; min-height: 38px; border-radius: 999px; cursor: pointer;
                border: 1px solid rgba(255,255,255,0.16); background: rgba(255,255,255,0.05); color: var(--ink);
                transition: border-color .15s, box-shadow .15s, background .15s; }
  .try button:hover { border-color: var(--mars); box-shadow: 0 0 0 3px rgba(232,121,74,0.15); }
  .try button:focus-visible { outline: 2px solid var(--link); outline-offset: 2px; }
  .try button.on { background: var(--mars); border-color: var(--mars); color: #1b0d06; font-weight: 600; }
  .try .row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0; }
  .try .panel { background: rgba(8,7,14,0.6); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; margin: 12px 0; max-width: none; }
  .try .small { font-size: 14px; color: var(--muted); }
  .try .chip { display: inline-block; padding: 4px 11px; margin: 6px 6px 0 0; border-radius: 999px; font: 13.5px/1.4 var(--mono);
               color: var(--ink); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); }
  .try .ok { color: var(--ok); font-weight: 600; }
  .try .no { color: var(--mars-soft); font-weight: 600; }
  .try .big-number { font: 700 36px/1.1 var(--display); color: var(--mars); text-shadow: 0 0 24px rgba(232,121,74,0.55); font-variant-numeric: tabular-nums; }
  .try .meter { height: 12px; background: rgba(255,255,255,0.06); border: 1px solid var(--line); border-radius: 999px; overflow: hidden; }
  .try .meter div { height: 100%; width: 0; background: linear-gradient(90deg, #3987e5, #e8794a 65%, #ffd27a); box-shadow: 0 0 14px rgba(232,121,74,0.6); }
  .try .lane { display: grid; grid-template-columns: minmax(110px, 170px) 1fr; gap: 10px; align-items: center; margin: 8px 0; font-size: 14px; }
  .try .lane-track { position: relative; height: 26px; border: 1px solid rgba(255,255,255,0.12); border-radius: 999px;
                     background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.08)); }
  .try .lane-track::after { content: ''; position: absolute; right: 22px; top: 3px; bottom: 3px; border-right: 2px solid var(--dust); }
  .try .runner { position: absolute; left: 0; top: 1px; width: 22px; text-align: center; font-size: 18px; line-height: 22px;
                 color: var(--mars); text-shadow: 0 0 10px rgba(232,121,74,0.9); }
  .try .feed { list-style: none; padding: 0; max-height: 340px; overflow-y: auto; }
  .try .feed li { background: rgba(8,7,14,0.6); border: 1px solid var(--line); border-radius: 12px; padding: 9px 13px; margin: 6px 0; }
  .try .cards, .try .guess-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin: 12px 0; }
  .try .card { display: block; text-align: left; border-radius: 14px; padding: 11px 13px; background: rgba(8,7,14,0.6);
               border: 1px solid var(--line); color: var(--body); overflow-wrap: anywhere; }
  .try button.card.on { background: rgba(232,121,74,0.12); color: var(--ink); border: 2px solid var(--mars); font-weight: 500; }
  #try-case .cards { grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); }
  .try .refpieces { display: block; }
  .try .suspect { transition: opacity .3s; }
  .try .suspect.out { opacity: 0.42; }
  .try .suspect.out b { text-decoration: line-through; }
  .try .suspect .why { font-size: 13px; margin-top: 4px; }
  .try .suspect.winner { border: 2px solid var(--ok); box-shadow: 0 0 28px rgba(95,211,141,0.25); }
  @media (prefers-reduced-motion: reduce) { .try * { transition: none !important; animation: none !important; } }
"""

def molecule_svg():
    # A benzene molecule for the hero: six carbon atoms in a ring (with the aromatic circle), each holding a hydrogen
    centre, ring, outer = 150, 62, 112
    angles = [math.radians(a) for a in range(-90, 270, 60)]
    carbons = [(centre + ring * math.cos(a), centre + ring * math.sin(a)) for a in angles]
    hydrogens = [(centre + outer * math.cos(a), centre + outer * math.sin(a)) for a in angles]
    ring_path = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in carbons) + ' Z'
    bonds = ''.join(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
                    for (x1, y1), (x2, y2) in zip(carbons, hydrogens))
    carbon_atoms = ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9"/>' for x, y in carbons)
    hydrogen_atoms = ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6"/>' for x, y in hydrogens)
    return (f'<svg class="molecule" viewBox="0 0 300 300" aria-hidden="true" focusable="false">'
            f'<g fill="none" stroke="#f3c98b" stroke-width="2.2" stroke-opacity="0.85"><path d="{ring_path}"/>'
            f'<circle cx="{centre}" cy="{centre}" r="36"/>{bonds}</g>'
            f'<g fill="#e8794a">{carbon_atoms}</g><g fill="#f6f0ea">{hydrogen_atoms}</g></svg>')


TRY_JS = r"""
(function () {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const num = (n, digits = 0) => n == null ? '—' :
    Number(n).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  // Run draw(fraction) from 0 to 1 over ms milliseconds (or jump straight to 1 if the reader prefers less motion)
  function animate(ms, draw, done) {
    if (reduceMotion) { draw(1); if (done) done(); return; }
    const start = performance.now();
    function frame(now) {
      const f = Math.min(1, (now - start) / ms);
      draw(f);
      if (f < 1) requestAnimationFrame(frame); else if (done) done();
    }
    requestAnimationFrame(frame);
  }
  function pick(buttons, chosen) { buttons.forEach(b => b.classList.toggle('on', b === chosen)); }

  // ---- Run the rover's lab: bake, sort, weigh ----
  const lab = document.getElementById('try-lab');
  if (lab) {
    const L = TRY.lab;
    const tabs = [...lab.querySelectorAll('.step-tab')], panels = [...lab.querySelectorAll('.step-panel')];
    const showStep = i => { panels.forEach((p, j) => p.hidden = j !== i); pick(tabs, tabs[i]); };
    tabs.forEach((t, i) => t.addEventListener('click', () => showStep(i)));
    showStep(0);

    lab.querySelector('#heat').addEventListener('click', () => {
      const out = lab.querySelector('#oven-temp'), bar = lab.querySelector('#oven-bar');
      animate(2500, f => {
        out.textContent = num(L.oven_min + f * (L.oven_max - L.oven_min)) + ' °C';
        bar.style.width = (f * 100) + '%';
      });
    });

    lab.querySelector('#race').addEventListener('click', () => {
      const dots = lab.querySelectorAll('.runner'), order = lab.querySelector('#finish-order'), clock = lab.querySelector('#race-clock');
      order.innerHTML = '';
      const finished = new Set();
      animate(6000, f => {
        const now = f * L.race_end;
        clock.textContent = num(now) + ' s';
        L.runners.forEach((r, i) => {
          const g = Math.min(1, now / r.t);           // each runner reaches the finish at its real time
          dots[i].style.left = `calc(${g * 100}% - ${g * 22}px)`;
          if (g >= 1 && !finished.has(i)) { finished.add(i); order.append(el('li', null, `${r.name}: ${num(r.t)} s`)); }
        });
      });
    });

    lab.querySelector('#smash').addEventListener('click', () => {
      const box = lab.querySelector('#pieces');
      box.innerHTML = '';
      L.benzene_pieces.forEach(([mass, pct], i) =>
        setTimeout(() => box.append(el('span', 'chip', `piece ${mass}: ${pct}%`)), reduceMotion ? 0 : i * 250));
    });
  }

  // ---- Finish-line replay of a sorting run ----
  const rp = document.getElementById('try-replay');
  if (rp) {
    let tube = 4, speed = 50, clockTime = 0, shown = 0, playing = false, last = null;
    const list = rp.querySelector('#rp-list'), clock = rp.querySelector('#rp-clock');
    const count = rp.querySelector('#rp-count'), playBtn = rp.querySelector('#rp-play');
    function card(e) {
      const li = el('li');
      if (e.event) { li.append(el('b', null, `${num(e.t)} s · `), document.createTextNode(e.label)); return li; }
      li.append(el('b', null, `${num(e.t)} s · Bump ${e.peak}${e.name ? ' · ' + e.name : ''}`), el('br'),
                document.createTextNode(`Raw data: ${num(e.our, 1)} s (${e.diff >= 0 ? '+' : ''}${num(e.diff, 1)} s) `),
                el('span', e.within ? 'ok' : 'no', e.within ? '✓ within one reading' : '≈ further off'), el('br'),
                document.createTextNode(`Strongest pieces: ${e.masses}`));
      return li;
    }
    function update() {
      const run = TRY.race[tube];
      clock.textContent = num(clockTime) + ' s';
      while (shown < run.entries.length && run.entries[shown].t <= clockTime) list.prepend(card(run.entries[shown++]));
      const bumps = run.entries.filter(e => !e.event).length;
      const crossed = run.entries.slice(0, shown).filter(e => !e.event).length;
      count.textContent = `${crossed} of ${bumps} bumps have crossed the finish line`;
      if (clockTime >= run.length) { playing = false; playBtn.textContent = '▶ Play'; }
    }
    function reset() { clockTime = 0; shown = 0; playing = false; list.innerHTML = ''; playBtn.textContent = '▶ Play'; update(); }
    function frame(now) {
      if (!playing) return;
      if (last != null) clockTime = Math.min(TRY.race[tube].length, clockTime + (now - last) / 1000 * speed);
      last = now;
      update();
      if (playing) requestAnimationFrame(frame);
    }
    playBtn.addEventListener('click', () => {
      if (clockTime >= TRY.race[tube].length) reset();
      playing = !playing;
      playBtn.textContent = playing ? '❚❚ Pause' : '▶ Play';
      last = null;
      if (playing) requestAnimationFrame(frame);
    });
    rp.querySelector('#rp-reset').addEventListener('click', reset);
    rp.querySelector('#rp-end').addEventListener('click', () => { clockTime = TRY.race[tube].length; update(); });
    const tubeBtns = [...rp.querySelectorAll('[data-tube]')], speedBtns = [...rp.querySelectorAll('[data-speed]')];
    tubeBtns.forEach(b => b.addEventListener('click', () => { tube = +b.dataset.tube; pick(tubeBtns, b); reset(); }));
    speedBtns.forEach(b => b.addEventListener('click', () => { speed = +b.dataset.speed; pick(speedBtns, b); }));
    reset();
  }

  // ---- Match the fingerprint ----
  const fg = document.getElementById('try-finger');
  if (fg) {
    const G = TRY.game;
    let bump = '13';
    const pieces = fg.querySelector('#fg-pieces'), verdict = fg.querySelector('#fg-verdict');
    const bumpBtns = [...fg.querySelectorAll('[data-bump]')], guessBtns = [...fg.querySelectorAll('[data-guess]')];
    guessBtns.forEach(card => G.refs[card.dataset.guess].forEach(([m, p]) =>
      card.querySelector('.refpieces').append(el('span', 'chip', `${m}: ${p}%`))));
    const showBump = b => {
      bump = b;
      pick(bumpBtns, bumpBtns.find(x => x.dataset.bump === b));
      pick(guessBtns, null);
      verdict.textContent = '';
      pieces.innerHTML = '';
      G.bumps[b].pieces.forEach(([m, p]) => pieces.append(el('span', 'chip', `${m}: ${p}%`)));
    };
    guessBtns.forEach(card => card.addEventListener('click', () => {
      const s = G.bumps[bump].scores, name = G.bumps[bump].name;
      const best = s.benzene >= s.toluene ? 'benzene' : 'toluene';
      const right = card.dataset.guess === best;
      pick(guessBtns, card);
      verdict.innerHTML = '';
      verdict.append(el('span', right ? 'ok' : 'no', right ? '✓ Good call. ' : `✗ It’s closer to ${best}. `));
      let text = `Similarity: benzene ${s.benzene.toFixed(2)}, toluene ${s.toluene.toFixed(2)}. `;
      if (s[best] >= 0.95) text += `That’s a near-perfect match: bump ${bump} really is ${best}.`;
      else if (s[best] >= 0.7) text += `It looks a lot like ${best}, but not perfectly.` +
                                       (name ? '' : ' NASA didn’t name this bump, so it’s an open question.');
      else text += 'Even the closest match is weak: pieces that belong to neither chemical are mixed in ' +
                   '(the Bonus section below works out what they are).' + (name ? ` NASA named this bump ${name}.` : '');
      verdict.append(document.createTextNode(text));
    }));
    bumpBtns.forEach(x => x.addEventListener('click', () => showBump(x.dataset.bump)));
    showBump('13');
  }

  // ---- Bump cards with filters ----
  const bc = document.getElementById('try-cards');
  if (bc) {
    const grid = bc.querySelector('.cards'), detail = bc.querySelector('#bc-detail');
    const filterBtns = [...bc.querySelectorAll('[data-filter]')];
    const filters = { all: c => true, within: c => c.within, off: c => !c.within, named: c => !!c.name, benzene: c => c.benzene >= 0.8 };
    function render(f) {
      grid.innerHTML = '';
      detail.textContent = 'Tap a card to see its details.';
      pick(filterBtns, filterBtns.find(x => x.dataset.filter === f));
      TRY.cards.filter(filters[f]).forEach(c => {
        const b = el('button', 'card');
        b.append(el('b', null, `Bump ${c.peak}`), el('br'), document.createTextNode(c.name || `Tube ${c.tube}, no name`), el('br'),
                 el('span', c.within ? 'ok' : 'no', c.within ? '✓ matched' : `≈ off by ${num(Math.abs(c.diff), 1)} s`));
        b.addEventListener('click', () => {
          pick([...grid.querySelectorAll('.card')], b);
          detail.textContent = `Bump ${c.peak} (tube ${c.tube}${c.name ? ', ' + c.name : ', no name from NASA'}): ` +
            `NASA’s time ${num(c.team)} s, raw data ${num(c.our, 1)} s. Strongest pieces: ${c.masses}. ` +
            `Looks like benzene ${c.benzene.toFixed(2)}, toluene ${c.toluene.toFixed(2)}.`;
        });
        grid.append(b);
      });
    }
    filterBtns.forEach(x => x.addEventListener('click', () => render(x.dataset.filter)));
    render('all');
  }

  // ---- Solve the case: rule out suspects one clue at a time ----
  const cs = document.getElementById('try-case');
  if (cs) {
    const K = TRY.case;
    let step = 0;
    const grid = cs.querySelector('.cards'), clues = cs.querySelector('#cs-clues'), btn = cs.querySelector('#cs-next');
    const cards = K.suspects.map(s => {
      const d = el('div', 'card suspect');
      d.append(el('b', null, s.name), el('br'), document.createTextNode(`${s.formula} · weighs ${s.mw}`), el('div', 'why'));
      grid.append(d);
      return d;
    });
    // One rule per clue: return a reason to rule the suspect out, or null if it still fits
    const rules = [
      s => s.mw >= K.heaviest ? null : `Out: weighs ${s.mw}, lighter than the ${K.heaviest} piece`,
      s => s.mw <= K.heaviest ? null : `Out: weighs ${s.mw}, but nothing heavier than ${K.heaviest} shows up`,
      s => s.has_n ? null : 'Out: has no nitrogen',
      s => Math.abs(s.carbons - K.carbons) <= 1 ? null : `Out: has ${s.carbons} carbon atoms`,
      s => null,
    ];
    function reset() {
      step = 0; clues.innerHTML = '';
      cards.forEach(c => { c.classList.remove('out', 'winner'); c.querySelector('.why').textContent = ''; });
      btn.textContent = `Reveal clue 1 of ${K.clues.length}`;
    }
    btn.addEventListener('click', () => {
      if (step >= K.clues.length) { reset(); return; }
      clues.append(el('li', null, K.clues[step]));
      K.suspects.forEach((s, i) => {
        if (cards[i].classList.contains('out')) return;
        const why = rules[step](s);
        if (why) { cards[i].classList.add('out'); cards[i].querySelector('.why').textContent = why; }
      });
      step++;
      if (step < K.clues.length) { btn.textContent = `Reveal clue ${step + 1} of ${K.clues.length}`; return; }
      cards.forEach((c, i) => {
        if (c.classList.contains('out')) return;
        c.classList.add('winner');
        c.querySelector('.why').append(el('span', 'ok', `✓ Fits every clue (similarity ${K.suspects[i].score.toFixed(3)})`));
      });
      clues.append(el('li', null, `Case closed: ${K.best}, a by-product of the lab chemical from Earth.`));
      btn.textContent = 'Start over';
    });
    reset();
  }
})();
"""

try_script = ('<script>\nconst TRY = ' + json.dumps(try_data, ensure_ascii=False) + ';\n' + TRY_JS + '\n</script>')

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

mystery_section = f"""
<h2><span class="num">Bonus</span> · Detective work: who is the mystery chemical?</h2>
<p>In Graph 3, toluene’s bump turned out to hide a second chemical, whose biggest pieces weighed 15, 69 and 127.
Can the data tell us what it is? Chemists narrow down an unknown chemical with a few standard clues. Here they are, one by one.</p>

<h3>Clue 1: the detector got overloaded</h3>
<p><b>What you’re looking at:</b> close-ups of a few weights as the mystery chemical comes out of the tube, in both sorting
runs. Weights 69 and 127 shoot up together just after toluene (91) and fade together, so they come from the same chemical.
Weight 58 is strange: it reads almost <b>zero</b> right when the chemical is strongest, then jumps up a few seconds later.
The gray line is the highest reading anywhere in the file ({highest_reading / 1e6:.1f} million counts per second).</p>
<h3>Tube 4, around peak 14 (toluene)</h3>
<div class="chart">{chart(overload_figure(4))}</div>
<h3>Tube 1, around peak 4</h3>
<div class="chart">{chart(overload_figure(1))}</div>
<p><b>What it tells us:</b> a signal that disappears exactly at its peak, in an instrument that tops out like this, looks
like <b>detector overload</b>: the signal is too strong for the counter to keep up, so it reports far too little. That means
weight 58 is probably the chemical’s <i>strongest</i> piece. So for its fingerprint we use the tail of the bump
({MYSTERY_WINDOW[0]}–{MYSTERY_WINDOW[1]} seconds), where the signal is back in the range the detector can count.</p>

<h3>Clue 2: what the pieces say</h3>
<p>The biggest pieces of the clean fingerprint are
{', '.join(f'{int(m)} ({v:.0f}%)' for m, v in mystery_pct[mystery_pct.index >= 35].nlargest(5).items())}.</p>
<div class="table-wrap"><table class="clues">
<tr><th>Clue</th><th>What the data shows</th><th>What it means</th></tr>
{clue_table}
</table></div>
<p>A molecule that weighs 127, with about 3 carbon atoms, one nitrogen and fluorine, is a very specific description.</p>

<h3>Clue 3: the suspect lineup</h3>
<p><b>What you’re looking at:</b> the mystery fingerprint (top) mirrored against the best-matching lab fingerprint (bottom),
then the similarity score of every suspect. The suspects are the chemicals the NASA team lists for this experiment, plus
chemicals that could explain weights 58 or 127.</p>
<div class="chart">{chart(mystery_mirror_figure())}</div>
<div class="chart">{chart(lineup_figure())}</div>
<div class="result"><b>The verdict:</b> the mystery chemical is almost certainly <b>{best}</b>
(similarity {lineup[best]:.3f}; the next best, {runner_up}, scores only {lineup[runner_up]:.2f}). It is a by-product of
MTBSTFA, a lab chemical the rover carries from Earth that had soaked into this rock sample, and the NASA team’s own
oven-run table lists it in this experiment. So it most likely <b>came from Earth, not Mars</b>. NASA’s unnamed peak 4 in
tube 1 looks like the same chemical.</div>

<h3>How sure is this?</h3>
<ul>
  <li><b>The fingerprint match is very strong</b>, and the chemical fits every clue: it weighs 127 and has 3 carbon atoms,
      one nitrogen and a CF₃ group.</li>
  <li><b>“Detector overload” is our explanation</b> for weight 58’s strange dip. It fits the evidence, but this file alone can’t prove it.</li>
  <li><b>Weight 15 is bigger than the lab fingerprint predicts.</b> The score ignores weights below 35, and other chemicals can make that small piece too.</li>
  <li><b>Three silicon chemicals from the reagent couldn’t be scored</b>, because NIST has no fingerprint for them. Their usual marker pieces (73 and 75) are almost absent, though.</li>
</ul>
<p>Lab fingerprints for all the suspects come from the NIST Chemistry WebBook (N-methyl-trifluoroacetamide: CAS 815-06-5).
The full working is in section 9 of the project notebook.</p>
"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Benzene on Mars</title>
<meta name="description" content="Checking NASA's chemistry results with the Curiosity rover's raw data: interactive graphs with plain-language explanations.">
<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" charset="utf-8"></script>
<meta name="theme-color" content="#07060d">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400..700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap">
<style>
{PAGE_CSS}
{TRY_CSS}
</style>
</head>
<body>
<header class="hero">
  <div class="planet" aria-hidden="true"></div>
  <div class="orbit" aria-hidden="true"></div>
  {molecule_svg()}
  <div class="wrap">
    <p class="eyebrow">CS85 · Project 11{byline}</p>
    <h1>Benzene on <span class="mars">Mars</span></h1>
    <p class="sub">Checking NASA’s chemistry results with the Curiosity rover’s raw data. Every graph on this page is interactive.</p>
    <p class="readout">SOL {SOL} · EXPERIMENT {EID} · SAM GC-MS · GALE CRATER</p>
    <div class="stats"><span><b>{len(ms):,}</b> raw readings</span><span><b>{len(comparison)}</b> bumps checked</span><span><b>{benzene_score:.2f}</b> benzene match</span><span><b>1</b> mystery solved</span></div>
  </div>
</header>
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

{try_lab}

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

{try_race}

{try_cards}

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

{try_fingerprint}

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

{mystery_section}

{try_case}

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
{try_script}
</body>
</html>
"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(page, encoding='utf-8')
(OUT.parent / '.nojekyll').touch()     # tells GitHub Pages to serve the files as they are
print(f'wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB)')
print(f'{within} of {len(comparison)} peaks within one reading; benzene score {benzene_score:.2f}, '
      f'toluene score {toluene_score:.2f}; areas {ratio}')
