# Halloween Festival showcase (Selling Test)

Floating festival island at world origin **-1450 150 -560** that shows off the Halloween (Hollowmere) furniture set,
plus an 11-shot MistCam film.

- `festival.py` - the build generator (blocks + 119 piece placements). Local frame: x across, y up, z from gate (-z) to barn (+z).
- `checks.py` - floating blocks, cottage gap flood, piece footing/clipping, palette.
- `render.py`, `views.py`, `storyboard.py` - preview renderer (blocks + real piece models, night lighting) and storyboard.
- `shots.py`, `camcheck.py`, `bake/Bake.java` - the 11 camera shots, baked through MistCam's own PathBaker and clearance-checked.
- `datapack.py` -> `datapack/` (hfest_showcase): `function hfest:build`, `hfest:furniture`, `hfest:clear`, `hfest:arrive`, tick ambience.
