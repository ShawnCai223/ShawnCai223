"""Pick a "song of the day" and rebuild playlist.md.

- Reads music/songs.json (the single source of truth for the list).
- Rebuilds playlist.md from it, with today's pick on top.
- Points the "My List" card in README.md at today's song on YouTube.

Runs from GitHub Actions. Scheduled runs only pick a new song once per
Pacific-time day, at or after noon; pass --force to pick right away.
"""

import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SONGS = ROOT / "music" / "songs.json"
PLAYLIST = ROOT / "playlist.md"
README = ROOT / "README.md"
TZ = ZoneInfo("America/Los_Angeles")

CARD_LINK = re.compile(r'(<a href=")[^"]*("><strong>🎧 My List</strong>)')
STATE = re.compile(r"<!-- pick: (\d{4}-\d{2}-\d{2}) \| (.*?) -->")


def youtube(song):
    return "https://www.youtube.com/results?search_query=" + quote_plus(f"{song['title']} {song['artist']}")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def current_state():
    if not PLAYLIST.exists():
        return None, None
    m = STATE.search(PLAYLIST.read_text(encoding="utf-8"))
    return (m.group(1), m.group(2)) if m else (None, None)


def build_playlist(groups, pick, date):
    total = sum(len(g["songs"]) for g in groups)
    out = []
    out.append(f"<!-- pick: {date} | {pick['title']} — {pick['artist']} -->")
    out.append('<div align="center">')
    out.append('  <img src="images/vinyl.svg" height="90" alt="Spinning record" />')
    out.append("  <h1>🎧 My List</h1>")
    out.append(f"  <sub>{total} songs I keep coming back to · click ▶ to listen on YouTube</sub>")
    out.append("  <br /><br />")
    out.append("")
    out.append("<table>")
    out.append('<tr><td align="center" width="460">')
    out.append(f"<sub>🎲 SONG OF THE DAY · {date}</sub>")
    out.append(f"<h2>{esc(pick['title'])}</h2>")
    out.append(f"<p>{esc(pick['artist'])}</p>")
    out.append(f'<a href="{youtube(pick)}"><img src="images/play_button.svg" height="40" alt="Play on YouTube" /></a>')
    out.append("<br /><br />")
    out.append("</td></tr>")
    out.append("</table>")
    out.append("</div>")
    out.append("")

    for g in groups:
        out.append(f"<h3 align=\"center\">{g['title']}</h3>")
        out.append('<div align="center">')
        out.append('<table width="600">')
        out.append('<tr><th align="right" width="40">#</th><th align="left" width="300">Song</th><th align="left" width="220">Artist</th><th width="40"></th></tr>')
        for i, s in enumerate(g["songs"], 1):
            star = " ⭐" if s == pick else ""
            out.append(
                f'<tr><td align="right"><sub>{i:02d}</sub></td>'
                f"<td><b>{esc(s['title'])}</b>{star}</td>"
                f"<td>{esc(s['artist'])}</td>"
                f'<td align="center"><a href="{youtube(s)}">▶</a></td></tr>'
            )
        out.append("</table>")
        out.append("</div>")
        out.append("")

    out.append('<div align="center">')
    out.append("<br />")
    out.append("<sub>A new song of the day is picked every day at noon, Pacific time.</sub><br />")
    out.append('<a href="https://github.com/ShawnCai223">← back to my page</a>')
    out.append("</div>")
    out.append("")
    return "\n".join(out)


def main():
    force = "--force" in sys.argv
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")

    groups = json.loads(SONGS.read_text(encoding="utf-8"))["groups"]
    songs = [s for g in groups for s in g["songs"]]

    last_date, last_label = current_state()
    if not force:
        if now.hour < 12:
            print(f"Before noon Pacific ({now:%H:%M}), nothing to do.")
            return
        if last_date == today:
            print(f"Already picked a song for {today}.")
            return

    # Don't repeat yesterday's song.
    pool = [s for s in songs if f"{s['title']} — {s['artist']}" != last_label] or songs
    pick = random.SystemRandom().choice(pool)
    print(f"Song of the day ({today}): {pick['title']} — {pick['artist']}")

    PLAYLIST.write_text(build_playlist(groups, pick, today), encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    url = youtube(pick)
    # The "My List" card itself links straight to today's song on YouTube.
    readme = CARD_LINK.sub(lambda m: f"{m.group(1)}{url}{m.group(2)}", readme)
    README.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
