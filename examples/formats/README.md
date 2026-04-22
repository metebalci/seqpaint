# Output formats

Every subcommand dispatches to the right backend based on the `--output` suffix:

| Suffix | Backend | Characteristics |
|---|---|---|
| `.png` | Pillow | Compact binary, universally viewable. Default for every example in the sibling folders. |
| `.svg` | text-based | Vector; zoom without pixelation. One `<rect>` per pixel, so file size scales with sequence length. |
| `.html` | self-contained HTML | Wraps the SVG, embeds the sequence + a position map, adds a JS hover tooltip. |

## SVG

[`spike.svg`](spike.svg) — SARS-CoV-2 spike protein (YP_009724390.1, 1273 aa) rendered with the `nature` amino-acid palette at pixel-size 4, raster layout.

GitHub renders SVGs inline on file pages, so clicking the file name opens it as a real image you can inspect. Unlike a PNG, zooming in a browser doesn't pixelate.

## HTML with hover tooltip

[`spike_interactive.html`](spike_interactive.html) — same spike protein, but as a self-contained HTML document. Download and open in a browser (GitHub won't render HTML inline for security reasons).

On hover over any pixel you get:
- the position index (1-based)
- a window of 10 residues before and after, with the hovered residue in bold

Useful for quickly spotting *where* a feature sits without lining up ruler coordinates by eye.

## Reproduce

```bash
seqpaint faa --accession YP_009724390.1 --output spike.svg \
  --pixel-size 4 --aspect-ratio 3 2 --palette nature
seqpaint faa --accession YP_009724390.1 --output spike_interactive.html \
  --pixel-size 8 --aspect-ratio 3 2 --palette nature
```

## Size note

SVG file size scales with the number of pixels (one `<rect>` per pixel today). A 30 kb genome at pixel-size 4 produces an ~2 MB SVG; a 1.3 kb protein is under 100 KB. For huge inputs, prefer PNG; SVG's benefit (vector zoom) mostly pays off on smaller renderings where each pixel is meaningful.
