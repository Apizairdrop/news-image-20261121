#!/usr/bin/env python3
"""World news of Saturday 21 November 2026, summed up in one image.

Pure standard library: draws a 1024x1024 newspaper front page with a
hand-rolled 5x7 bitmap font and a tiny PNG encoder, then writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png). Deterministic:
no randomness, no time, no network, so every run writes identical bytes.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font. '#' is a set pixel, '.' is clear. Uppercase + digits
# + the punctuation the poster needs.
FONT = {
    "A": ("..#..", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
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
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": ("..#..", ".#.#.", ".#...", "..#..", "#.#.#", "#..#.", ".##.#"),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.#.#", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
}

# ------------------------------------------------------------- canvas -----
NAVY = (20, 33, 61)
PAPER = (247, 242, 231)
GOLD = (232, 196, 104)
WHITE = (255, 255, 255)
INK = (24, 24, 24)
GREY = (90, 90, 90)


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x0, x1, y, c, t=1):
        for yy in range(y, y + t):
            for xx in range(x0, x1 + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        for xx in range(x, x + t):
            for yy in range(y0, y1 + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a - t // 2, y0 + b - t // 2, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= r * r:
                    self.set(xx, yy, c)

    def triangle(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (xa, ya), (xb, yb) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ya == yb:
                    continue
                if min(ya, yb) <= yy < max(ya, yb):
                    xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(xx, yy, c)

    # -- text -------------------------------------------------------------
    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, y, s, scale, c, cx=512):
        self.text(cx - self.text_w(s, scale) // 2, y, s, scale, c)

    def wrap(self, s, scale, max_w):
        words, lines, cur = s.split(" "), [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def write_png(cv, path):
    raw = b"".join(b"\x00" + bytes(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
                   for y in range(cv.h))
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# -------------------------------------------------------------- icons -----
def icon_blast(cv, x, y, s, c, bg):
    cx, cy = x + s // 2, y + s // 2
    cv.circle(cx, cy, s // 5, c)
    for k in range(8):
        ang = k * math.pi / 4
        x1 = cx + int(0.30 * s * math.cos(ang))
        y1 = cy + int(0.30 * s * math.sin(ang))
        x2 = cx + int(0.48 * s * math.cos(ang))
        y2 = cy + int(0.48 * s * math.sin(ang))
        cv.line(x1, y1, x2, y2, c, 5)


def icon_quake(cv, x, y, s, c, bg):
    cv.rect(x + 8, y + 34, 22, 46, NAVY)
    cv.rect(x + 52, y + 22, 22, 58, NAVY)
    pts = [(x + 4, y + 84), (x + 22, y + 62), (x + 34, y + 80),
           (x + 48, y + 58), (x + 62, y + 78), (x + 80, y + 60)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(x0, y0, x1, y1, GOLD, 4)


def icon_shield(cv, x, y, s, c, bg):
    cx = x + s // 2
    cv.triangle([(cx - 30, y + 10), (cx + 30, y + 10), (cx, y + 74)], c)
    cv.line(cx - 16, y + 36, cx - 4, y + 50, bg, 6)
    cv.line(cx - 4, y + 50, cx + 20, y + 22, bg, 6)


def icon_chart(cv, x, y, s, c, bg):
    cv.vline(x + 10, y + 10, y + 74, c, 4)
    cv.hline(x + 10, x + 78, y + 74, c, 4)
    pts = [(x + 14, y + 22), (x + 32, y + 34), (x + 48, y + 30),
           (x + 64, y + 52), (x + 76, y + 62)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(x0, y0, x1, y1, (192, 57, 43), 5)
    cv.triangle([(x + 76, y + 62), (x + 62, y + 58), (x + 70, y + 72)],
                (192, 57, 43))


def icon_bars(cv, x, y, s, c, bg):
    for k in range(4):
        cv.vline(x + 12 + k * 18, y + 12, y + 72, c, 7)
    cv.hline(x + 8, x + 80, y + 12, c, 5)
    cv.hline(x + 8, x + 80, y + 72, c, 5)


def icon_virus(cv, x, y, s, c, bg):
    cx, cy = x + s // 2, y + s // 2
    cv.circle(cx, cy, s // 4, c)
    for k in range(8):
        ang = k * math.pi / 4
        x1 = cx + int(0.28 * s * math.cos(ang))
        y1 = cy + int(0.28 * s * math.sin(ang))
        x2 = cx + int(0.44 * s * math.cos(ang))
        y2 = cy + int(0.44 * s * math.sin(ang))
        cv.line(x1, y1, x2, y2, c, 5)
    cv.circle(cx - 6, cy - 4, 3, bg)
    cv.circle(cx + 7, cy + 5, 3, bg)


ICONS = [icon_blast, icon_quake, icon_shield, icon_chart, icon_bars,
         icon_virus]

# ------------------------------------------------------------ stories -----
# Six stories, each: (tag, colour, headline, summary). Facts as reported
# on Saturday 21 November 2026.
STORIES = [
    ("WAR IN EUROPE", (192, 57, 43),
     "RUSSIAN MISSILES LAND IN POLAND",
     "Moscow's strikes on Ukraine cross the border; Kyiv bridges hit and at least nine people killed."),
    ("EARTHQUAKE", (139, 90, 43),
     "6.8 QUAKE SHAKES PERU",
     "The Junin region is hit; tremors are felt in Lima, 320 km away."),
    ("MIDDLE EAST", (14, 124, 123),
     "HOUTHI MISSILES AT RIYADH STOPPED",
     "The Saudi-led coalition intercepts three missiles aimed at the capital."),
    ("MARKETS", (125, 60, 152),
     "TECH SELL-OFF DRAGS STOCKS DOWN",
     "Shares slide into a correction as AI worries grow; Anthropic shares fall."),
    ("NEW YORK", (31, 97, 141),
     "RIKERS ISLAND TO CLOSE BY 2032",
     "The mayor unveils the city's first plan to shut the jail complex."),
    ("HEALTH", (30, 132, 73),
     "US LOSES MEASLES-FREE STATUS",
     "Measles cases surge and the US loses its measles-free standing."),
]


def build():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(0, 0, W, 168, NAVY)
    cv.text_center(16, "THE WORLD IN ONE DAY", 2, GOLD)
    cv.text_center(42, "SATURDAY", 3, WHITE)
    cv.text_center(72, "21 NOVEMBER 2026", 8, WHITE)
    cv.rect(0, 152, W, 4, GOLD)

    # Subhead.
    cv.text_center(176, "SIX STORIES THAT DEFINED THE DAY", 2, INK)

    # Story grid: 2 columns x 3 rows.
    gx, gy = 16, 204
    pw, ph, gap = 488, 238, 8
    for i, (tag, colour, head, summ) in enumerate(STORIES):
        x = gx + (i % 2) * (pw + gap)
        y = gy + (i // 2) * (ph + gap)
        cv.rect(x, y, pw, ph, WHITE)
        cv.rect(x, y, pw, 10, colour)
        cv.rect(x, y, pw, 2, NAVY)
        cv.rect(x, y + ph - 2, pw, 2, NAVY)
        cv.rect(x, y, 2, ph, NAVY)
        cv.rect(x + pw - 2, y, 2, ph, NAVY)
        # Icon tile.
        cv.rect(x + 16, y + 26, 88, 88, colour)
        ICONS[i](cv, x + 16, y + 26, 88, WHITE, colour)
        # Tag + headline + summary.
        cv.text(x + 120, y + 34, tag, 2, colour)
        lines = cv.wrap(head, 3, pw - 136)
        ly = y + 62
        for ln in lines[:2]:
            cv.text(x + 120, ly, ln, 3, INK)
            ly += 24
        slines = cv.wrap(summ, 2, pw - 32)
        ly = y + 128
        for ln in slines[:3]:
            cv.text(x + 16, ly, ln, 2, GREY)
            ly += 17

    # Footer ticker: more of the day, plus sources.
    cv.rect(0, 944, W, 80, NAVY)
    cv.rect(0, 944, W, 3, GOLD)
    cv.text_center(954, "ALSO TODAY: VOYAGER 1 PASSES ONE LIGHT-DAY FROM EARTH |", 2, WHITE)
    cv.text_center(972, "KL RAHUL COMPLETES SENA CENTURIES | CYCLONE AKVAN HITS ODISHA |", 2, WHITE)
    cv.text_center(990, "EISENKOT TAPPED TO FORM ISRAEL GOVERNMENT", 2, WHITE)
    cv.text_center(1008, "SOURCES: BBC - AFP - NYT - AL JAZEERA - THE DAILY SHORT", 2, GOLD)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    write_png(build(), os.path.join(outdir, "entry.png"))


if __name__ == "__main__":
    main()
