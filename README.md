# seqpaint

Visualize nucleic acid and protein sequences as images.

Successor to [`fasta2png`](https://github.com/metebalci/fasta2png) — same core idea (one colored square per base/residue), broader ambitions: new layouts, comparative views, richer output formats.

## Status

v0.7.0. Subcommand CLI with `fna`, `faa`, `gc`, `dotplot`, `diff`, `stacked`; Hilbert / Z-order / raster layouts; four named palettes per alphabet; k-mer coloring; GFF annotation overlay; PNG / SVG / HTML outputs (HTML has hover-tooltip with position + context); transparent `.gz` / `.bgz` reading; NCBI accession fetch.

## Install

```
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Quick example

The `--accession` flag fetches sequences from NCBI on demand and caches them at `~/.cache/seqpaint/`. Every example below also works with `--input your.fna` or `--input your.faa`.

```
# Nucleic acid — pick your style:
seqpaint fna --accession NC_045512.2 --output covid.png         --pixel-size 8 --aspect-ratio 3 2
seqpaint fna --accession NC_045512.2 --output covid_hilbert.png --layout hilbert --palette colorblind-safe
seqpaint fna --accession NC_045512.2 --output covid_kmer.png    --kmer 6 --pixel-size 4 --aspect-ratio 3 2

# Protein:
seqpaint faa --accession YP_009724389.1 --output spike.png --palette nature --pixel-size 4 --aspect-ratio 3 2

# Other modes:
seqpaint gc      --accession NC_045512.2 --output gc.png --window 100 --pixel-size 4 --aspect-ratio 3 2
seqpaint dotplot --input A.fna --input2 B.fna --output dp.png --word-size 12
seqpaint diff    --input A.fna --input2 B.fna --output diff.png                 # NW alignment, capped at 5000bp
seqpaint stacked --input multi.fna --output stacked.png --palette nature        # one row per record

# Output format follows the --output suffix: .png, .svg, or .html:
seqpaint fna --accession NC_045512.2 --output covid.svg  --pixel-size 2
seqpaint fna --accession NC_045512.2 --output covid.html --pixel-size 4         # hover tooltip
```

`fna` and `faa` pick the alphabet by subcommand name. `gc` is nucleic-only; `dotplot` and `diff` are alphabet-agnostic (categorical colors); `stacked` sniffs alphabet from the first record's content.

Compressed inputs (`.gz`, and `.bgz` with `pip install 'seqpaint[bgzf]'`) are read transparently.

## Gallery

Browse the [`examples/`](examples/) folder for a visual tour of what each mode produces:

- [`examples/layouts/`](examples/layouts/) — raster / Hilbert / Z-order compared on the same data
- [`examples/palettes/`](examples/palettes/) — all four named palettes side-by-side
- [`examples/hilbert/`](examples/hilbert/) — when Hilbert layout actually helps (GC maps, k-mer coloring)
- [`examples/single/`](examples/single/) — focused renderings: 16S rRNA, human mitochondrion, lambda phage
- [`examples/comparative/`](examples/comparative/) — dotplot, diff, stacked
- [`examples/formats/`](examples/formats/) — SVG and HTML outputs (including a hover-tooltip HTML demo)

Each folder has its own README explaining what the images show and the exact commands to reproduce them.

## Example data

This repository does not bundle FASTA files. Sequences used in the gallery are fetched from [NCBI](https://www.ncbi.nlm.nih.gov/) via the E-utilities service when you pass `--accession`.

## License

GPL-3.0-only. See [`LICENSE`](LICENSE) for the full text.
