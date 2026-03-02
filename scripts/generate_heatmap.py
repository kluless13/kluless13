#!/usr/bin/env python3
"""Generate SVG heatmap from the localcommit repo's git history.

Runs in GitHub Actions: clones kluless13/localcommit, reads commit dates,
generates a GitHub-style contribution heatmap SVG.
"""

import subprocess
from datetime import date, timedelta
from collections import defaultdict

REPO_PATH = "/tmp/localcommit"
OUTPUT_PATH = "local-activity.svg"

BG_COLOR = "#0d1117"
TEXT_COLOR = "#8b949e"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL_SIZE = 11
CELL_GAP = 3
CELL_RADIUS = 2
LABEL_WIDTH = 30
TOP_MARGIN = 25
LEFT_MARGIN = 10


def get_commit_counts():
    result = subprocess.run(
        ["git", "log", "--all", "--format=%ai"],
        capture_output=True, text=True, cwd=REPO_PATH
    )
    counts = defaultdict(int)
    for line in result.stdout.strip().split("\n"):
        if line:
            counts[line[:10]] += 1
    return counts


def build_grid(counts, end_date):
    start = end_date - timedelta(days=364)
    start = start - timedelta(days=(start.weekday() + 1) % 7)

    weeks = []
    current = start
    while current <= end_date:
        week = []
        for dow in range(7):
            d = current + timedelta(days=dow)
            key = d.strftime("%Y-%m-%d")
            week.append((d, counts.get(key, 0) if d <= end_date else -1))
        weeks.append(week)
        current += timedelta(days=7)
    return weeks


def level_for_value(value, max_val):
    if value <= 0:
        return 0
    ratio = value / max_val
    if ratio <= 0.25:
        return 1
    elif ratio <= 0.50:
        return 2
    elif ratio <= 0.75:
        return 3
    return 4


def generate_svg(weeks, max_val):
    width = LEFT_MARGIN + LABEL_WIDTH + len(weeks) * (CELL_SIZE + CELL_GAP) + 20
    height = TOP_MARGIN + 7 * (CELL_SIZE + CELL_GAP) + 30

    month_labels = []
    last_month = -1
    for i, week in enumerate(weeks):
        for d, _ in week:
            if d.month != last_month and d.day <= 7:
                x = LEFT_MARGIN + LABEL_WIDTH + i * (CELL_SIZE + CELL_GAP)
                month_labels.append((x, d.strftime("%b")))
                last_month = d.month
                break

    total_commits = sum(c for w in weeks for _, c in w if c > 0)
    active_days = sum(1 for w in weeks for _, c in w if c > 0)

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append(f'  <rect width="{width}" height="{height}" rx="6" fill="{BG_COLOR}"/>')

    for x, label in month_labels:
        lines.append(f'  <text x="{x}" y="{TOP_MARGIN - 8}" fill="{TEXT_COLOR}" font-size="10" font-family="monospace">{label}</text>')

    for row, label in [(0, "Mon"), (2, "Wed"), (4, "Fri")]:
        y = TOP_MARGIN + row * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 1
        lines.append(f'  <text x="{LEFT_MARGIN}" y="{y}" fill="{TEXT_COLOR}" font-size="9" font-family="monospace">{label}</text>')

    for col, week in enumerate(weeks):
        for row, (d, count) in enumerate(week):
            x = LEFT_MARGIN + LABEL_WIDTH + col * (CELL_SIZE + CELL_GAP)
            y = TOP_MARGIN + row * (CELL_SIZE + CELL_GAP)
            if count < 0:
                continue
            level = level_for_value(count, max_val)
            color = LEVELS[level]
            if count > 0:
                tooltip = f"{d.strftime('%b %d, %Y')}: {count} commits"
            else:
                tooltip = f"{d.strftime('%b %d, %Y')}: No commits"
            lines.append(f'  <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{CELL_RADIUS}" fill="{color}">')
            lines.append(f'    <title>{tooltip}</title>')
            lines.append(f'  </rect>')

    legend_y = TOP_MARGIN + 7 * (CELL_SIZE + CELL_GAP) + 8
    legend_x = LEFT_MARGIN + LABEL_WIDTH
    lines.append(f'  <text x="{legend_x}" y="{legend_y + 9}" fill="{TEXT_COLOR}" font-size="10" font-family="monospace">{total_commits} local commits | {active_days} active days</text>')

    lx = width - 120
    lines.append(f'  <text x="{lx - 30}" y="{legend_y + 9}" fill="{TEXT_COLOR}" font-size="9" font-family="monospace">Less</text>')
    for i, color in enumerate(LEVELS):
        lines.append(f'  <rect x="{lx + i * (CELL_SIZE + 2)}" y="{legend_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{CELL_RADIUS}" fill="{color}"/>')
    lines.append(f'  <text x="{lx + 5 * (CELL_SIZE + 2) + 2}" y="{legend_y + 9}" fill="{TEXT_COLOR}" font-size="9" font-family="monospace">More</text>')

    lines.append('</svg>')
    return '\n'.join(lines)


def main():
    counts = get_commit_counts()
    end_date = date.today()
    weeks = build_grid(counts, end_date)
    all_counts = [c for w in weeks for _, c in w if c > 0]
    max_val = max(all_counts) if all_counts else 1

    svg = generate_svg(weeks, max_val)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)

    total = sum(all_counts)
    print(f"Generated: {total} commits, {len(all_counts)} active days, max {max_val}/day")


if __name__ == "__main__":
    main()
