# 🧠 BrainForge

> **Forge a complete, 3D-printable brain — cerebrum, cerebellum, and brainstem — from any MRI.**

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![FreeSurfer](https://img.shields.io/badge/FreeSurfer-7.4.1-5B2D86?style=for-the-badge)](https://surfer.nmr.mgh.harvard.edu)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Whole Brain](https://img.shields.io/badge/Whole_Brain-watertight_solid-success?style=for-the-badge)](https://github.com/Koalalive/BrainForge)
[![3D Printable](https://img.shields.io/badge/3D_Printable-ready_to_slice-FF6F00?style=for-the-badge)](https://github.com/Koalalive/BrainForge)

Turn a T1-weighted MRI into a **single watertight solid of the whole brain** — not just the cortex, but the **cerebrum with its fine gyri, the cerebellum, and the brainstem**, all correctly separated by the tentorial gap and joined by the brainstem bridge.

```
        ┌───────────────────────────┐
        │         CEREBRUM          │   pial surface · fine gyri · 2 light smooth passes
        │    (left + right hemis)   │
        └─────────────┬─────────────┘
           tentorial gap ~6 mm      ◄── anatomically correct, never welded
        ┌─────────────┴─────────────┐
        │        CEREBELLUM         │   aseg marching cubes · 20 smooth passes
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │         BRAINSTEM         │   aseg marching cubes · 20 smooth passes
        └───────────────────────────┘
```

---

## ✨ What you get

One watertight, slicer-ready model of a *specific, real* brain:

| | |
|---|---|
| 🧠 **The whole brain** | Cerebrum + cerebellum + brainstem in a single solid |
| 🔬 **Fine cortical detail** | Every gyrus and sulcus, straight from the pial surface |
| 📐 **Correct anatomy** | Cerebrum & cerebellum separated by the tentorial gap, bridged only by the brainstem |
| 📏 **Life-size** | ≈ 147 × 172 × 148 mm (scale down in the slicer) |
| 🧊 **Slicer-ready** | Closed, manifold mesh — no repair needed |
| 🌀 **Per-part smoothing** | Light on the cortex (keeps folds), heavy on cerebellum/brainstem (kills the voxel staircase) |

## 🚀 The pipeline

1. **DICOM → NIfTI** — `dcm2niix`, reoriented to RAS
2. **Cortical reconstruction** — FreeSurfer `recon-all -all` (Docker, background, 4–8 h on CPU)
3. **Surface extraction** — `mris_convert` turns lh/rh pial surfaces into STL
4. **Cerebellum + brainstem** — binarize aseg labels, marching cubes → STL
5. **Per-part smoothing + merge** — smooth each part to its own needs, boolean-union → `ultimate_brain.stl`

## 🧭 New to FreeSurfer?

The full tutorial — [SKILL.md](SKILL.md) — has a dedicated **"Understanding the FreeSurfer environment"** section (license, `FREESURFER_HOME`, `SUBJECTS_DIR`, `SetUpFreeSurfer.sh`), plus the whole-brain recipe with per-part smoothing, and a troubleshooting table.

## 📦 Scripts

| Script | Purpose |
|---|---|
| [`scripts/check_fs_env.sh`](scripts/check_fs_env.sh) | Verify the FreeSurfer environment before the long run |
| [`scripts/run_recon.sh`](scripts/run_recon.sh) | recon-all wrapper (config at top) |
| [`scripts/merge_stl.py`](scripts/merge_stl.py) | concatenate lh/rh pial STLs |
| [`scripts/smooth_stl.py`](scripts/smooth_stl.py) | Taubin smoothing |
| [`scripts/extract_cerebellum_brainstem.sh`](scripts/extract_cerebellum_brainstem.sh) | extract cerebellum + brainstem from aseg |
| [`scripts/build_whole_brain.py`](scripts/build_whole_brain.py) | per-part smoothing + trim + boolean-union into the whole brain |

## 🔧 Dependencies

- **Docker** + a FreeSurfer image (e.g. `freesurfer/freesurfer:7.4.1`)
- **FreeSurfer license** — free registration at [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html)
- **Python** — `pip install pydicom dcm2niix trimesh nibabel manifold3d`

## 🔒 Privacy

MRI data, patient information, and the FreeSurfer license are all sensitive. This repository ships **only the tutorial and scripts — no data files**.
