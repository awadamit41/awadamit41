import os
import json
import urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = "awadamit41"
TOKEN = os.environ["GITHUB_TOKEN"]
OUTPUT = "profile"

os.makedirs(OUTPUT, exist_ok=True)


def github_graphql(query):
    data = json.dumps({"query": query}).encode()

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=data,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "awadamit41-profile-cards",
        },
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read())

    if "errors" in result:
        raise RuntimeError(result["errors"])

    return result["data"]


query = """
query {
  user(login: "awadamit41") {
    name
    login
    followers {
      totalCount
    }
    repositories(first: 1, ownerAffiliations: OWNER) {
      totalCount
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoryContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

data = github_graphql(query)["user"]
calendar = data["contributionsCollection"]["contributionCalendar"]

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": day["date"],
            "count": day["contributionCount"]
        })

days.sort(key=lambda x: x["date"])

# ---------------------------------------------------------
# Calculate streaks
# ---------------------------------------------------------

active = {
    d["date"]: d["count"]
    for d in days
}

today = datetime.now(timezone.utc).date()

current = 0
cursor = today

while active.get(cursor.isoformat(), 0) > 0:
    current += 1
    cursor -= timedelta(days=1)

if current == 0:
    cursor = today - timedelta(days=1)

    while active.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

longest = 0
running = 0

for day in days:
    if day["count"] > 0:
        running += 1
        longest = max(longest, running)
    else:
        running = 0


# ---------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------

def write_svg(filename, title, rows):
    width = 900
    height = 260

    lines = []

    for i, (label, value) in enumerate(rows):
        y = 75 + i * 34

        lines.append(
            f'<text x="55" y="{y}" '
            f'font-family="Arial, sans-serif" '
            f'font-size="18" fill="#c9d1d9">{label}</text>'
        )

        lines.append(
            f'<text x="500" y="{y}" '
            f'font-family="Arial, sans-serif" '
            f'font-size="18" font-weight="bold" '
            f'fill="#58a6ff">{value}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <rect width="100%" height="100%" rx="14" fill="#0d1117"/>
    <text x="55" y="42"
      font-family="Arial, sans-serif"
      font-size="24"
      font-weight="bold"
      fill="#ffffff">{title}</text>
    {''.join(lines)}
    </svg>'''

    with open(filename, "w", encoding="utf-8") as file:
        file.write(svg)


# ---------------------------------------------------------
# Stats card
# ---------------------------------------------------------

contrib = data["contributionsCollection"]

write_svg(
    f"{OUTPUT}/stats.svg",
    "GitHub Statistics",
    [
        ("Total Contributions", calendar["totalContributions"]),
        ("Commits", contrib["totalCommitContributions"]),
        ("Pull Requests", contrib["totalPullRequestContributions"]),
        ("Issues", contrib["totalIssueContributions"]),
        ("Repositories", contrib["totalRepositoryContributions"]),
        ("Followers", data["followers"]["totalCount"]),
    ],
)


# ---------------------------------------------------------
# Streak card
# ---------------------------------------------------------

write_svg(
    f"{OUTPUT}/streak.svg",
    "Contribution Streak",
    [
        ("Current Streak", f"{current} days"),
        ("Longest Streak", f"{longest} days"),
        ("Total Contributions", calendar["totalContributions"]),
    ],
)


# ---------------------------------------------------------
# Activity card
# ---------------------------------------------------------

recent = days[-30:]

bar_width = 24
gap = 5
height = 300

bars = []

maximum = max([d["count"] for d in recent] or [1])

for i, day in enumerate(recent):
    x = 30 + i * (bar_width + gap)

    bar_height = int(
        (day["count"] / maximum) * 180
    )

    y = 230 - bar_height

    bars.append(
        f'<rect x="{x}" y="{y}" '
        f'width="{bar_width}" height="{bar_height}" '
        f'rx="4" fill="#58a6ff"/>'
    )

activity_svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
width="900" height="{height}" viewBox="0 0 900 {height}">

<rect width="100%" height="100%" rx="14" fill="#0d1117"/>

<text x="30" y="35"
font-family="Arial, sans-serif"
font-size="24"
font-weight="bold"
fill="#ffffff">
Contribution Activity — Last 30 Days
</text>

{''.join(bars)}

</svg>
'''

with open(f"{OUTPUT}/activity.svg", "w", encoding="utf-8") as file:
    file.write(activity_svg)

print("Profile cards generated successfully.")
