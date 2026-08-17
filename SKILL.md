---
name: mri-brain-to-3d-print
description: Generate a 3D-printable brain cortex STL from brain MRI (DICOM/NIfTI). Covers dcm2niix conversion, FreeSurfer recon-all cortical reconstruction, pial surface extraction, hemisphere merge + watertight, and Taubin smoothing. Triggers: MRI, DICOM, NIfTI, FreeSurfer, recon-all, cortical surface, pial surface, STL, 3D print brain, brain model.
---

# From Brain MRI to a 3D-Printable Brain Model

Turn a T1-weighted brain MRI into a 3D-printable cortical model (with sulcal/gyral folds) that drops straight into any slicer.

**Full pipeline**:

```
DICOM ──dcm2niix──▶ NIfTI ──recon-all──▶ pial surface ──mris_convert──▶ STL ──trimesh──▶ merge + watertight + smooth
```

---

## 0. Prerequisites

| Dependency | Purpose | Notes |
|---|---|---|
| Docker | Run FreeSurfer | Docker Desktop on Windows/macOS, native docker on Linux |
| A FreeSurfer image | recon-all | e.g. `freesurfer/freesurfer:7.4.1`, or your own neuroimaging image |
| FreeSurfer **license** | Required by recon-all | Free, register at https://surfer.nmr.mgh.harvard.edu/registration.html |
| Python | Mesh processing | `pydicom`, `dcm2niix`, `trimesh`, `nibabel` |

> ⚠️ **FreeSurfer license**: without it `recon-all` refuses to run. Register (free) at the URL above to get a `license.txt` containing your email and a registration key. **This file is private — never commit it to a public repo.**

```bash
pip install pydicom dcm2niix trimesh nibabel
```

---

## 1. DICOM → NIfTI

Convert the raw DICOM series (a 3D T1, e.g. `t1_mprage_sag_1mm`) to NIfTI:

```bash
dcm2niix -z y -b y -f "%p" -o <output_dir> <dicom_series_dir>
```

- `-z y` — compress to `.nii.gz`
- `-b y` — also emit a BIDS JSON sidecar (sequence parameters)
- `-f "%p"` — name files after the protocol

Verify the result (voxels should be near-isotropic 1mm):

```bash
python -c "import nibabel as n; img=n.load('<t1>.nii.gz'); print(img.shape, img.header.get_zooms(), n.aff2axcodes(img.affine))"
```

Expect something like `(256, 256, 208) (0.9, 0.9, 0.9) ('R','A','S')` — dcm2niix has already reoriented it to RAS.

---

## 2. FreeSurfer recon-all

The slowest step (4–8 hours on CPU). Run it in the background.

### 2.1 Prepare the script

The runnable script is [`scripts/run_recon.sh`](scripts/run_recon.sh). It sources FreeSurfer, points at your license, and launches `recon-all -all`. Edit the config block at the top (`SUBJECT`, `INPUT_NIFTI`, `NTHREADS`, `FREESURFER_HOME`).

### 2.2 Launch in the background

```bash
docker run -d --name recon \
  -v "<data_dir>:/data" \
  <neuroimage-image> bash /data/scripts/run_recon.sh
```

### 2.3 Track progress

recon-all writes two logs you can inspect anytime:

```bash
tail -f <data_dir>/recon_all.log                                   # overall stdout
grep '^#@#' <data_dir>/freesurfer/subj01/scripts/recon-all-status.log   # completed steps
```

Success marker at the end of the log:

```
recon-all -s subj01 finished without error at ...
```

> 💡 **Timing**: `autorecon1` (preprocessing, ~15 min) → `autorecon2` (segmentation + surface reconstruction, 1–2 h) → `autorecon3` (spherical registration + cortex, 2–3 h). The three slowest stages — automatic topology fixer, per-hemisphere spherical registration, and cortical parcellation — are where progress appears to stall; that's normal.
>
> 💡 **Docker Desktop resources**: check `docker info` for the real `CPUs`/`Total Memory` (often capped below the host). Don't set `-openmp` higher than that.

---

## 3. pial surface → STL

After recon-all, convert the cortical surfaces to STL with FreeSurfer's `mris_convert`:

```bash
docker run --rm -v "<data_dir>:/data" <neuroimage-image> bash -c '
  export FREESURFER_HOME=/usr/local/freesurfer/7.4.1
  export FS_LICENSE=/data/license.txt
  source $FREESURFER_HOME/SetUpFreeSurfer.sh
  mkdir -p /data/output
  mris_convert /data/freesurfer/subj01/surf/lh.pial /data/output/lh.pial.stl
  mris_convert /data/freesurfer/subj01/surf/rh.pial /data/output/rh.pial.stl
'
```

> ⚠️ **Gotcha**: on a Windows-mounted directory, `lh.pial` / `rh.pial` show as **0 bytes** — they are **symlinks** (`lh.pial -> lh.pial.T1`); the real file is `lh.pial.T1` (several MB). Windows Explorer shows Linux symlinks as 0-byte files, but inside the container `mris_convert` follows the link fine — the data is complete, nothing to fix.

FreeSurfer's pial surfaces are **already watertight closed meshes** (they cover the whole cortex, including the medial wall and basal closure), one closed shell per hemisphere — ideal for 3D printing.

---

## 4. Merge hemispheres + watertight

Run [`scripts/merge_stl.py`](scripts/merge_stl.py):

```bash
python scripts/merge_stl.py
```

Produces `output/brain_full.stl` — the two hemisphere shells in one file (separated at the interhemispheric fissure, as in real anatomy), each shell watertight and slicer-ready.

---

## 5. Taubin smoothing (optional, recommended)

Pial surfaces carry fine per-vertex noise. A Taubin pass (shrink + expand alternating → smooths noise, preserves volume and folds) makes for a cleaner print. Run [`scripts/smooth_stl.py`](scripts/smooth_stl.py):

```bash
python scripts/smooth_stl.py
```

- `iterations=10` — light-to-moderate smoothing; removes noise, keeps folds
- smoother → 20; keep more detail → 5
- volume drops ~5–7% (normal: surface bumps are flattened), watertightness is preserved

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `recon-all` license error | `license.txt` missing under `$FREESURFER_HOME` or `FS_LICENSE` not set |
| `lh.pial` is 0 bytes | It's a symlink to `lh.pial.T1`; fine inside the container |
| Stuck on a step for a long time | Topology fix / spherical registration are slow; check `recon-all-status.log` to confirm it's still advancing |
| `mris_convert` not found | `SetUpFreeSurfer.sh` not sourced; use full path `/usr/local/freesurfer/7.4.1/bin/mris_convert` |
| Docker slower than expected | Check actual `CPUs` in `docker info` — Docker Desktop only allocates a fraction of the host |

---

## Scripts

- [`scripts/run_recon.sh`](scripts/run_recon.sh) — recon-all wrapper (config at top)
- [`scripts/merge_stl.py`](scripts/merge_stl.py) — concatenate lh/rh pial STLs
- [`scripts/smooth_stl.py`](scripts/smooth_stl.py) — Taubin smoothing

**Privacy**: MRI data, patient info, and the FreeSurfer license are all sensitive — never commit them to a public repository.
