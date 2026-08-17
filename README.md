# 🧠 CortexForge

> **Forge a 3D-printable brain from any MRI.**

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![FreeSurfer](https://img.shields.io/badge/FreeSurfer-7.4.1-5B2D86?style=for-the-badge)](https://surfer.nmr.mgh.harvard.edu)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![3D Printable](https://img.shields.io/badge/3D_Printable-watertight-success?style=for-the-badge)](https://github.com/Koalalive/CortexForge)

Turn a T1-weighted brain MRI into a **watertight, slicer-ready cortical model** — every gyrus and sulcus intact, ready to drop into Cura, PrusaSlicer, or Bambu Studio.

```
 ┌─────────┐   ┌──────────┐   ┌──────────────┐   ┌────────────┐   ┌──────────────┐
 │  DICOM  │ → │  NIfTI   │ → │  recon-all   │ → │ pial .stl  │ → │  printable   │
 │  series │   │   (T1)   │   │ (FreeSurfer) │   │  (lh + rh) │   │  brain STL  │
 └─────────┘   └──────────┘   └──────────────┘   └────────────┘   └──────────────┘
    dcm2niix       nibabel        FreeSurfer       mris_convert       trimesh
```

---

## ✨ What you get

A real, anatomically-accurate model of a specific brain:

| | |
|---|---|
| 🧠 **Cortical surface** | Full sulcal/gyral folding, one watertight shell per hemisphere |
| 📏 **Life-size** | ≈ 147 × 173 × 122 mm — real adult brain (scale down in the slicer) |
| 🧊 **Slicer-ready** | Closed, manifold mesh — no repair needed |
| 🌀 **Smoothed** | Optional Taubin pass removes surface noise, keeps the folds |

## 🚀 The pipeline

1. **DICOM → NIfTI** — `dcm2niix`, reoriented to RAS
2. **Cortical reconstruction** — FreeSurfer `recon-all -all` (Docker, background, 4–8 h on CPU)
3. **Surface extraction** — `mris_convert` turns the lh/rh pial surfaces into STL
4. **Merge + watertight** — `trimesh` concatenates the hemispheres → `brain_full.stl`
5. **Smoothing** — Taubin smoothing → `brain_full_smooth.stl`

## 🧭 New to FreeSurfer?

The full tutorial — [SKILL.md](SKILL.md) — has a dedicated **"Understanding the FreeSurfer environment"** section that walks through `FREESURFER_HOME`, `FS_LICENSE`, `SUBJECTS_DIR`, and `SetUpFreeSurfer.sh`, plus a step-by-step license guide and a troubleshooting table.

## 📦 Scripts

| Script | Purpose |
|---|---|
| [`scripts/check_fs_env.sh`](scripts/check_fs_env.sh) | Verify the FreeSurfer environment before the long run |
| [`scripts/run_recon.sh`](scripts/run_recon.sh) | recon-all wrapper (config at top) |
| [`scripts/merge_stl.py`](scripts/merge_stl.py) | concatenate lh/rh pial STLs |
| [`scripts/smooth_stl.py`](scripts/smooth_stl.py) | Taubin smoothing |

## 🔧 Dependencies

- **Docker** + a FreeSurfer image (e.g. `freesurfer/freesurfer:7.4.1`)
- **FreeSurfer license** — free registration at [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html)
- **Python** — `pip install pydicom dcm2niix trimesh nibabel`

## 🔒 Privacy

MRI data, patient information, and the FreeSurfer license are all sensitive. This repository ships **only the tutorial and scripts — no data files**.
