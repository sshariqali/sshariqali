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

    max_d = max(d["commits"] for d in days) if any(d["commits"] for d in days) else 1
    peak_day = next((d["name"] for d in days if d["commits"] == max_d), "Tue")

    periods = [
        {"name": "Morning", "range": "06:00 – 12:00", "commits": morning, "pct": m_pct},
        {"name": "Afternoon", "range": "12:00 – 18:00", "commits": daytime, "pct": d_pct},
        {"name": "Evening", "range": "18:00 – 00:00", "commits": evening, "pct": e_pct},
        {"name": "Night", "range": "00:00 – 06:00", "commits": night, "pct": n_pct},
    ]
    max_period = max(p["commits"] for p in periods)
    for p in periods:
        p["peak"] = (p["commits"] == max_period)

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="840" height="224" viewBox="0 0 840 224" fill="none">')
    svg.append('''  <style>
    .bg { fill: #161b22; stroke: #30363d; }
    .divider { stroke: #21262d; }
    .track { fill: #21262d; }
    .bar-normal { fill: #238636; }
    .bar-peak { fill: #39d353; }
    .text-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 600; fill: #f0f6fc; }
    .text-subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #8b949e; }
    .text-header { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; fill: #8b949e; letter-spacing: 0.5px; }
    .text-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12px; fill: #c9d1d9; }
    .text-val { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 11px; font-weight: 600; fill: #f0f6fc; }
    .text-val-muted { fill: #8b949e; font-weight: 400; }
    .text-day { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 500; fill: #8b949e; }
    .text-day-peak { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; fill: #39d353; }
    .badge-bg { fill: #21262d; stroke: #30363d; }
    .badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 600; fill: #8b949e; }

    @media (prefers-color-scheme: light) {
      .bg { fill: #ffffff; stroke: #d0d7de; }
      .divider { stroke: #d8dee4; }
      .track { fill: #eaeef2; }
      .bar-normal { fill: #2da44e; }
      .bar-peak { fill: #1a7f37; }
      .text-title { fill: #1f2328; }
      .text-subtitle { fill: #656d76; }
      .text-header { fill: #656d76; }
      .text-label { fill: #24292f; }
      .text-val { fill: #1f2328; }
      .text-val-muted { fill: #656d76; }
      .text-day { fill: #656d76; }
      .text-day-peak { fill: #1a7f37; }
      .badge-bg { fill: #f6f8fa; stroke: #d0d7de; }
      .badge-text { fill: #656d76; }
    }
  </style>''')

    # Card background
    svg.append('  <rect x="0.5" y="0.5" width="839" height="223" rx="8" class="bg" stroke-width="1" />')

    # Header
    svg.append('  <g transform="translate(24, 18)">')
    svg.append('    <text x="0" y="13" class="text-title">⚡ Commit Activity Breakdown</text>')
    svg.append('    <text x="0" y="27" class="text-subtitle">Weekly &amp; hourly rhythm across repositories · Karachi Time (PKT / UTC+5)</text>')
    svg.append('    <rect x="668" y="1" width="124" height="22" rx="11" class="badge-bg" stroke-width="1" />')
    svg.append(f'    <text x="730" y="15" text-anchor="middle" class="badge-text">{total_commits:,} COMMITS</text>')
    svg.append('  </g>')

    # Horizontal divider
    svg.append('  <line x1="24" y1="56" x2="816" y2="56" class="divider" stroke-width="1" />')

    # Left Column: Time of Day
    svg.append('  <g transform="translate(24, 70)">')
    svg.append('    <text x="0" y="0" class="text-header">TIME OF DAY</text>')

    track_max_w = 175
    y_start = 14
    for i, p in enumerate(periods):
        y = y_start + i * 32
        bar_w = max(4, (p["pct"] / 100) * track_max_w)
        bar_class = "bar-peak" if p["peak"] else "bar-normal"

        svg.append(f'    <text x="0" y="{y + 11}" class="text-label">{p["name"]}</text>')
        svg.append(f'    <rect x="110" y="{y + 2}" width="{track_max_w}" height="10" rx="5" class="track" />')
        svg.append(f'    <rect x="110" y="{y + 2}" width="{bar_w:.1f}" height="10" rx="5" class="{bar_class}" />')
        svg.append(f'    <text x="{110 + track_max_w + 14}" y="{y + 11}" class="text-val">{p["commits"]} <tspan class="text-val-muted">({p["pct"]:.1f}%)</tspan></text>')
    svg.append('  </g>')

    # Vertical divider
    svg.append('  <line x1="420" y1="68" x2="420" y2="208" class="divider" stroke-width="1" />')

    # Right Column: Day of Week
    svg.append('  <g transform="translate(444, 70)">')
    svg.append(f'    <text x="0" y="0" class="text-header">DAY OF WEEK</text>')
    svg.append(f'    <text x="372" y="0" text-anchor="end" class="text-subtitle">Peak: {peak_day} ({max_d} commits)</text>')

    bar_width = 34
    spacing = (372 - (7 * bar_width)) / 6
    chart_h = 80
    chart_base_y = 112

    for i, d in enumerate(days):
        bx = i * (bar_width + spacing)
        bh = max(4, (d["commits"] / max_d) * chart_h)
        by = chart_base_y - bh
        is_peak = d["peak"]
        bar_class = "bar-peak" if is_peak else "bar-normal"
        lbl_class = "text-day-peak" if is_peak else "text-day"
        val_color = "fill: #39d353; font-weight: 700;" if is_peak else ""

        svg.append(f'    <text x="{bx + bar_width/2:.1f}" y="{by - 6:.1f}" text-anchor="middle" class="text-val" style="{val_color}">{d["commits"]}</text>')
        svg.append(f'    <rect x="{bx:.1f}" y="{chart_base_y - chart_h}" width="{bar_width}" height="{chart_h}" rx="4" class="track" />')
        svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_width}" height="{bh:.1f}" rx="4" class="{bar_class}" />')
        svg.append(f'    <text x="{bx + bar_width/2:.1f}" y="{chart_base_y + 18}" text-anchor="middle" class="{lbl_class}">{d["name"]}</text>')

    svg.append('  </g>')
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
