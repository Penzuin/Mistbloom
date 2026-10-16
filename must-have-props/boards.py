"""Category boards for Payhip (its cover gallery holds only 9 items): the piece icons of one group in a grid."""
import glob
from PIL import Image
M = "/root/props/media"
GROUPS = {"lights": [1, 2, 3, 4], "outdoor-town": [5, 6, 7, 8], "storage-clutter": [9, 10, 11, 12, 13, 14]}
GAP, BG = 8, (52, 60, 46)
for i, (g, nums) in enumerate(GROUPS.items(), 1):
    files = [glob.glob(f"{M}/must-have-props-{n:02d}-*.png")[0] for n in nums]
    cols = 2 if len(files) == 4 else 3
    rows = (len(files) + cols - 1) // cols
    cell = 512
    out = Image.new("RGB", (cols * cell + (cols + 1) * GAP, rows * cell + (rows + 1) * GAP), BG)
    for j, f in enumerate(files):
        im = Image.open(f).resize((cell, cell), Image.LANCZOS)
        out.paste(im, (GAP + (j % cols) * (cell + GAP), GAP + (j // cols) * (cell + GAP)))
    out.save(f"{M}/must-have-props-board-{i}-{g}.png")
    print(g, out.size)
