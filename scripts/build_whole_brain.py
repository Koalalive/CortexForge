"""
Build the "ultimate" whole-brain model: fine pial cerebrum + cerebellum + brainstem.

Strategy -- smooth each part BEFORE merging (per-part smoothing):
  - Cerebrum pial surface is already a smooth anatomical surface -> only 2 light
    Taubin passes, so the gyri/sulci stay intact.
  - Cerebellum & brainstem come from marching-cubes on aseg (voxel staircase)
    -> 20 passes to smooth out the steps.
  - Trim the cerebrum's inferior occipital pole and the cerebellum's tentorial
    top, so cerebrum and cerebellum remain separated by the tentorial gap.
  - Boolean-union all three: the brainstem bridges cerebrum and cerebellum into
    a single watertight solid, while the tentorial gap stays open.

Prereqs:
  - output/lh.pial.stl, output/rh.pial.stl   (from step 3 of the tutorial)
  - output/cerebellum.stl, output/brainstem.stl (from extract_cerebellum_brainstem.sh)
  - pip install trimesh manifold3d

Usage:  python build_whole_brain.py
Output: output/ultimate_brain.stl
"""
import trimesh

OUT = "output"

# --- load ---
lh = trimesh.load(f"{OUT}/lh.pial.stl")
rh = trimesh.load(f"{OUT}/rh.pial.stl")
cb = trimesh.load(f"{OUT}/cerebellum.stl")
bs = trimesh.load(f"{OUT}/brainstem.stl")

# --- trimming boxes (FreeSurfer RAS coordinates) ---
# Cerebrum: cut the inferior occipital pole (X +-16, Y -56..-26, Z < 10)
# so it does not touch the cerebellum. Keeps the temporal pole (Y > -20)
# and the brainstem apex (Y > -27) untouched.
box_brain = trimesh.creation.box(extents=[32, 30, 50])
box_brain.apply_translation([0, -41, -15])
# Cerebellum: cut the tentorial top (Z > -5)
box_cb = trimesh.creation.box(extents=[400, 400, 400])
box_cb.apply_translation([0, 0, 195])

# --- per-part smoothing ---
# cerebrum: light (preserve gyri)
lh_s = trimesh.smoothing.filter_taubin(lh, lamb=0.5, nu=-0.53, iterations=2)
rh_s = trimesh.smoothing.filter_taubin(rh, lamb=0.5, nu=-0.53, iterations=2)
# cerebellum & brainstem: heavy (remove voxel staircase)
cb_s = trimesh.smoothing.filter_taubin(cb, lamb=0.5, nu=-0.53, iterations=20)
bs_s = trimesh.smoothing.filter_taubin(bs, lamb=0.5, nu=-0.53, iterations=20)

# --- trim ---
lh_cut = trimesh.boolean.difference([lh_s, box_brain], engine="manifold")
rh_cut = trimesh.boolean.difference([rh_s, box_brain], engine="manifold")
cb_cut = trimesh.boolean.difference([cb_s, box_cb], engine="manifold")

# --- merge ---
union = trimesh.boolean.union([lh_cut, rh_cut, cb_cut, bs_s], engine="manifold")
parts = union.split(only_watertight=True)
main = max(parts, key=lambda x: len(x.faces))
main.fix_normals()

main.export(f"{OUT}/ultimate_brain.stl")
print(f"done: {len(main.vertices)} verts, watertight={main.is_watertight}, "
      f"vol={main.volume/1000:.1f} cm3, bodies={len(main.split())}")
