#!/bin/bash
# Extract cerebellum + brainstem from recon-all's aseg.mgz into STL.
# Run INSIDE a FreeSurfer Docker container with the data directory mounted at /data.
#
# Usage:
#   docker run --rm -v "<data_dir>:/data" <neuroimage-image> bash /data/scripts/extract_cerebellum_brainstem.sh
#
set -e

# ------------------ config ------------------
SUBJECT="subj01"
FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
# ---------------------------------------------

export FREESURFER_HOME
export FS_LICENSE="/data/license.txt"
source "$FREESURFER_HOME/SetUpFreeSurfer.sh"
mkdir -p /data/output

ASEG="/data/freesurfer/$SUBJECT/mri/aseg.mgz"

# Cerebellum (labels 7,8 = white matter, 46,47 = cortex)
echo "=== cerebellum ==="
mri_binarize --i "$ASEG" --match 7 8 46 47 --o /data/output/cerebellum_mask.mgz
mri_mc /data/output/cerebellum_mask.mgz 1 /data/output/cerebellum.surf
mris_convert /data/output/cerebellum.surf /data/output/cerebellum.stl

# Brainstem (label 16)
echo "=== brainstem ==="
mri_binarize --i "$ASEG" --match 16 --o /data/output/brainstem_mask.mgz
mri_mc /data/output/brainstem_mask.mgz 1 /data/output/brainstem.surf
mris_convert /data/output/brainstem.surf /data/output/brainstem.stl

echo "=== done ==="
ls -la /data/output/cerebellum.stl /data/output/brainstem.stl
