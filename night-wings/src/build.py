"""Builds the Night Wings download: one folder per items plugin (Nexo, ItemsAdder,
Oraxen, or none), Blockbench files, previews, README and license, all zipped."""
import base64, io, json, os, shutil, uuid, zipfile
from PIL import Image
from engine import NS
from wings import WINGS

VERSION = "1.0"
PACK = "Mistbloom_Night_Wings"
CREDIT = "Mistbloom Studios"


from configs import nexo_items, oraxen_items, ia_items, hmc_cosmetics, hmc_menu


def bbmodel(model_json_path, tex_path, out_path, name):
    m = json.load(open(model_json_path))
    im = Image.open(tex_path)
    S = im.width
    buf = io.BytesIO(); im.save(buf, "PNG")
    k = S / 16
    elements, outliner = [], []
    for i, e in enumerate(m["elements"]):
        u = str(uuid.uuid4())
        rot, origin = [0, 0, 0], [8, 8, 8]
        if "rotation" in e:
            rot["xyz".index(e["rotation"]["axis"])] = e["rotation"]["angle"]
            origin = e["rotation"]["origin"]
        faces = {f: {"uv": [v * k for v in fd["uv"]], "texture": 0, **({"tint": 0} if "tintindex" in fd else {})}
                 for f, fd in e["faces"].items()}
        el = {"name": e.get("name", f"detail_{i}"), "type": "cube", "box_uv": False, "from": e["from"], "to": e["to"],
              "origin": origin, "rotation": rot, "faces": faces, "uuid": u}
        if e.get("light_emission"):
            el["light_emission"] = e["light_emission"]
        elements.append(el)
        outliner.append((el["name"], u))
    tex = {"name": f"{name}.png", "id": "0", "width": S, "height": im.height, "uv_width": S, "uv_height": S,
           "namespace": NS, "folder": "cosmetics", "uuid": str(uuid.uuid4()),
           "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}
    if im.height > S:
        tex["frame_time"] = 3
    json.dump({"meta": {"format_version": "4.10", "model_format": "java_block", "box_uv": False},
               "name": name, "parent": "", "ambientocclusion": True, "front_gui_light": False,
               "visible_box": [1, 1, 0], "resolution": {"width": S, "height": S},
               "elements": elements, "outliner": _groups(outliner), "textures": [tex], "display": m.get("display", {})},
              open(out_path, "w"))


def _groups(parts):
    """Blockbench folders: left wing, right wing, and everything else."""
    out = []
    for label, test in (("left_wing", lambda n: n.startswith("left_")),
                        ("right_wing", lambda n: n.startswith("right_")),
                        ("details", lambda n: not n.startswith(("left_", "right_")))):
        kids = [u for n, u in parts if test(n)]
        if kids:
            out.append({"name": label, "origin": [8, 8, 8], "color": 0, "uuid": str(uuid.uuid4()),
                        "export": True, "isOpen": True, "visibility": True, "children": kids})
    return out


def zipdir(src, dst, prefix=""):
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(src):
            for f in sorted(files):
                p = os.path.join(base, f)
                z.write(p, os.path.join(prefix, os.path.relpath(p, src)))


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)


def main():
    from readme import readme
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    entries = []
    for key, title, blurb, mk in WINGS:
        m = mk()
        m.check()
        entries.append((m, title, blurb))
    assets = os.path.abspath("dist/_assets")
    for m, *_ in entries:
        m.export(assets, CREDIT)
    root = os.path.abspath(f"dist/{PACK}")

    def copy_assets(dst, with_items=True):
        for sub in ("models/cosmetics", "textures/cosmetics") + (("items",) if with_items else ()):
            shutil.copytree(os.path.join(assets, "assets", NS, sub), os.path.join(dst, sub), dirs_exist_ok=True)

    menu = hmc_menu(entries)
    for plugin, folder in (("nexo", "Nexo"), ("oraxen", "Oraxen")):
        base = os.path.join(root, folder, "plugins")
        copy_assets(os.path.join(base, folder, "pack", "assets", NS))
        w(os.path.join(base, folder, "items", "night_wings.yml"),
          (nexo_items if plugin == "nexo" else oraxen_items)(entries))
        w(os.path.join(base, "HMCCosmetics", "cosmetics", "night_wings.yml"), hmc_cosmetics(entries, plugin))
        w(os.path.join(base, "HMCCosmetics", "menus", "night_wings.yml"), menu)
    base = os.path.join(root, "ItemsAdder", "plugins")
    ia = os.path.join(base, "ItemsAdder", "contents", "night_wings")
    copy_assets(os.path.join(ia, "resourcepack", "assets", NS), with_items=False)
    w(os.path.join(ia, "configs", "night_wings.yml"), ia_items(entries))
    w(os.path.join(base, "HMCCosmetics", "cosmetics", "night_wings.yml"), hmc_cosmetics(entries, "itemsadder"))
    w(os.path.join(base, "HMCCosmetics", "menus", "night_wings.yml"), menu)
    base = os.path.join(root, "No items plugin")
    w(os.path.join(base, "plugins", "HMCCosmetics", "cosmetics", "night_wings.yml"), hmc_cosmetics(entries, "none"))
    w(os.path.join(base, "plugins", "HMCCosmetics", "menus", "night_wings.yml"), menu)
    rp = os.path.abspath("dist/_rp")
    copy_assets(os.path.join(rp, "assets", NS))
    json.dump({"pack": {"pack_format": 46, "supported_formats": {"min_inclusive": 46, "max_inclusive": 999},
                        "description": "Night Wings by Mistbloom Studios"}}, open(os.path.join(rp, "pack.mcmeta"), "w"), indent=1)
    zipdir(rp, os.path.join(base, f"{PACK}_ResourcePack.zip"))
    shutil.rmtree(rp)
    os.makedirs(os.path.join(root, "Blockbench"))
    for m, *_ in entries:
        bbmodel(os.path.join(assets, "assets", NS, "models", "cosmetics", m.name + ".json"),
                os.path.join(assets, "assets", NS, "textures", "cosmetics", m.name + ".png"),
                os.path.join(root, "Blockbench", m.name + ".bbmodel"), m.name)
    open(os.path.join(root, "README.txt"), "w", newline="\r\n").write(readme(entries, VERSION))
    open(os.path.join(root, "LICENSE.txt"), "w", newline="\r\n").write(open("LICENSE.txt").read())
    zipdir(root, os.path.abspath(f"dist/{PACK}_v{VERSION}.zip"), PACK)
    shutil.rmtree(assets)
    print("built", len(entries), "wings")


if __name__ == "__main__":
    main()
