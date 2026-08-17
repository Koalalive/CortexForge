"""
Apply Taubin smoothing to a brain STL for 3D printing.

Taubin smoothing alternates shrink/expand passes, smoothing surface
noise while preserving volume and the sulcal/gyral folds.

Usage:  python smooth_stl.py
Input:  output/brain_full.stl
Output: output/brain_full_smooth.stl
"""
import trimesh

SRC = "output/brain_full.stl"
DST = "output/brain_full_smooth.stl"

mesh = trimesh.load(SRC)
print(f"before: watertight={mesh.is_watertight}, volume={mesh.volume/1000:.1f} cm3", flush=True)

# lamb (shrink) + nu (expand) alternate -> smooth without collapsing folds
smooth = trimesh.smoothing.filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=10)
smooth.fix_normals()

smooth.export(DST)
print(f"after : watertight={smooth.is_watertight}, volume={smooth.volume/1000:.1f} cm3", flush=True)
print(f"saved {DST}", flush=True)
