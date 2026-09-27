import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from collections import defaultdict

def fetch_json(url, token=None):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'GitHub-Stats-Script')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def generate_svg(total_commits, hours, days):
    morning = sum(hours[6:12])
    daytime = sum(hours[12:18])
    evening = sum(hours[18:24])
    night = sum(hours[0:6])
    
    m_pct = (morning / total_commits) * 100 if total_commits else 0
    d_pct = (daytime / total_commits) * 100 if total_commits else 0
    e_pct = (evening / total_commits) * 100 if total_commits else 0
    n_pct = (night / total_commits) * 100 if total_commits else 0

    weekday_commits = sum(d["commits"] for d in days[:5])
    weekend_commits = sum(d["commits"] for d in days[5:])
    weekday_pct = (weekday_commits / total_commits) * 100 if total_commits else 0
    weekend_pct = (weekend_commits / total_commits) * 100 if total_commits else 0

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="840" height="370" viewBox="0 0 840 370" fill="none">')
    svg.append('''<style>
      .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 700; fill: #ffffff; }
      .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 500; fill: #8b949e; }
      .header-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; fill: #58a6ff; }
      .header-sub { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; fill: #8b949e; letter-spacing: 0.5px; }
      .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #c9d1d9; }
      .sublabel { font-family: "Fira Code", monospace; font-size: 11px; font-weight: 500; fill: #8b949e; }
      .val-mono { font-family: "Fira Code", monospace; font-size: 12px; font-weight: 600; fill: #ffffff; }
      .bar-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; fill: #8b949e; }
      .peak-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 700; fill: #38bdf8; }
      .chip-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 600; fill: #58a6ff; }
      .badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 700; fill: #000000; }
    </style>''')

    svg.append('''<defs>
      <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#0d1117" />
        <stop offset="100%" stop-color="#161b22" />
      </linearGradient>
      <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#161b22" />
        <stop offset="100%" stop-color="#0f141c" />
      </linearGradient>
      <linearGradient id="daytimeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#38bdf8" />
        <stop offset="100%" stop-color="#0284c7" />
      </linearGradient>
      <linearGradient id="eveningGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#c084fc" />
        <stop offset="100%" stop-color="#9333ea" />
      </linearGradient>
      <linearGradient id="nightGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#fbbf24" />
        <stop offset="100%" stop-color="#d97706" />
      </linearGradient>
      <linearGradient id="morningGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#34d399" />
        <stop offset="100%" stop-color="#059669" />
      </linearGradient>
      <linearGradient id="barPeakGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#38bdf8" />
        <stop offset="100%" stop-color="#2563eb" />
      </linearGradient>
      <linearGradient id="barStdGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#8b949e" stop-opacity="0.8" />
        <stop offset="100%" stop-color="#30363d" />
      </linearGradient>
      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="4" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
    </defs>''')

    svg.append('<rect x="1" y="1" width="838" height="368" rx="14" fill="url(#bgGrad)" stroke="#30363d" stroke-width="1.2" />')

    # Header
    svg.append('<g transform="translate(24, 22)">')
    svg.append('  <text x="0" y="14" class="header-title">⚡ COMMIT ACTIVITY &amp; WORKFLOW METRICS</text>')
    svg.append('  <text x="0" y="29" class="header-sub">REAL-TIME HISTORICAL DISTRIBUTION · LOCAL KARACHI TIME (PKT / UTC+5)</text>')
    svg.append('  <rect x="650" y="-3" width="142" height="24" rx="12" fill="#1f2937" stroke="#374151" stroke-width="1" />')
    svg.append('  <circle cx="662" cy="9" r="4" fill="#34d399" />')
    svg.append(f'  <text x="672" y="13" class="chip-text">{total_commits} COMMITS ANALYZED</text>')
    svg.append('</g>')

    # Left Card: Time of Day
    svg.append('<g transform="translate(24, 68)">')
    svg.append('  <rect width="384" height="278" rx="12" fill="url(#cardGrad)" stroke="#30363d" stroke-width="1" />')
    svg.append('  <text x="18" y="26" class="title">🕒 Productive Hours Breakdown</text>')
    svg.append('  <text x="18" y="42" class="subtitle">Commit velocity by time of day (Karachi Time)</text>')

    bar_w = 348
    w_d = (daytime / total_commits) * bar_w if total_commits else 0
    w_e = (evening / total_commits) * bar_w if total_commits else 0
    w_n = (night / total_commits) * bar_w if total_commits else 0
    w_m = (morning / total_commits) * bar_w if total_commits else 0

    svg.append('  <g transform="translate(18, 56)">')
    svg.append(f'    <rect x="0" y="0" width="{bar_w}" height="10" rx="5" fill="#21262d" />')
    svg.append(f'    <rect x="0" y="0" width="{w_d:.1f}" height="10" rx="5" fill="url(#daytimeGrad)" />')
    svg.append(f'    <rect x="{w_d:.1f}" y="0" width="{w_e:.1f}" height="10" fill="url(#eveningGrad)" />')
    svg.append(f'    <rect x="{w_d + w_e:.1f}" y="0" width="{w_n:.1f}" height="10" fill="url(#nightGrad)" />')
    svg.append(f'    <rect x="{w_d + w_e + w_n:.1f}" y="0" width="{w_m:.1f}" height="10" rx="5" fill="url(#morningGrad)" />')
    svg.append('  </g>')

    rows = [
        {"icon": "☀️", "name": "Daytime", "hours": "12:00 – 18:00", "commits": daytime, "pct": d_pct, "color": "#38bdf8", "tag": "Peak Flow"},
        {"icon": "🌆", "name": "Evening", "hours": "18:00 – 00:00", "commits": evening, "pct": e_pct, "color": "#c084fc", "tag": ""},
        {"icon": "🌙", "name": "Night Owl", "hours": "00:00 – 06:00", "commits": night, "pct": n_pct, "color": "#fbbf24", "tag": "Active"},
        {"icon": "🌅", "name": "Morning", "hours": "06:00 – 12:00", "commits": morning, "pct": m_pct, "color": "#34d399", "tag": ""}
    ]

    ry = 82
    for r in rows:
        svg.append(f'  <g transform="translate(18, {ry})">')
        svg.append(f'    <circle cx="10" cy="11" r="9" fill="{r["color"]}" fill-opacity="0.15" stroke="{r["color"]}" stroke-width="1" />')
        svg.append(f'    <text x="6" y="15" font-size="11">{r["icon"]}</text>')
        svg.append(f'    <text x="26" y="11" class="label">{r["name"]}</text>')
        svg.append(f'    <text x="26" y="24" class="sublabel">{r["hours"]}</text>')
        if r["tag"]:
            svg.append(f'    <rect x="150" y="2" width="58" height="16" rx="8" fill="{r["color"]}" fill-opacity="0.2" stroke="{r["color"]}" stroke-width="0.8" />')
            svg.append(f'    <text x="160" y="14" font-family="-apple-system, sans-serif" font-size="9" font-weight="700" fill="{r["color"]}">{r["tag"].upper()}</text>')
        svg.append(f'    <text x="348" y="12" text-anchor="end" class="val-mono">{r["commits"]} <tspan fill="#8b949e" font-size="11">commits</tspan></text>')
        svg.append(f'    <text x="348" y="24" text-anchor="end" class="sublabel">{r["pct"]:.1f}%</text>')
        svg.append('  </g>')
        ry += 32

    # Sparkline
    svg.append('  <g transform="translate(18, 214)">')
    svg.append('    <text x="0" y="10" class="sublabel" font-size="10">24-HOUR HOURLY FREQUENCY:</text>')
    max_h = max(hours) if any(hours) else 1
    chart_w = 348
    bar_space = chart_w / 24
    for i, h_val in enumerate(hours):
        bh = max(2, (h_val / max_h) * 26)
        bx = i * bar_space
        by = 40 - bh
        fill_col = "#38bdf8" if i in [2, 16] else "#30363d" if h_val == 0 else "#238636" if h_val > 50 else "#1f6feb" if h_val > 30 else "#58a6ff"
        svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_space - 2.5:.1f}" height="{bh:.1f}" rx="1.5" fill="{fill_col}" />')
    svg.append('    <text x="0" y="52" class="sublabel" font-size="9">00h</text>')
    svg.append('    <text x="80" y="52" class="sublabel" font-size="9">06h</text>')
    svg.append('    <text x="168" y="52" class="sublabel" font-size="9">12h</text>')
    svg.append('    <text x="254" y="52" class="sublabel" font-size="9">18h</text>')
    svg.append('    <text x="332" y="52" class="sublabel" font-size="9">23h</text>')
    svg.append('  </g>')
    svg.append('</g>')

    # Right Card: Day of Week
    svg.append('<g transform="translate(432, 68)">')
    svg.append('  <rect width="384" height="278" rx="12" fill="url(#cardGrad)" stroke="#30363d" stroke-width="1" />')
    svg.append('  <text x="18" y="26" class="title">📅 Day of Week Velocity</text>')
    svg.append('  <text x="18" y="42" class="subtitle">Weekly rhythm &amp; cadence across all repositories</text>')

    chart_top = 64
    max_d = max(d["commits"] for d in days) if any(d["commits"] for d in days) else 1
    chart_h = 100
    bar_width = 32
    spacing = (348 - (7 * bar_width)) / 6

    for i, d in enumerate(days):
        bx = 18 + i * (bar_width + spacing)
        bh = (d["commits"] / max_d) * chart_h
        by = chart_top + (chart_h - bh) + 20
        is_peak = d.get("peak", False)

        val_fill = "#38bdf8" if is_peak else "#ffffff"
        svg.append(f'  <text x="{bx + bar_width/2:.1f}" y="{by - 6:.1f}" text-anchor="middle" font-family="Fira Code, monospace" font-size="10" font-weight="700" fill="{val_fill}">{d["commits"]}</text>')

        if is_peak:
            svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_width}" height="{bh:.1f}" rx="6" fill="url(#barPeakGrad)" stroke="#60a5fa" stroke-width="1.2" filter="url(#glow)" />')
            svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_width}" height="{bh:.1f}" rx="6" fill="url(#barPeakGrad)" />')
            svg.append(f'  <rect x="{bx - 2:.1f}" y="{by - 24:.1f}" width="{bar_width + 4}" height="14" rx="7" fill="#38bdf8" />')
            svg.append(f'  <text x="{bx + bar_width/2:.1f}" y="{by - 13:.1f}" text-anchor="middle" class="badge-text">PEAK</text>')
        else:
            svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_width}" height="{bh:.1f}" rx="6" fill="url(#barStdGrad)" stroke="#30363d" stroke-width="0.8" />')

        label_class = "peak-label" if is_peak else "bar-label"
        svg.append(f'  <text x="{bx + bar_width/2:.1f}" y="{chart_top + chart_h + 36:.1f}" text-anchor="middle" class="{label_class}">{d["name"]}</text>')

    # Summary
    svg.append('  <g transform="translate(18, 218)">')
    svg.append('    <rect x="0" y="0" width="168" height="46" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />')
    svg.append('    <text x="12" y="16" class="sublabel" font-size="10">WEEKDAY VELOCITY</text>')
    svg.append(f'    <text x="12" y="34" class="val-mono" font-size="13">{weekday_pct:.1f}% <tspan font-size="10" fill="#8b949e">({weekday_commits} commits)</tspan></text>')

    svg.append('    <rect x="180" y="0" width="168" height="46" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />')
    svg.append('    <text x="192" y="16" class="sublabel" font-size="10">WEEKEND ACTIVITY</text>')
    svg.append(f'    <text x="192" y="34" class="val-mono" font-size="13">{weekend_pct:.1f}% <tspan font-size="10" fill="#8b949e">({weekend_commits} commits)</tspan></text>')
    svg.append('  </g>')

    svg.append('</g>')
    svg.append('</svg>')
    return "\n".join(svg)

def main():
    token = os.environ.get('GITHUB_TOKEN')
    # Default data fallback (from exact current historical calculation)
    hours = [57, 61, 73, 14, 14, 3, 3, 11, 0, 8, 17, 19, 37, 54, 57, 59, 75, 54, 58, 33, 49, 42, 44, 44]
    day_counts = [142, 183, 95, 135, 141, 83, 107]
    total_commits = 886

    if token:
        try:
            pkt = timezone(timedelta(hours=5))
            repos = fetch_json('https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator', token)
            h_acc = defaultdict(int)
            d_acc = defaultdict(int)
            c_total = 0
            for repo in repos:
                repo_name = repo['full_name']
                commits = fetch_json(f'https://api.github.com/repos/{repo_name}/commits?author=sshariqali&per_page=100', token)
                if isinstance(commits, list):
                    for c in commits:
                        ds = c.get('commit', {}).get('author', {}).get('date')
                        if ds:
                            dt = datetime.fromisoformat(ds.replace('Z', '+00:00')).astimezone(pkt)
                            h_acc[dt.hour] += 1
                            d_acc[dt.weekday()] += 1
                            c_total += 1
            if c_total > 0:
                hours = [h_acc[h] for h in range(24)]
                day_counts = [d_acc[i] for i in range(7)]
                total_commits = c_total
        except Exception as e:
            print(f"Error fetching live data: {e}, using baseline distribution.")

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    max_commits = max(day_counts)
    days_data = [
        {"name": day_names[i], "commits": day_counts[i], "peak": (day_counts[i] == max_commits)}
        for i in range(7)
    ]

    svg_content = generate_svg(total_commits, hours, days_data)
    out_path = os.path.join(os.path.dirname(__file__), "..", "assets", "activity_breakdown.svg")
    out_path = os.path.normpath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Successfully generated {out_path}")

if __name__ == '__main__':
    main()
