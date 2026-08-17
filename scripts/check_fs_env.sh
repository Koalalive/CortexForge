#!/bin/bash
# Verify the FreeSurfer environment inside a Docker container.
#
# Run inside the container (same image you'll use for recon-all):
#   docker run --rm -v "<data_dir>:/data" <neuroimage-image> bash /data/scripts/check_fs_env.sh
#
# Override the defaults if your image differs:
#   FREESURFER_HOME=/opt/freesurfer FS_LICENSE=/data/license.txt bash check_fs_env.sh

set -e

FREESURFER_HOME="${FREESURFER_HOME:-/usr/local/freesurfer/7.4.1}"
FS_LICENSE="${FS_LICENSE:-/data/license.txt}"

export FREESURFER_HOME
export FS_LICENSE

echo "=== FreeSurfer environment check ==="
echo "FREESURFER_HOME = $FREESURFER_HOME"

if [ ! -d "$FREESURFER_HOME" ]; then
  echo "FAIL: $FREESURFER_HOME does not exist."
  echo "      Find the install with:  find / -name recon-all 2>/dev/null"
  exit 1
fi

if [ ! -f "$FREESURFER_HOME/SetUpFreeSurfer.sh" ]; then
  echo "FAIL: SetUpFreeSurfer.sh not found under $FREESURFER_HOME"
  exit 1
fi

if [ ! -f "$FS_LICENSE" ]; then
  echo "FAIL: license file not found at $FS_LICENSE"
  echo "      Register (free) at https://surfer.nmr.mgh.harvard.edu/registration.html"
  exit 1
fi
echo "license         = $FS_LICENSE (found)"

source "$FREESURFER_HOME/SetUpFreeSurfer.sh"

echo "recon-all       = $(which recon-all)"
echo "mris_convert    = $(which mris_convert)"
echo "mri_convert     = $(which mri_convert)"
echo "version         = $(recon-all -version 2>&1 | head -1)"

echo ""
echo "=== OK: environment is ready for recon-all ==="
