---
name: cortexforge
description: Generate a 3D-printable brain cortex STL from brain MRI (DICOM/NIfTI). Covers dcm2niix conversion, FreeSurfer environment setup and recon-all cortical reconstruction, pial surface extraction, hemisphere merge + watertight, and Taubin smoothing. Includes detailed FreeSurfer setup for beginners. Triggers: MRI, DICOM, NIfTI, FreeSurfer, recon-all, cortical surface, pial surface, STL, 3D print brain, brain model.
---

# 🧠 CortexForge

> Forge a 3D-printable brain from any MRI.

Turn a T1-weighted brain MRI into a 3D-printable cortical model (with sulcal/gyral folds) that drops straight into any slicer.

```
DICOM ──dcm2niix──▶ NIfTI ──recon-all──▶ pial surface ──mris_convert──▶ STL ──trimesh──▶ merge + watertight + smooth
```

---

## 0. Prerequisites

You need four things: **Docker**, a **FreeSurfer image**, a **FreeSurfer license**, and a **Python environment**.

| Dependency | Purpose | Effort |
|---|---|---|
| Docker Desktop | Run FreeSurfer in a container | ~10 min, one-time |
| A FreeSurfer Docker image | recon-all | ~10 min download |
| FreeSurfer **license** | Required by recon-all | ~2 min, free registration |
| Python (conda/venv) | Mesh processing | ~5 min |

### 0.1 Install Docker

- **Windows / macOS**: install [Docker Desktop](https://www.docker.com/products/docker-desktop/). On Windows, it runs a Linux VM via WSL2 — accept the default WSL2 backend during install.
- **Linux**: `sudo apt-get install docker.io` (or follow Docker's official install script).

Verify it works:

```bash
docker version          # shows Client + Server, both must appear
docker info             # shows "CPUs" and "Total Memory" the container can actually use
```

> ⚠️ On Windows/macOS, Docker Desktop only gives the Linux VM a **fraction** of your host CPU/RAM. Note the `CPUs` number from `docker info` — you'll cap `-openmp` at it later.

### 0.2 Get a FreeSurfer Docker image

Pick one:

- **Official** (easiest): `docker pull freesurfer/freesurfer:7.4.1`
- **Any image that bundles FreeSurfer** (e.g. a lab's neuroimaging image). This tutorial writes `<neuroimage-image>` where the image name goes; substitute yours.

Find where FreeSurfer is installed inside the image:

```bash
docker run --rm <neuroimage-image> bash -c "find / -name recon-all 2>/dev/null"
# e.g. -> /usr/local/freesurfer/7.4.1/bin/recon-all
```

The parent directory (`/usr/local/freesurfer/7.4.1` in this example) is your `FREESURFER_HOME`. Remember it.

### 0.3 Get a FreeSurfer license (free, 2 minutes)

`recon-all` **refuses to run without a license**. It's free but must be registered to you personally.

1. Open https://surfer.nmr.mgh.harvard.edu/registration.html
2. Fill in first/last name, institution, and email, submit
3. You receive an email containing the license text (your email + a registration key)
4. Save that text to a plain file named `license.txt`

A `license.txt` looks like this (placeholder values — yours will differ):

```
your-email@example.com
12345
*XXXXXXX
*XXXXXXX
<base64 registration key>
```

> 🔒 **Keep `license.txt` private.** It is tied to you. Never commit it to a public repo, and don't paste its contents anywhere public.

### 0.4 Python environment

Any Python 3.9+ works. Create an isolated environment (recommended):

```bash
conda create -n brain python=3.11 -y
conda activate brain
pip install pydicom dcm2niix trimesh nibabel
```

---

## 1. Understanding the FreeSurfer environment (read this first)

Most confusion comes from FreeSurfer's environment setup. Here's the mental model.

### 1.1 The three things FreeSurfer needs

Every FreeSurfer command requires three pieces of state, set via environment variables:

| Variable | What it is | Example | Required? |
|---|---|---|---|
| `FREESURFER_HOME` | Where FreeSurfer is installed | `/usr/local/freesurfer/7.4.1` | ✅ always |
| `FS_LICENSE` (or `license.txt`) | Your license file | `/data/license.txt` | ✅ always |
| `SUBJECTS_DIR` | Where results are written | `/data/freesurfer` | ✅ for recon-all |
| `PATH` (updated) | So `recon-all`, `mris_convert`, etc. are found | `$FREESURFER_HOME/bin` | ✅ to run by name |

### 1.2 `SetUpFreeSurfer.sh` — what it does

FreeSurfer ships a script, `$FREESURFER_HOME/SetUpFreeSurfer.sh`, that sets `PATH` and a dozen internal variables for you. You must **source** it (not execute it) in every fresh shell:

```bash
export FREESURFER_HOME=/usr/local/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh
```

Without this, you'll see:

```
ERROR: FreeSurfer environment FREESURFER_HOME is not defined.
```

or `command not found: mris_convert`.

### 1.3 The license: two ways to point at it

FreeSurfer accepts either:

1. **`license.txt` sitting in `$FREESURFER_HOME/`** — the classic location; or
2. **`FS_LICENSE` environment variable** pointing at the file anywhere.

```bash
export FS_LICENSE=/data/license.txt      # works if license.txt is anywhere
```

If neither is set, `recon-all` fails immediately with a license error.

### 1.4 Verify your environment before the long run

Run the bundled check script (see [`scripts/check_fs_env.sh`](scripts/check_fs_env.sh)) or manually:

```bash
docker run --rm -v "<data_dir>:/data" <neuroimage-image> bash -c '
  export FREESURFER_HOME=/usr/local/freesurfer/7.4.1
  export FS_LICENSE=/data/license.txt
  source $FREESURFER_HOME/SetUpFreeSurfer.sh
  echo "FREESURFER_HOME = $FREESURFER_HOME"
  which recon-all mris_convert mri_convert
  recon-all -version | head -1
  # if this prints without a license error, you are good to go
'
```

A correct setup prints the paths and a version line like `freesurfer-linux-...-7.4.1-...`.

---

## 2. DICOM → NIfTI

Convert the raw DICOM series (a 3D T1, e.g. `t1_mprage_sag_1mm`) to NIfTI:

```bash
dcm2niix -z y -b y -f "%p" -o <output_dir> <dicom_series_dir>
```

| Flag | Meaning |
|---|---|
| `-z y` | compress to `.nii.gz` |
| `-b y` | also emit a BIDS JSON sidecar (sequence parameters) |
| `-f "%p"` | name files after the protocol |
| `-o <dir>` | output directory |

Verify the result:

```bash
python -c "import nibabel as n; img=n.load('<t1>.nii.gz'); print(img.shape, img.header.get_zooms(), n.aff2axcodes(img.affine))"
```

Expect something like `(256, 256, 208) (0.9, 0.9, 0.9) ('R','A','S')`. The voxel size should be near-isotropic **1 mm** — this is ideal for recon-all. The orientation code `RAS` means dcm2niix already reoriented the volume to a standard convention.

---

## 3. FreeSurfer recon-all

The slowest step (4–8 hours on CPU). Run it in the background.

### 3.1 Lay out your data directory

Put everything in one folder that you'll mount into the container as `/data`:

```
<data_dir>/
├── license.txt            # your FreeSurfer license (private)
├── <t1>.nii.gz            # the T1 you made in step 2
└── scripts/
    └── run_recon.sh       # from this repo
```

### 3.2 Edit and run the recon-all script

Use [`scripts/run_recon.sh`](scripts/run_recon.sh). Edit the config block at the top:

```bash
SUBJECT="subj01"                              # any name; becomes the output folder
INPUT_NIFTI="/data/<t1>.nii.gz"               # your T1 (path inside the container)
NTHREADS=16                                   # <= the CPUs from `docker info`
FREESURFER_HOME="/usr/local/freesurfer/7.4.1" # the path you found in 0.2
```

Launch in the background:

```bash
docker run -d --name recon \
  -v "<data_dir>:/data" \
  <neuroimage-image> bash /data/scripts/run_recon.sh
```

What each part means:

| Part | Meaning |
|---|---|
| `-d` | run detached (background) |
| `--name recon` | container name, so you can inspect it later |
| `-v "<data_dir>:/data"` | mount your folder at `/data` inside the container |
| `bash /data/scripts/run_recon.sh` | run the script (which sources FreeSurfer and calls recon-all) |

### 3.3 Track progress

```bash
docker ps -a --filter "name=recon"      # is the container still running?
tail -f <data_dir>/recon_all.log        # overall stdout
grep '^#@#' <data_dir>/freesurfer/subj01/scripts/recon-all-status.log   # completed steps
```

Success marker at the end of the log:

```
recon-all -s subj01 finished without error at ...
```

### 3.4 What's happening under the hood

recon-all `-all` runs ~40 steps in three phases:

- **autorecon1** (~15 min): motion correction, Talairach alignment, N4 bias-field correction, intensity normalization.
- **autorecon2** (1–2 h): skull stripping, white-matter segmentation, tiling the cortex into a triangle mesh, smoothing, inflation, spherical projection, and the slow **automatic topology fixer**.
- **autorecon3** (2–3 h): spherical surface registration (one per hemisphere — slow), pial surface generation, thickness, ribbon, and the Desikan–Killiany parcellation.

The three stages that look "stuck" — topology fixer, per-hemisphere spherical registration, and parcellation — are simply slow. Check the status log to confirm it's still advancing.

---

## 4. pial surface → STL

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

- `lh.pial` / `rh.pial` = left/right **pial surface** (the outer cortical boundary, where the gyri are).
- `lh.white` = white-matter surface (inner boundary) — use this if you want a smoother, fold-detail-free model instead.

> ⚠️ **Gotcha**: on a Windows-mounted directory, `lh.pial` / `rh.pial` show as **0 bytes** — they are **symlinks** (`lh.pial -> lh.pial.T1`); the real file is `lh.pial.T1` (several MB). Windows Explorer shows Linux symlinks as 0-byte files, but inside the container `mris_convert` follows the link fine — the data is complete, nothing to fix.

FreeSurfer's pial surfaces are **already watertight closed meshes** (one closed shell per hemisphere), ideal for 3D printing.

---

## 5. Merge hemispheres + watertight

Run [`scripts/merge_stl.py`](scripts/merge_stl.py):

```bash
python scripts/merge_stl.py
```

Produces `output/brain_full.stl` — the two hemisphere shells in one file (separated at the interhemispheric fissure, as in real anatomy), each shell watertight and slicer-ready.

Expected output:

```
lh: 176680 verts, watertight=True
rh: 180429 verts, watertight=True
saved brain_full.stl
watertight=True, volume=1227.2 cm3
```

---

## 6. Taubin smoothing (optional, recommended)

Run [`scripts/smooth_stl.py`](scripts/smooth_stl.py):

```bash
python scripts/smooth_stl.py
```

- `iterations=10` — light-to-moderate smoothing; removes per-vertex noise, keeps folds
- smoother → 20; keep more detail → 5
- volume drops ~5–7% (normal: surface bumps are flattened), watertightness is preserved

---

## 7. Whole-brain model (cerebrum + cerebellum + brainstem)

The pial surface gives you the cerebrum only. To add the cerebellum and brainstem (a full "whole brain"), pull them from the aseg segmentation and merge everything with **per-part smoothing**.

### 7.1 Extract cerebellum + brainstem

Run [`scripts/extract_cerebellum_brainstem.sh`](scripts/extract_cerebellum_brainstem.sh) inside the container. It binarizes the aseg labels for the cerebellum (7,8,46,47) and brainstem (16), runs marching cubes (`mri_mc`), and converts each to STL.

### 7.2 Build the whole brain (per-part smoothing)

Run [`scripts/build_whole_brain.py`](scripts/build_whole_brain.py):

```bash
pip install trimesh manifold3d   # boolean + smoothing engines
python scripts/build_whole_brain.py
```

**Why smooth each part separately, not the merged model?**

The three parts have very different surface natures:

| Part | Source | Surface | Smoothing |
|---|---|---|---|
| Cerebrum | pial surface | already smooth, fine gyri | **2 light passes** (preserve folds) |
| Cerebellum | aseg marching cubes | voxel staircase | **20 passes** (remove steps) |
| Brainstem | aseg marching cubes | voxel staircase | **20 passes** (remove steps) |

Smoothing the merged whole uniformly would either melt the cerebrum's gyri (too strong) or leave the cerebellum/brainstem stepped (too weak). Smooth-then-merge hits both goals.

**Keeping the cerebrum and cerebellum separated (the tentorial gap):**

FreeSurfer's pial surface and aseg labels overlap at the tentorium — the cerebrum's inferior occipital pole (its pial dips too low) against the cerebellum's top (its aseg label rises too high). A plain union would weld them together, which is anatomically wrong: they should stay separated by the tentorial gap. The script therefore:

1. trims the cerebrum's inferior occipital pole (`Z < 10`, only in the midline-posterior region),
2. trims the cerebellum's tentorial top (`Z > -5`),
3. unions the three, leaving a ~6 mm tentorial gap while the brainstem still bridges them.

The brainstem is deliberately left untrimmed: its apex (`Y > -27`) reaches the cerebrum and its base connects the cerebellum, so it remains the only bridge — exactly the real anatomy. (The brainstem apex and the cerebellum top don't overlap in `Y`, which is what makes this split clean.)

Output: `output/ultimate_brain.stl` — a single watertight solid.

### 7.3 Verify the gap

```python
import trimesh
m = trimesh.load("output/ultimate_brain.stl")
for z in [0, 2, 4]:
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    rear = ((abs(sec.vertices[:, 0]) < 15) & (sec.vertices[:, 1] < -27) & (sec.vertices[:, 1] > -48)).sum()
    print(f"Z={z}: {rear} verts in the tentorial region")  # 0 = separated
```

---

## 8. Troubleshooting

### Environment

| Symptom | Cause / fix |
|---|---|
| `ERROR: FreeSurfer environment FREESURFER_HOME is not defined` | You didn't `export FREESURFER_HOME` or `source SetUpFreeSurfer.sh` |
| `command not found: recon-all` / `mris_convert` | `SetUpFreeSurfer.sh` not sourced; use full path `/usr/local/freesurfer/7.4.1/bin/<tool>` |
| `ERROR: FreeSurfer license ... not found` | `license.txt` missing from `$FREESURFER_HOME` and `FS_LICENSE` not set |
| recon-all starts then dies immediately | Usually a license problem — check the log's first lines |

### Docker

| Symptom | Cause / fix |
|---|---|
| `docker info` shows fewer CPUs than your host | Docker Desktop VM cap — lower `-openmp` to match |
| `-v` mount shows empty inside container | Windows path not shared; check Docker Desktop → Settings → Resources → File Sharing |
| Container exits with non-zero code | `docker logs recon` for the error; often a bad `INPUT_NIFTI` path |

### Data

| Symptom | Cause / fix |
|---|---|
| `lh.pial` is 0 bytes | Symlink to `lh.pial.T1`; fine inside the container |
| recon-all complains the image isn't a T1 | You may have pointed it at a T2/FLAIR; recon-all needs a T1 (or T2 for some pipelines) |
| Stuck on a step for a long time | Topology fix / spherical registration are slow; check `recon-all-status.log` is advancing |

---

## Scripts

- [`scripts/check_fs_env.sh`](scripts/check_fs_env.sh) — verify the FreeSurfer environment (license, paths, tools)
- [`scripts/run_recon.sh`](scripts/run_recon.sh) — recon-all wrapper (config at top)
- [`scripts/merge_stl.py`](scripts/merge_stl.py) — concatenate lh/rh pial STLs
- [`scripts/smooth_stl.py`](scripts/smooth_stl.py) — Taubin smoothing
- [`scripts/extract_cerebellum_brainstem.sh`](scripts/extract_cerebellum_brainstem.sh) — extract cerebellum + brainstem from aseg
- [`scripts/build_whole_brain.py`](scripts/build_whole_brain.py) — per-part smoothing + trim + boolean-union into the whole brain

**Privacy**: MRI data, patient info, and the FreeSurfer license are all sensitive — never commit them to a public repository.
