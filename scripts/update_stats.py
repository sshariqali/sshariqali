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
        {"name": "Morning", "hours": "06:00 – 12:00", "commits": morning, "pct": m_pct},
        {"name": "Afternoon", "hours": "12:00 – 18:00", "commits": daytime, "pct": d_pct},
        {"name": "Evening", "hours": "18:00 – 00:00", "commits": evening, "pct": e_pct},
        {"name": "Night", "hours": "00:00 – 06:00", "commits": night, "pct": n_pct},
    ]
    max_p = max(p["commits"] for p in periods)
    for p in periods:
        p["peak"] = (p["commits"] == max_p)

    width = 840
    height = 185

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">')
    svg.append('''  <style>
    .bg { fill: #161b22; stroke: #30363d; }
    .divider { stroke: #30363d; }
    .track { fill: #21262d; }
    .bar-normal { fill: #FB8C00; fill-opacity: 0.45; }
    .bar-peak { fill: #FB8C00; }
    .header-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 700; fill: #FB8C00; letter-spacing: 0.8px; }
    .sub-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #9E9E9E; }
    .row-name { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12px; fill: #E4E2E2; }
    .val-text { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 11px; font-weight: 600; fill: #FEFEFE; }
    .val-muted { fill: #9E9E9E; font-weight: 400; }
    .day-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 500; fill: #9E9E9E; }
    .day-text-peak { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 700; fill: #FB8C00; }
  </style>''')

    # Card background
    svg.append(f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" class="bg" stroke-width="1" />')

    # Section Headers (Symmetrical at y=27)
    svg.append('  <text x="24" y="27" class="header-label">TIME OF DAY</text>')
    svg.append('  <text x="396" y="27" text-anchor="end" class="sub-label">Karachi Time (PKT)</text>')

    svg.append('  <text x="444" y="27" class="header-label">DAY OF WEEK</text>')
    svg.append(f'  <text x="816" y="27" text-anchor="end" class="sub-label">Peak: {peak_day} ({max_d} commits)</text>')

    # Horizontal Divider
    svg.append('  <line x1="24" y1="38" x2="816" y2="38" class="divider" stroke-width="1" stroke-opacity="0.6" />')

    # Vertical Divider between the two charts
    svg.append(f'  <line x1="420" y1="18" x2="420" y2="{height - 18}" class="divider" stroke-width="1" stroke-opacity="0.6" />')

    # Left: Time of Day (4 horizontal bars)
    track_w = 170
    y_start = 50
    for i, p in enumerate(periods):
        y = y_start + i * 28
        bar_w = max(4, (p["pct"] / 100) * track_w)
        bar_class = "bar-peak" if p["peak"] else "bar-normal"

        svg.append(f'  <text x="24" y="{y + 11}" class="row-name">{p["name"]}</text>')
        svg.append(f'  <rect x="110" y="{y + 2}" width="{track_w}" height="10" rx="5" class="track" />')
        svg.append(f'  <rect x="110" y="{y + 2}" width="{bar_w:.1f}" height="10" rx="5" class="{bar_class}" />')
        svg.append(f'  <text x="{110 + track_w + 14}" y="{y + 11}" class="val-text">{p["commits"]} <tspan class="val-muted">({p["pct"]:.1f}%)</tspan></text>')

    # Right: Day of Week (7 vertical bars)
    bar_width = 34
    spacing = (372 - (7 * bar_width)) / 6
    chart_h = 76
    chart_base_y = 142

    for i, d in enumerate(days):
        bx = 444 + i * (bar_width + spacing)
        bh = max(4, (d["commits"] / max_d) * chart_h)
        by = chart_base_y - bh
        is_peak = d["peak"]
        bar_class = "bar-peak" if is_peak else "bar-normal"
        lbl_class = "day-text-peak" if is_peak else "day-text"
        val_color = "fill: #FB8C00; font-weight: 700;" if is_peak else "fill: #9E9E9E;"

        svg.append(f'  <text x="{bx + bar_width/2:.1f}" y="{by - 5:.1f}" text-anchor="middle" class="val-text" style="{val_color}">{d["commits"]}</text>')
        svg.append(f'  <rect x="{bx:.1f}" y="{chart_base_y - chart_h}" width="{bar_width}" height="{chart_h}" rx="4" class="track" />')
        svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_width}" height="{bh:.1f}" rx="4" class="{bar_class}" />')
        svg.append(f'  <text x="{bx + bar_width/2:.1f}" y="{chart_base_y + 18}" text-anchor="middle" class="{lbl_class}">{d["name"]}</text>')

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
