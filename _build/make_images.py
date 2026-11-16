#!/usr/bin/env python3
"""Original logo and social image. Flat colors and a tiny bitmap wordmark. Not a photo."""

import struct
import zlib

# 5x7 glyphs, rows of 0/1.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def save_png(path, w, h, buf):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(buf[y * w * 3 : (y + 1) * w * 3])
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def fill(buf, w, h, rgb):
    px = bytes(rgb)
    for i in range(0, w * h * 3, 3):
        buf[i : i + 3] = px


def rect(buf, w, h, x0, y0, x1, y1, rgb):
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    for y in range(y0, y1):
        row = y * w * 3
        for x in range(x0, x1):
            i = row + x * 3
            buf[i : i + 3] = bytes(rgb)


def text(buf, w, h, words, x, y, scale, rgb):
    cursor = x
    for ch in words:
        glyph = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    rect(buf, w, h, cursor + gx * scale, y + gy * scale, cursor + (gx + 1) * scale, y + (gy + 1) * scale, rgb)
        cursor += 6 * scale


def mark(buf, w, h, ox, oy, s):
    # Road and a ring, scaled by s, origin top-left of a 64-unit box.
    rect(buf, w, h, ox + 8 * s, oy + 34 * s, ox + 56 * s, oy + 50 * s, (231, 245, 238))
    for dx in (14, 28, 42):
        rect(buf, w, h, ox + dx * s, oy + 40 * s, ox + (dx + 8) * s, oy + 44 * s, (240, 180, 41))
    # Ring approximated with a thick circle.
    cx, cy, r, t = ox + 32 * s, oy + 20 * s, 8 * s, 4 * s
    r2, inner = (r + 1) ** 2, (r - t) ** 2
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if inner <= d <= r2:
                if 0 <= x < w and 0 <= y < h:
                    i = (y * w + x) * 3
                    buf[i : i + 3] = bytes((240, 180, 41))


def main():
    w, h = 512, 512
    buf = bytearray(w * h * 3)
    fill(buf, w, h, (11, 57, 84))
    mark(buf, w, h, 64, 96, 6)
    save_png("/workspace/logo.png", w, h, buf)

    w, h = 1200, 630
    buf = bytearray(w * h * 3)
    fill(buf, w, h, (11, 57, 84))
    rect(buf, w, h, 0, 470, 1200, 560, (231, 245, 238))
    for x in range(80, 1120, 90):
        rect(buf, w, h, x, 505, x + 40, 525, (240, 180, 41))
    text(buf, w, h, "WHICH DRIVING TEST", 80, 150, 8, (255, 255, 255))
    text(buf, w, h, "STATE DMV GUIDES", 80, 280, 6, (240, 180, 41))
    save_png("/workspace/og.png", w, h, buf)


if __name__ == "__main__":
    main()
