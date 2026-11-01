import re
from pathlib import Path

p = Path("mizuno.xml")
x = p.read_text(encoding="utf-8")

start = x.find('xml:id="hostel"')
end = x.find('<div type="appendix"')
if start == -1 or end == -1:
    raise SystemExit("Could not find the hostel section or the appendix - nothing changed.")

# --- kanji numerals (壱 = 1; 千五百 = 1500) ---
D = dict(zip("〇一二三四五六七八九", range(10)))
D["壱"] = 1
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
NUMC = "〇一二三四五六七八九十百千壱"
CUR = re.compile(rf"(?P<c>[{NUMC}]+)(?:コントス|コント)(?:(?P<m1>[{NUMC}]+)ミルレース)?"
                 rf"|(?P<m2>[{NUMC}]+)ミルレース")
YEN = re.compile(r"([〇一二三四五六七八九十百千]+)円")
WEEKDAY = re.compile(r"^[日月火水木金土](?:曜日?)?$")
NOT_WEATHER = {"祭日"}
DATELINE = re.compile(r"(</date>)([^<]*)(</dateline>)")
ENTRY = re.compile(r'<div type="entry" xml:id="(e[\d-]+)">.*?</div>', re.S)

stats = {"encoded": 0, "skipped": 0, "weather": 0, "milreis": 0, "yen": 0}

def wrap_weather(m):
    out = []
    for part in re.split(r"(\s+)", m.group(2)):
        if part and not part.isspace() and not WEEKDAY.match(part) and part not in NOT_WEATHER:
            out.append(f'<seg type="weather">{part}</seg>')
            stats["weather"] += 1
        else:
            out.append(part)
    return m.group(1) + "".join(out) + m.group(3)

def wrap_cur(m):
    if m.group("c"):
        q = kanji_num(m.group("c")) * 1000 + (kanji_num(m.group("m1")) if m.group("m1") else 0)
    else:
        q = kanji_num(m.group("m2"))
    stats["milreis"] += 1
    return f'<measure type="currency" unit="milreis" quantity="{q}">{m.group(0)}</measure>'

def wrap_yen(m):
    stats["yen"] += 1
    return f'<measure type="currency" unit="yen" quantity="{kanji_num(m.group(1))}">{m.group(0)}</measure>'

def encode_entry(m):
    e = m.group(0)
    if 'type="weather"' in e or 'type="currency"' in e:
        stats["skipped"] += 1
        return e
    stats["encoded"] += 1
    e = DATELINE.sub(wrap_weather, e, count=1)
    e = CUR.sub(wrap_cur, e)
    return YEN.sub(wrap_yen, e)

section = x[start:end]
x = x[:start] + ENTRY.sub(encode_entry, section) + x[end:]
p.write_text(x, encoding="utf-8")

print("Entries encoded:", stats["encoded"], "| already done, skipped:", stats["skipped"])
print("Weather segments:", stats["weather"])
print("Currency amounts - mil-reis:", stats["milreis"], "| yen:", stats["yen"])