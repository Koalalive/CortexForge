# MRI Brain → 3D Print

Turn a brain MRI into a 3D-printable cortex STL model.

```
DICOM ──dcm2niix──▶ NIfTI ──FreeSurfer recon-all──▶ pial surface ──▶ STL ──▶ merge + watertight + smooth
```

## Pipeline

- **DICOM → NIfTI** — `dcm2niix` on a 3D T1, reoriented to RAS
- **Cortical reconstruction** — FreeSurfer `recon-all -all` (Docker, background, 4–8 h on CPU)
- **Surface extraction** — `mris_convert` turns lh/rh pial surfaces into STL
- **Merge + watertight** — `trimesh` concatenates hemispheres → `brain_full.stl`
- **Smoothing** — Taubin smoothing (volume-preserving, fold-preserving) → `brain_full_smooth.stl`

## Example output specs

- Watertight closed mesh (one shell per hemisphere)
- Size ≈ 147 × 173 × 122 mm (real adult brain; scale down in the slicer)
- Brain volume ≈ 1227 cm³

## Full tutorial

See [SKILL.md](SKILL.md).

## Scripts

| Script | Purpose |
|---|---|
| [`scripts/run_recon.sh`](scripts/run_recon.sh) | recon-all wrapper (config at top) |
| [`scripts/merge_stl.py`](scripts/merge_stl.py) | concatenate lh/rh pial STLs |
| [`scripts/smooth_stl.py`](scripts/smooth_stl.py) | Taubin smoothing |

## Dependencies

- Docker + a FreeSurfer image
- FreeSurfer license (free registration; **never commit the license**)
- Python: `pydicom`, `dcm2niix`, `trimesh`, `nibabel`

## Privacy

MRI data, patient information, and the FreeSurfer license are all sensitive. This repository contains only the tutorial and scripts — **no data files**.
