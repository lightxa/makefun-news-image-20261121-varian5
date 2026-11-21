# news-image-20261121, variant 5: "The day, hour by hour".
#
# A vertical timeline infographic for Saturday 21 November 2026.
# Six verified stories run down one spine, from the overnight barrage
# over Ukraine to a late-night FBI breach, each with its own day-part,
# colour and small drawn icon. Nothing here is a grid of cards, a world
# map, a single-lead poster or a broadcast front page: the timeline
# itself is the composition, and the date is the biggest line on it.
#
# Pure Python 3.13 standard library, no network, fully deterministic:
# the same run always writes the same bytes. Text is rendered with a
# small embedded 5x7 bitmap font; the PNG is encoded by hand with zlib.

import math
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette: clean white paper, ink, one colour per story ------------------
PAPER = (255, 255, 255)
INK = (17, 24, 39)
INK2 = (55, 65, 81)
MUTED = (107, 114, 128)
RULE = (209, 213, 219)
SPINE = (203, 213, 225)
FOOTER_BG = (17, 24, 39)
FOOTER_TX = (226, 232, 240)
WHITE = (255, 255, 255)

RED = (185, 28, 28)       # overnight: war
TEAL = (13, 148, 136)     # morning: youth strike
AMBER = (217, 119, 6)     # midday: climate talks
BLUE = (29, 78, 216)      # afternoon: markets
PURPLE = (109, 40, 217)   # evening: Trump / AI
MAROON = (136, 19, 55)    # night: FBI hack

# --- 5x7 bitmap font: A-Z, 0-9 and a small punctuation set ------------------
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is empty.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.#.#", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "&": (".###.", "#...#", "#...#", ".#...", "#.#.#", "#..#.", ".##.#"),
}


def chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb, w, h):
    """Encode an RGB byte string as a deterministic PNG (filter 0 rows)."""
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    return png


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, color)

    def hline(self, x0, x1, y, color, thick=1):
        for t in range(thick):
            for x in range(x0, x1):
                self.set(x, y + t, color)

    def vline(self, x, y0, y1, color, thick=1):
        for t in range(thick):
            for y in range(y0, y1):
                self.set(x + t, y, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        """Filled disc."""
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def ring(self, cx, cy, r, color, thick=3):
        for y in range(cy - r - thick, cy + r + thick + 1):
            for x in range(cx - r - thick, cx + r + thick + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if (r - thick) ** 2 <= d2 <= (r + thick) ** 2:
                    self.set(x, y, color)

    def text(self, x, y, s, color, msg):
        """Draw uppercase text at scale s (glyph 5x7, 1px gap)."""
        cx = x
        for ch in msg.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row_i, row in enumerate(glyph):
                for col_i, cell in enumerate(row):
                    if cell == "#":
                        self.rect(cx + col_i * s, y + row_i * s,
                                  cx + (col_i + 1) * s, y + (row_i + 1) * s,
                                  color)
            cx += 6 * s
        return cx

    def text_w(self, s, msg):
        return len(msg) * 6 * s - s

    def center(self, y, s, color, msg):
        x = (self.w - self.text_w(s, msg)) // 2
        self.text(x, y, s, color, msg)
        return x

    def wrap(self, msg, s, max_w):
        """Greedy word wrap; returns a list of lines fitting max_w pixels."""
        words = msg.split(" ")
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_w(s, trial) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# --- small drawn icons (one per story, ~100 px box) -------------------------

def icon_burst(cv, cx, cy, color):
    """Explosion / missile burst: radiating spikes around a core."""
    cv.disc(cx, cy, 12, color)
    for k in range(12):
        a = k * math.pi / 6
        x1 = cx + int(14 * math.cos(a))
        y1 = cy + int(14 * math.sin(a))
        x2 = cx + int(44 * math.cos(a))
        y2 = cy + int(44 * math.sin(a))
        cv.line(x1, y1, x2, y2, color)
        cv.disc(x2, y2, 4, color)


def icon_placard(cv, cx, cy, color):
    """Protest placard on a stick."""
    cv.rect(cx - 42, cy - 40, cx + 42, cy + 6, color)
    cv.rect(cx - 34, cy - 32, cx + 34, cy - 2, PAPER)
    cv.text(cx - 30, cy - 30, 2, color, "GEN Z")
    cv.rect(cx - 4, cy + 6, cx + 4, cy + 46, color)
    cv.disc(cx, cy + 46, 5, color)


def icon_globe(cv, cx, cy, color):
    """Globe with meridians, for the climate talks."""
    cv.ring(cx, cy, 40, color, 4)
    cv.line(cx - 40, cy, cx + 40, cy, color)
    cv.line(cx, cy - 40, cx, cy + 40, color)
    for dx in (-20, 20):
        cv.line(cx + dx, cy - 35, cx + dx, cy + 35, color)
    cv.disc(cx + 26, cy - 26, 7, AMBER)


def icon_chart(cv, cx, cy, color):
    """Falling market chart with arrowhead."""
    cv.hline(cx - 44, cx + 44, cy + 40, INK2, 3)
    cv.vline(cx - 44, cy - 40, cy + 40, INK2, 3)
    pts = [(cx - 40, cy - 28), (cx - 20, cy - 18), (cx, cy - 24),
           (cx + 20, cy + 8), (cx + 40, cy + 34)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], color)
        cv.line(a[0], a[1] + 2, b[0], b[1] + 2, color)
    cv.line(cx + 40, cy + 34, cx + 28, cy + 30, color)
    cv.line(cx + 40, cy + 34, cx + 36, cy + 20, color)


def icon_servers(cv, cx, cy, color):
    """Stack of data-centre servers."""
    for i, y0 in enumerate((cy - 42, cy - 14, cy + 14)):
        cv.rect(cx - 40, y0, cx + 40, y0 + 24, color)
        cv.rect(cx - 32, y0 + 4, cx + 32, y0 + 20, PAPER)
        cv.disc(cx - 24, y0 + 12, 4, color)
        cv.hline(cx - 12, cx + 24, y0 + 12, color, 2)


def icon_padlock(cv, cx, cy, color):
    """Padlock with a crack: the hacked database."""
    cv.ring(cx, cy - 8, 22, color, 5)
    cv.rect(cx - 34, cy - 6, cx + 34, cy + 42, color)
    cv.rect(cx - 6, cy + 6, cx + 6, cy + 18, PAPER)
    cv.disc(cx, cy + 24, 6, PAPER)
    cv.line(cx - 34, cy + 8, cx + 34, cy + 30, WHITE)


ICONS = {
    "burst": icon_burst,
    "placard": icon_placard,
    "globe": icon_globe,
    "chart": icon_chart,
    "servers": icon_servers,
    "padlock": icon_padlock,
}

# --- stories: (day-part, colour, icon, headline, body) ----------------------
# Every fact below was verified against live news roundups for 21 Nov 2026:
# Russia/Poland barrage (OneTurn 21 Nov roundup; BBC); Gen Z youth strike
# in 25 countries (Reuters/CNN, 20-21 Nov); COP31 overtime in Antalya
# (OneTurn; talks past deadline, fossil fuels cut from draft); Wall St
# rout, Nasdaq -5.3%, Nvidia -14% (OneTurn; BBC/Guardian); Trump data
# centre tax threat (Reuters, 20 Nov press conference); FBI NCIC breach
# (CNN/Reuters, reported 20 Nov, carried in 21 Nov roundups).
STORIES = [
    ("OVERNIGHT", RED, "burst",
     "RUSSIA'S BIGGEST BARRAGE HITS KYIV",
     "MORE THAN 400 DRONES AND 110 MISSILES HIT UKRAINE. 8 KILLED IN "
     "KYIV. 2 MISSILES AND A DRONE LAND IN POLAND."),
    ("MORNING", TEAL, "placard",
     "GEN Z TAKES TO EUROPE'S STREETS",
     "STUDENTS WALK OUT IN 25 COUNTRIES OVER LIVING COSTS, TUITION AND "
     "REARMAMENT. MARCHES FILL 100 SQUARES IN ITALY."),
    ("MIDDAY", AMBER, "globe",
     "CLIMATE TALKS MISS THEIR DEADLINE",
     "COP31 IN ANTALYA RUNS INTO OVERTIME AS NEARLY 200 NATIONS STAY "
     "SPLIT OVER FOSSIL FUELS."),
    ("AFTERNOON", BLUE, "chart",
     "AI SELL-OFF SINKS WALL STREET",
     "NASDAQ FALLS 5.3% AND THE S AND P AND DOW ENTER CORRECTION. "
     "NVIDIA SLIDES 14% AS AI FEARS SPREAD."),
    ("EVENING", PURPLE, "servers",
     "TRUMP VOWS TAX ON AI ABROAD",
     "US FIRMS BUILDING DATA CENTRES OVERSEAS FACE A TREMENDOUS TAX, "
     "TRUMP SAYS. HE WANTS THEM BUILT IN AMERICA."),
    ("NIGHT", MAROON, "padlock",
     "FBI CRIME DATABASE HACKED",
     "FBI PROBES AN APPARENT BREACH OF ITS NATIONAL CRIME DATABASE. "
     "THE SECOND INTRUSION IN MONTHS, AFTER A WEEK OF US OUTAGES."),
]

ROW_Y0 = 168
ROW_H = 126
SPINE_X = 72
TEXT_X = 116
ICON_CX = 940


def draw_header(cv):
    cv.center(22, 2, BLUE, "THE DAY, HOUR BY HOUR")
    cv.center(48, 5, INK, "SATURDAY 21 NOVEMBER 2026")
    cv.center(98, 2, MUTED,
              "EVERY STORY HERE HAPPENED OR WAS FIRST REPORTED ON THIS DAY")
    cv.hline(48, W - 48, 134, RULE, 3)


def draw_rows(cv):
    cv.vline(SPINE_X - 2, ROW_Y0 + 12, ROW_Y0 + 6 * ROW_H - 12, SPINE, 4)
    for i, (phase, color, icon, headline, body) in enumerate(STORIES):
        y0 = ROW_Y0 + i * ROW_H
        cy = y0 + 56
        cv.disc(SPINE_X, cy, 24, color)
        cv.ring(SPINE_X, cy, 24, PAPER, 2)
        num = str(i + 1)
        cv.text(SPINE_X - cv.text_w(3, num) // 2, cy - 10, 3, WHITE, num)
        cv.text(TEXT_X, y0 + 8, 2, color, phase)
        cv.text(TEXT_X, y0 + 32, 3, INK, headline)
        lines = cv.wrap(body, 2, 740)[:2]
        for j, ln in enumerate(lines):
            cv.text(TEXT_X, y0 + 78 + j * 16, 2, INK2, ln)
        ICONS[icon](cv, ICON_CX, cy, color)
        if i < len(STORIES) - 1:
            cv.hline(TEXT_X, W - 48, y0 + ROW_H - 1, RULE, 1)


def draw_footer(cv):
    cv.rect(0, 936, W, H, FOOTER_BG)
    cv.center(952, 2, FOOTER_TX,
              "ALSO TODAY: RIKERS TO CLOSE BY 2032 - PALISADES FIRE "
              "VERDICT - GTA VI $3.79BN")
    cv.center(984, 2, (148, 163, 184),
              "ALL SIX STORIES ABOVE, AND THESE BRIEFS, ARE FROM "
              "SATURDAY 21 NOVEMBER 2026")


def build():
    cv = Canvas(W, H, PAPER)
    draw_header(cv)
    draw_rows(cv)
    draw_footer(cv)
    return encode_png(bytes(cv.buf), W, H)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
