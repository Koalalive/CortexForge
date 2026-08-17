#!/bin/bash
# FreeSurfer cortical reconstruction (recon-all) for a single T1-weighted image.
# Run this script INSIDE a Docker container with the data directory mounted at /data.
#
# Usage:
#   docker run -d --name recon -v "<data_dir>:/data" <neuroimage-image> bash /data/scripts/run_recon.sh
#
set -e

# ------------------ config ------------------
SUBJECT="subj01"                          # subject / output folder name
INPUT_NIFTI="/data/<t1>.nii.gz"           # T1 image inside the container (replace with your file)
NTHREADS=16                               # OpenMP threads (do not exceed Docker Desktop's CPU limit)
FREESURFER_HOME="/usr/local/freesurfer/7.4.1"   # adjust to your image's FreeSurfer path
# ---------------------------------------------

export FREESURFER_HOME
export FS_LICENSE="/data/license.txt"     # your FreeSurfer license (keep private!)
export SUBJECTS_DIR="/data/freesurfer"

source "$FREESURFER_HOME/SetUpFreeSurfer.sh"
mkdir -p "$SUBJECTS_DIR"

recon-all -all -s "$SUBJECT" -i "$INPUT_NIFTI" -openmp "$NTHREADS" \
    > /data/recon_all.log 2>&1

echo "recon-all finished. Check /data/recon_all.log for the 'finished without error' message."
