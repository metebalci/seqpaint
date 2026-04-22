from __future__ import annotations

from pathlib import Path
from typing import Protocol
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

from .core import RGBA


class Canvas(Protocol):
    width: int
    height: int

    def fill_cell(self, x: int, y: int, color: RGBA) -> None:
        """Fill a single cell (pixel_size-aware at the caller level — the
        canvas works in final pixel coordinates)."""
        ...

    def fill_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None: ...

    def stroke_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None: ...

    def save(self, path: str | Path) -> None: ...


class PngCanvas:
    def __init__(self, width: int, height: int, bg_color: RGBA = (0, 0, 0, 255)) -> None:
        self.width = width
        self.height = height
        self._image = Image.new("RGBA", (width, height), color=bg_color)  # type: ignore[arg-type]
        self._draw = ImageDraw.Draw(self._image)

    @property
    def image(self) -> Image.Image:
        return self._image

    @property
    def size(self) -> tuple[int, int]:
        return self._image.size

    def getpixel(self, xy: tuple[int, int]):
        return self._image.getpixel(xy)

    def fill_cell(self, x: int, y: int, color: RGBA) -> None:
        self._image.putpixel((x, y), color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None:
        self._draw.rectangle([x, y, x + w, y + h], fill=color)

    def stroke_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None:
        self._draw.rectangle([x, y, x + w - 1, y + h - 1], outline=color)

    def save(self, path: str | Path) -> None:
        self._image.save(path, "PNG")


def _rgba_css(c: RGBA) -> str:
    r, g, b, a = c
    return f"rgba({r},{g},{b},{a / 255:.3f})"


class SvgCanvas:
    def __init__(self, width: int, height: int, bg_color: RGBA = (0, 0, 0, 255)) -> None:
        self.width = width
        self.height = height
        self._bg = bg_color
        self._rects: list[str] = []

    def fill_cell(self, x: int, y: int, color: RGBA) -> None:
        self.fill_rect(x, y, 1, 1, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None:
        self._rects.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{_rgba_css(color)}"/>'
        )

    def stroke_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None:
        self._rects.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="none" stroke="{_rgba_css(color)}" stroke-width="1"/>'
        )

    def _render(self) -> str:
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" '
            f'shape-rendering="crispEdges">'
        )
        bg = (
            f'<rect x="0" y="0" width="{self.width}" height="{self.height}" '
            f'fill="{_rgba_css(self._bg)}"/>'
        )
        return head + bg + "".join(self._rects) + "</svg>"

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self._render(), encoding="utf-8")


class HtmlCanvas:
    """SVG wrapped in a self-contained HTML document with a hover tooltip.

    The tooltip requires a sequence and a pixel→index mapping; both are
    injected by the caller via `attach_sequence()` before save().
    """

    def __init__(self, width: int, height: int, bg_color: RGBA = (0, 0, 0, 255)) -> None:
        self.width = width
        self.height = height
        self._svg = SvgCanvas(width, height, bg_color)
        self._sequence: str | None = None
        self._description: str = ""
        # Optional index mapping: flat pixel coord (y*width+x) -> sequence index.
        self._index_map: list[int] | None = None
        self._pixel_size: int = 1

    # Delegate drawing to the underlying SVG.
    def fill_cell(self, x: int, y: int, color: RGBA) -> None:
        self._svg.fill_cell(x, y, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None:
        self._svg.fill_rect(x, y, w, h, color)

    def stroke_rect(self, x: int, y: int, w: int, h: int, color: RGBA) -> None:
        self._svg.stroke_rect(x, y, w, h, color)

    def attach_sequence(
        self,
        sequence: str,
        description: str,
        *,
        pixel_size: int = 1,
        index_map: list[int] | None = None,
    ) -> None:
        self._sequence = sequence
        self._description = description
        self._pixel_size = pixel_size
        self._index_map = index_map

    def save(self, path: str | Path) -> None:
        svg_body = self._svg._render()
        if self._sequence is None:
            Path(path).write_text(
                f"<!doctype html><html><body>{svg_body}</body></html>",
                encoding="utf-8",
            )
            return
        import json
        seq_js = json.dumps(self._sequence)
        idx_js = json.dumps(self._index_map) if self._index_map is not None else "null"
        desc = escape(self._description)
        html = _HTML_TEMPLATE.format(
            description=desc,
            svg=svg_body,
            sequence=seq_js,
            index_map=idx_js,
            pixel_size=self._pixel_size,
            width=self.width,
            height=self.height,
        )
        Path(path).write_text(html, encoding="utf-8")


_HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>seqpaint: {description}</title>
<style>
  body {{ font-family: ui-monospace, monospace; background: #111; color: #ddd; margin: 1em; }}
  #seq {{ display: inline-block; border: 1px solid #444; }}
  #tooltip {{ position: fixed; pointer-events: none; background: #222;
             border: 1px solid #555; padding: 4px 8px; font-size: 12px;
             color: #eee; display: none; white-space: nowrap; }}
  .meta {{ color: #999; margin-bottom: 8px; }}
</style>
</head>
<body>
<div class="meta">{description} &mdash; {width}x{height}px</div>
<div id="seq">{svg}</div>
<div id="tooltip"></div>
<script>
const SEQ = {sequence};
const INDEX_MAP = {index_map};
const PIXEL_SIZE = {pixel_size};
const tip = document.getElementById("tooltip");
const host = document.getElementById("seq");
host.addEventListener("mousemove", (ev) => {{
  const svg = host.firstElementChild;
  const rect = svg.getBoundingClientRect();
  const vbw = svg.viewBox.baseVal.width;
  const vbh = svg.viewBox.baseVal.height;
  const x = Math.floor((ev.clientX - rect.left) * vbw / rect.width);
  const y = Math.floor((ev.clientY - rect.top) * vbh / rect.height);
  if (x < 0 || y < 0 || x >= {width} || y >= {height}) {{
    tip.style.display = "none"; return;
  }}
  let i;
  if (INDEX_MAP) {{
    const cx = Math.floor(x / PIXEL_SIZE);
    const cy = Math.floor(y / PIXEL_SIZE);
    const flat = cy * Math.floor({width} / PIXEL_SIZE) + cx;
    i = INDEX_MAP[flat];
  }} else {{
    i = -1;
  }}
  if (i === undefined || i < 0 || i >= SEQ.length) {{ tip.style.display = "none"; return; }}
  const left = Math.max(0, i - 10);
  const right = Math.min(SEQ.length, i + 11);
  const before = SEQ.substring(left, i);
  const base = SEQ.charAt(i);
  const after = SEQ.substring(i + 1, right);
  tip.innerHTML = "pos " + i + ": " + before + "<b>" + base + "</b>" + after;
  tip.style.left = (ev.clientX + 12) + "px";
  tip.style.top = (ev.clientY + 12) + "px";
  tip.style.display = "block";
}});
host.addEventListener("mouseleave", () => {{ tip.style.display = "none"; }});
</script>
</body>
</html>
"""


def canvas_for(
    path: str | Path, width: int, height: int,
    bg_color: RGBA = (0, 0, 0, 255),
) -> Canvas:
    suffix = Path(path).suffix.lower()
    if suffix == ".svg":
        return SvgCanvas(width, height, bg_color)
    if suffix in (".html", ".htm"):
        return HtmlCanvas(width, height, bg_color)
    return PngCanvas(width, height, bg_color)
