import re
from pathlib import Path

p = Path("mizuno.xml")
x = p.read_text(encoding="utf-8")

start = x.find('xml:id="voyage"')
end = x.find('xml:id="hostel"')
if start == -1 or end == -1:
    raise SystemExit("Could not find the voyage/hostel sections - nothing changed.")

# --- kanji numerals: 百九十五=195, 二二〇=220, 一万二千=12000 ---
D = dict(zip("〇一二三四五六七八九", range(10)))
UNITS = {"十": 10, "百": 100, "千": 1000}

def kanji_num(s):
    if len(s) > 1 and all(c in D for c in s):
        return int("".join(str(D[c]) for c in s))
    s = s.replace("廿", "二十").replace("卅", "三十")
    total = section = num = 0
    for c in s:
        if c in D:
            num = D[c]
        elif c in UNITS:
            section += (num or 1) * UNITS[c]
            num = 0
        elif c == "万":
            total += (section + num) * 10000
            section = num = 0
    return total + section + num

# --- patterns ---
N = "〇一二三四五六七八九十廿卅百"
LAT = rf"(?:(?:北緯|南緯)[{N}]+度[{N}]+分|[{N}]+度[{N}]+分(?:（(?:北緯|南緯)）|北緯|南緯))"
LON = rf"(?:東経|西経)[{N}]+度(?:[{N}]+(?:ママ)?分)?"
POS = re.compile(rf"{LAT}\s*{LON}")
DIST = re.compile(r"([〇一二三四五六七八九十廿卅百千万]+)哩")
DIST_TYPE = {"約": "other", "迄": "remaining", "凡": "total"}
WEEKDAY = re.compile(r"^[日月火水木金土](?:曜日?)?$")
DATELINE = re.compile(r"(</date>)([^<]*)(</dateline>)")
ENTRY = re.compile(r'<div type="entry" xml:id="(e[\d-]+)">.*?</div>', re.S)

stats = {"encoded": 0, "skipped": 0, "weather": 0, "positions": 0}
dist_types = {}
missing = []

def wrap_weather(m):
    out = []
    for part in re.split(r"(\s+)", m.group(2)):
        if part and not part.isspace() and not WEEKDAY.match(part):
            out.append(f'<seg type="weather">{part}</seg>')
            stats["weather"] += 1
        else:
            out.append(part)
    return m.group(1) + "".join(out) + m.group(3)

def wrap_pos(m):
    stats["positions"] += 1
    return f'<seg type="noonPosition">{m.group(0)}</seg>'

def wrap_dist(m):
    before = m.string[m.start() - 1] if m.start() > 0 else ""
    kind = DIST_TYPE.get(before, "dayRun")
    dist_types[kind] = dist_types.get(kind, 0) + 1
    return (f'<measure type="{kind}" unit="mile" quantity="{kanji_num(m.group(1))}">'
            f'{m.group(0)}</measure>')

def encode_entry(m):
    e = m.group(0)
    if 'type="weather"' in e or "<measure" in e:
        stats["skipped"] += 1
        return e
    stats["encoded"] += 1
    e = DATELINE.sub(wrap_weather, e, count=1)
    found_before = stats["positions"]
    e = POS.sub(wrap_pos, e)
    if "正午" in e and stats["positions"] == found_before:
        missing.append(m.group(1))
    return DIST.sub(wrap_dist, e)

section = x[start:end]
x = x[:start] + ENTRY.sub(encode_entry, section) + x[end:]
p.write_text(x, encoding="utf-8")

print("Entries encoded:", stats["encoded"], "| already done, skipped:", stats["skipped"])
print("Weather segments:", stats["weather"])
print("Noon positions:", stats["positions"])
print("Distances by type:", dist_types)
if missing:
    print("CHECK BY HAND - noon position not recognized in:", ", ".join(missing))
    