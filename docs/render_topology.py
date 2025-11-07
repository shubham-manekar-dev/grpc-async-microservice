"""Render lightweight topology diagrams for the recruiter walkthrough."""

from __future__ import annotations

import argparse
import base64
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from xml.sax.saxutils import escape

WIDTH, HEIGHT = 720, 400
BACKGROUND = (18, 18, 20)
TEXT_COLOR = (240, 248, 255)
ACCENT = (89, 106, 255)
ACCENT_ALT = (0, 186, 136)
ACCENT_TERTIARY = (255, 199, 79)
ACCENT_DATA = (255, 112, 67)
ACCENT_CACHE = (126, 87, 194)
GRID_COLOR = (40, 40, 48)


@dataclass(frozen=True)
class TextLabel:
    x: int
    y: int
    content: str
    color: Tuple[int, int, int]
    size: int = 18
    weight: str = "500"


@dataclass(frozen=True)
class RectSpec:
    x: int
    y: int
    width: int
    height: int
    fill: Tuple[int, int, int]
    labels: Sequence[TextLabel]


FONT = {
    "A": [" 1 ", "1 1", "111", "1 1", "1 1"],
    "B": ["11 ", "1 1", "11 ", "1 1", "11 "],
    "C": [" 11", "1  ", "1  ", "1  ", " 11"],
    "D": ["11 ", "1 1", "1 1", "1 1", "11 "],
    "E": ["111", "1  ", "11 ", "1  ", "111"],
    "F": ["111", "1  ", "11 ", "1  ", "1  "],
    "G": [" 11", "1  ", "1 1", "1 1", " 11"],
    "H": ["1 1", "1 1", "111", "1 1", "1 1"],
    "I": ["111", " 1 ", " 1 ", " 1 ", "111"],
    "J": ["  1", "  1", "  1", "1 1", " 1 "],
    "K": ["1 1", "11 ", "1  ", "11 ", "1 1"],
    "L": ["1  ", "1  ", "1  ", "1  ", "111"],
    "M": ["1 1", "111", "1 1", "1 1", "1 1"],
    "N": ["1 1", "111", "111", "111", "1 1"],
    "O": ["111", "1 1", "1 1", "1 1", "111"],
    "P": ["111", "1 1", "111", "1  ", "1  "],
    "Q": ["111", "1 1", "1 1", "111", "  1"],
    "R": ["111", "1 1", "111", "11 ", "1 1"],
    "S": [" 11", "1  ", " 1 ", "  1", "11 "],
    "T": ["111", " 1 ", " 1 ", " 1 ", " 1 "],
    "U": ["1 1", "1 1", "1 1", "1 1", "111"],
    "V": ["1 1", "1 1", "1 1", "1 1", " 1 "],
    "W": ["1 1", "1 1", "1 1", "111", "1 1"],
    "X": ["1 1", "1 1", " 1 ", "1 1", "1 1"],
    "Y": ["1 1", "1 1", " 1 ", " 1 ", " 1 "],
    "Z": ["111", "  1", " 1 ", "1  ", "111"],
    "-": ["   ", "   ", "111", "   ", "   "],
    " ": ["   ", "   ", "   ", "   ", "   "],
    "|": [" 1 ", " 1 ", " 1 ", " 1 ", " 1 "],
    "&": ["111", "1  ", "111", "1 1", "111"],
    "/": ["  1", " 1 ", " 1 ", "1  ", "1  "],
    "1": [" 1 ", "11 ", " 1 ", " 1 ", "111"],
    "2": ["111", "  1", "111", "1  ", "111"],
    "3": ["111", "  1", "111", "  1", "111"],
    "4": ["1 1", "1 1", "111", "  1", "  1"],
    "5": ["111", "1  ", "111", "  1", "111"],
    "6": ["111", "1  ", "111", "1 1", "111"],
    "7": ["111", "  1", " 1 ", " 1 ", " 1 "],
    "8": ["111", "1 1", "111", "1 1", "111"],
    "9": ["111", "1 1", "111", "  1", "111"],
    "0": ["111", "1 1", "1 1", "1 1", "111"],
    ":": ["   ", " 1 ", "   ", " 1 ", "   "],
}


def to_hex(color: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % color


def build_layout() -> Tuple[List[RectSpec], List[TextLabel]]:
    rects = [
        RectSpec(
            60,
            50,
            260,
            120,
            ACCENT,
            [
                TextLabel(90, 80, "FastAPI Gateway", TEXT_COLOR),
                TextLabel(90, 118, "JWT + Care Flows", TEXT_COLOR),
            ],
        ),
        RectSpec(
            380,
            50,
            280,
            120,
            ACCENT_ALT,
            [
                TextLabel(400, 80, "gRPC Care-plan", TEXT_COLOR),
                TextLabel(400, 118, "ChatGPT / Gemini", TEXT_COLOR),
            ],
        ),
        RectSpec(
            60,
            210,
            160,
            120,
            ACCENT_DATA,
            [
                TextLabel(80, 240, "PostgreSQL", TEXT_COLOR),
                TextLabel(80, 278, "Patient Store", TEXT_COLOR),
            ],
        ),
        RectSpec(
            250,
            210,
            160,
            120,
            ACCENT_DATA,
            [
                TextLabel(270, 240, "MongoDB", TEXT_COLOR),
                TextLabel(270, 278, "Intake Audit", TEXT_COLOR),
            ],
        ),
        RectSpec(
            440,
            210,
            160,
            120,
            ACCENT_CACHE,
            [
                TextLabel(460, 240, "Redis", TEXT_COLOR),
                TextLabel(460, 278, "Cache + Tokens", TEXT_COLOR),
            ],
        ),
        RectSpec(
            630,
            210,
            70,
            120,
            ACCENT_TERTIARY,
            [
                TextLabel(640, 240, "UI", BACKGROUND),
                TextLabel(640, 278, "React", BACKGROUND),
            ],
        ),
    ]

    extra_labels = [
        TextLabel(140, 185, "REST / GraphQL", TEXT_COLOR, size=16),
        TextLabel(360, 185, "Async gRPC", TEXT_COLOR, size=16),
        TextLabel(
            110,
            340,
            "Kafka · Prometheus · Grafana · Kibana",
            TEXT_COLOR,
            size=14,
            weight="400",
        ),
    ]

    return rects, extra_labels


class Canvas:
    def __init__(self, width: int, height: int, background: Tuple[int, int, int]) -> None:
        self.width = width
        self.height = height
        self.pixels = [
            bytearray([0] + [background[c] for c in range(3)] * width)
            for _ in range(height)
        ]

    def draw_rect(self, x0: int, y0: int, x1: int, y1: int, color: Tuple[int, int, int]) -> None:
        for y in range(max(0, y0), min(self.height, y1)):
            row = self.pixels[y]
            for x in range(max(0, x0), min(self.width, x1)):
                offset = 1 + x * 3
                row[offset : offset + 3] = bytes(color)

    def draw_text(self, x: int, y: int, text: str, color: Tuple[int, int, int]) -> None:
        cursor_x = x
        for char in text.upper():
            glyph = FONT.get(char)
            if glyph is None:
                cursor_x += 4
                continue
            for gy, row_bits in enumerate(glyph):
                for gx, bit in enumerate(row_bits):
                    if bit == "1":
                        px = cursor_x + gx
                        py = y + gy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            offset = 1 + px * 3
                            self.pixels[py][offset : offset + 3] = bytes(color)
            cursor_x += 4

    def render(self) -> bytes:
        return b"".join(self.pixels)


def draw_grid(canvas: Canvas, spacing: int = 20) -> None:
    for x in range(0, canvas.width, spacing):
        canvas.draw_rect(x, 0, x + 1, canvas.height, GRID_COLOR)
    for y in range(0, canvas.height, spacing):
        canvas.draw_rect(0, y, canvas.width, y + 1, GRID_COLOR)


def draw_layout(canvas: Canvas, rects: Iterable[RectSpec], labels: Iterable[TextLabel]) -> None:
    for rect in rects:
        canvas.draw_rect(rect.x, rect.y, rect.x + rect.width, rect.y + rect.height, rect.fill)
        for label in rect.labels:
            canvas.draw_text(label.x, label.y, label.content, label.color)
    for label in labels:
        canvas.draw_text(label.x, label.y, label.content, label.color)


def chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, canvas: Canvas) -> None:
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    idat = zlib.compress(canvas.render(), level=9)
    png_bytes = header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(png_bytes)


def svg_line(x1: int, y1: int, x2: int, y2: int) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{to_hex(GRID_COLOR)}" stroke-width="1" />'


def svg_text(label: TextLabel) -> str:
    return (
        f'<text x="{label.x}" y="{label.y}" fill="{to_hex(label.color)}" '
        f'font-family="\'Segoe UI\', \"Helvetica Neue\", sans-serif" '
        f'font-size="{label.size}" font-weight="{label.weight}" '
        f'dominant-baseline="hanging">{escape(label.content)}</text>'
    )


def write_svg(path: Path, rects: Sequence[RectSpec], labels: Sequence[TextLabel]) -> None:
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="100%" height="100%" fill="{to_hex(BACKGROUND)}" />',
    ]

    for x in range(0, WIDTH, 20):
        lines.append(svg_line(x, 0, x, HEIGHT))
    for y in range(0, HEIGHT, 20):
        lines.append(svg_line(0, y, WIDTH, y))

    for rect in rects:
        lines.append(
            f'<rect x="{rect.x}" y="{rect.y}" width="{rect.width}" height="{rect.height}" '
            f'rx="16" fill="{to_hex(rect.fill)}" />'
        )
        for label in rect.labels:
            lines.append(svg_text(label))

    for label in labels:
        lines.append(svg_text(label))

    lines.append("</svg>")
    path.write_text("\n".join(lines))


def lighten(color: Tuple[int, int, int], factor: float = 0.35) -> Tuple[int, int, int]:
    return tuple(min(255, int(channel + (255 - channel) * factor)) for channel in color)


@dataclass(frozen=True)
class FrameSpec:
    highlight_rects: Sequence[int]
    overlay: Sequence[TextLabel]


def build_frames(rects: Sequence[RectSpec]) -> List[FrameSpec]:
    return [
        FrameSpec(
            highlight_rects=(5, 0),
            overlay=[
                TextLabel(40, 24, "Step 1", ACCENT_TERTIARY, size=22, weight="600"),
                TextLabel(120, 24, "Recruiter drives the React console", TEXT_COLOR, size=20),
                TextLabel(
                    120,
                    56,
                    "FastAPI gathers JWT-secured patient context for AI planning.",
                    TEXT_COLOR,
                    size=16,
                ),
            ],
        ),
        FrameSpec(
            highlight_rects=(1,),
            overlay=[
                TextLabel(40, 24, "Step 2", ACCENT_TERTIARY, size=22, weight="600"),
                TextLabel(120, 24, "Async gRPC and Generative AI", TEXT_COLOR, size=20),
                TextLabel(
                    120,
                    56,
                    "ChatGPT or Gemini refine the care plan; heuristics backstop demos.",
                    TEXT_COLOR,
                    size=16,
                ),
            ],
        ),
        FrameSpec(
            highlight_rects=(2, 3, 4),
            overlay=[
                TextLabel(40, 24, "Step 3", ACCENT_TERTIARY, size=22, weight="600"),
                TextLabel(120, 24, "Polyglot data + caching", TEXT_COLOR, size=20),
                TextLabel(
                    120,
                    56,
                    "PostgreSQL, MongoDB, and Redis persist, audit, and accelerate access.",
                    TEXT_COLOR,
                    size=16,
                ),
            ],
        ),
        FrameSpec(
            highlight_rects=(),
            overlay=[
                TextLabel(40, 24, "Step 4", ACCENT_TERTIARY, size=22, weight="600"),
                TextLabel(120, 24, "Streaming + observability", TEXT_COLOR, size=20),
                TextLabel(
                    120,
                    56,
                    "Kafka events and Prometheus/Grafana close the feedback loop.",
                    TEXT_COLOR,
                    size=16,
                ),
            ],
        ),
    ]


def draw_frame(rects: Sequence[RectSpec], labels: Sequence[TextLabel], frame: FrameSpec) -> Canvas:
    canvas = Canvas(WIDTH, HEIGHT, BACKGROUND)
    draw_grid(canvas)

    highlighted_rects = []
    for idx, rect in enumerate(rects):
        fill = lighten(rect.fill) if idx in frame.highlight_rects else rect.fill
        highlighted_rects.append(
            RectSpec(rect.x, rect.y, rect.width, rect.height, fill, rect.labels)
        )

    draw_layout(canvas, highlighted_rects, list(labels) + list(frame.overlay))
    return canvas


def build_apng_bytes(frames: Sequence[Canvas], delay_ms: int = 900) -> bytes:
    if not frames:
        raise ValueError("At least one frame is required to build an animated PNG")

    header = b"\x89PNG\r\n\x1a\n"
    width, height = frames[0].width, frames[0].height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    # Re-use existing chunk helper for consistency.
    png_bytes = header + chunk(b"IHDR", ihdr)
    png_bytes += chunk(b"acTL", struct.pack(">II", len(frames), 0))

    delay_num = delay_ms
    delay_den = 1000
    sequence = 0

    def frame_control(seq: int) -> bytes:
        return struct.pack(
            ">IIIIIHHBB",
            seq,
            width,
            height,
            0,
            0,
            delay_num,
            delay_den,
            0,
            0,
        )

    # First frame uses IDAT chunks.
    png_bytes += chunk(b"fcTL", frame_control(sequence))
    sequence += 1
    png_bytes += chunk(b"IDAT", zlib.compress(frames[0].render(), level=9))

    for canvas in frames[1:]:
        png_bytes += chunk(b"fcTL", frame_control(sequence))
        sequence += 1
        compressed = zlib.compress(canvas.render(), level=9)
        png_bytes += chunk(b"fdAT", struct.pack(">I", sequence) + compressed)
        sequence += 1

    png_bytes += chunk(b"IEND", b"")
    return png_bytes


def write_apng(path: Path, frames: Sequence[Canvas], delay_ms: int = 900) -> None:
    path.write_bytes(build_apng_bytes(frames, delay_ms))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render architecture diagrams for the README.")
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also emit a PNG version alongside the tracked SVG (useful for slide decks).",
    )
    parser.add_argument(
        "--apng",
        action="store_true",
        help="Emit an animated PNG walkthrough highlighting the recruiter journey.",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Print a data-URI version of the animated PNG for README embedding.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rects, labels = build_layout()
    svg_path = Path(__file__).with_name("live-topology.svg")
    write_svg(svg_path, rects, labels)
    print(f"Wrote {svg_path}")

    if args.png:
        canvas = Canvas(WIDTH, HEIGHT, BACKGROUND)
        draw_grid(canvas)
        draw_layout(canvas, rects, labels)
        png_path = Path(__file__).with_name("live-topology.png")
        write_png(png_path, canvas)
        print(f"Wrote {png_path}")

    if args.apng or args.embed:
        frames = [draw_frame(rects, labels, frame) for frame in build_frames(rects)]
        apng_bytes = build_apng_bytes(frames)

        if args.apng:
            apng_path = Path(__file__).with_name("workflow.apng")
            apng_path.write_bytes(apng_bytes)
            print(f"Wrote {apng_path}")

        if args.embed:
            data_uri = "data:image/png;base64," + base64.b64encode(apng_bytes).decode("ascii")
            embed_path = Path(__file__).with_name("workflow.apng.data-uri")
            embed_path.write_text(data_uri)
            print(f"Wrote {embed_path}")
            print(data_uri)


if __name__ == "__main__":
    main()
