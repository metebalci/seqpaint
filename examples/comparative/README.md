# Comparative modes

These modes take either two sequences (`dotplot`, `diff`) or a multi-record FASTA (`stacked`).

## Dotplot: SARS-CoV-2 vs SARS-CoV-1

![dotplot sars2 vs sars1](dotplot_sars2_vs_sars1.png)

X-axis = SARS-CoV-2 genome (NC_045512.2, 29,903 bp). Y-axis = SARS-CoV-1 genome (NC_004718.3, 29,751 bp). Each dot marks a shared 12-mer between the two sequences.

The strong main diagonal is the overall ~80% nucleotide identity between these two betacoronaviruses. The scattered off-diagonal dots are regions where either genome has shuffled or inserted material — most notably around the spike gene, which is the most divergent region of the two genomes.

## Dotplot: SARS-CoV-2 vs itself

![dotplot sars2 self](dotplot_sars2_self.png)

Self-dotplot — a useful control. A perfectly non-repetitive sequence produces only the main diagonal. SARS-CoV-2 shows almost exactly that: very little internal repetition, so the image is essentially a clean diagonal line with a handful of sparse hits.

## Diff: SARS-CoV-2 spike vs SARS-CoV-1 spike (protein)

![diff spike](diff_spike_sars2_vs_sars1.png)

Two rows, top = SARS-CoV-2 spike (YP_009724390.1, 1273 aa), bottom = SARS-CoV-1 spike (NP_828851.1, 1255 aa). Aligned by Needleman-Wunsch, then each position colored green (match), red (mismatch), or gray (gap).

The image is very thin — the diff mode is fundamentally a strip visualization. Zoom in to see the pattern: mismatches cluster in the receptor-binding domain (residues ~300-500), which is the region responsible for ACE2 binding and has the most species-adaptive substitutions.

## Stacked: hemoglobin chains

![stacked hemoglobins](stacked_hemoglobins.png)

Four globin chains stacked as rows (top to bottom):
1. Human hemoglobin alpha (NP_000549.1, 142 aa)
2. Human hemoglobin beta (NP_000509.1, 147 aa)
3. Mouse hemoglobin beta major (NP_032246.1, 147 aa)
4. Mouse hemoglobin epsilon-Y2 (NP_032247.1, 147 aa)

Columns line up by residue position. Residues conserved across all four chains (e.g. the proximal F8 histidine that binds heme iron) show up as a single color running vertically down the column. Variable residues are the places where rows disagree on color. The stacked view makes family-level conservation patterns scannable at a glance.

Note: row 1 is slightly shorter (142 aa) and the last ~5 pixels of that row are background-padded because hemoglobin alpha is shorter than the beta-family chains.

## Reproduce

```bash
# Dotplots
seqpaint dotplot --accession NC_045512.2 --accession2 NC_004718.3 \
  --output dotplot_sars2_vs_sars1.png --word-size 12 --pixel-size 1
seqpaint dotplot --accession NC_045512.2 --accession2 NC_045512.2 \
  --output dotplot_sars2_self.png --word-size 12 --pixel-size 1

# Diff
seqpaint diff --accession YP_009724390.1 --accession2 NP_828851.1 \
  --output diff_spike_sars2_vs_sars1.png --pixel-size 2

# Stacked — fetch each chain, concatenate, then stack
for acc in NP_000549.1 NP_000509.1 NP_032246.1 NP_032247.1; do
  seqpaint faa --accession $acc --output /tmp/_$acc.png --pixel-size 1 > /dev/null
done
cat ~/.cache/seqpaint/NP_{000549,000509,032246,032247}.1.faa > /tmp/hemoglobins.faa
seqpaint stacked --input /tmp/hemoglobins.faa --output stacked_hemoglobins.png \
  --pixel-size 6 --palette nature
```
