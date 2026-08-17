"""
Merge left/right pial surface STLs into a single 3D-printable brain model.

FreeSurfer's pial surfaces are already watertight closed meshes
(one per hemisphere). This script concatenates them into one STL file.

Usage:  python merge_stl.py
Output: output/brain_full.stl
"""
import trimesh
import os

OUT = "output"          # directory containing lh.pial.stl / rh.pial.stl

lh = trimesh.load(os.path.join(OUT, "lh.pial.stl"))
rh = trimesh.load(os.path.join(OUT, "rh.pial.stl"))

print(f"lh: {len(lh.vertices)} verts, watertight={lh.is_watertight}", flush=True)
print(f"rh: {len(rh.vertices)} verts, watertight={rh.is_watertight}", flush=True)

# Concatenate the two watertight hemisphere shells
combined = trimesh.util.concatenate([lh, rh])
combined = combined.process(validate=True)   # merge duplicate verts, drop degenerate faces
combined.fix_normals()                        # unify outward normals

combined.export(os.path.join(OUT, "brain_full.stl"))
print(f"saved brain_full.stl", flush=True)
print(f"watertight={combined.is_watertight}, "
      f"volume={combined.volume/1000:.1f} cm3, "
      f"extents={combined.extents}", flush=True)
