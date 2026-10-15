"""Builds the Witching Hour download: one folder per items plugin (Nexo, ItemsAdder,
Oraxen, or none), Blockbench files, previews, README and license, all zipped."""
import base64, io, json, os, shutil, uuid, zipfile
from PIL import Image
from engine import NS
from pieces import PIECES

VERSION = "1.0"
PACK = "Mistbloom_Witching_Hour"
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


GROUP_NAME = ["model"]


def _groups(parts):
    """One Blockbench folder per model, named after it."""
    out = []
    for label, test in (("all", lambda n: True),):
        kids = [u for n, u in parts if test(n)]
        if kids:
            out.append({"name": GROUP_NAME[0], "origin": [8, 8, 8], "color": 0, "uuid": str(uuid.uuid4()),
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
    for key, title, slot, lore, mk in PIECES:
        m = mk()
        m.check()
        entries.append((m, title, slot))
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
        w(os.path.join(base, folder, "items", "witching_hour.yml"),
          (nexo_items if plugin == "nexo" else oraxen_items)(entries))
        w(os.path.join(base, "HMCCosmetics", "cosmetics", "witching_hour.yml"), hmc_cosmetics(entries, plugin))
        w(os.path.join(base, "HMCCosmetics", "menus", "witching_hour.yml"), menu)
    base = os.path.join(root, "ItemsAdder", "plugins")
    ia = os.path.join(base, "ItemsAdder", "contents", "witching_hour")
    copy_assets(os.path.join(ia, "resourcepack", "assets", NS), with_items=False)
    w(os.path.join(ia, "configs", "witching_hour.yml"), ia_items(entries))
    w(os.path.join(base, "HMCCosmetics", "cosmetics", "witching_hour.yml"), hmc_cosmetics(entries, "itemsadder"))
    w(os.path.join(base, "HMCCosmetics", "menus", "witching_hour.yml"), menu)
    base = os.path.join(root, "No items plugin")
    w(os.path.join(base, "plugins", "HMCCosmetics", "cosmetics", "witching_hour.yml"), hmc_cosmetics(entries, "none"))
    w(os.path.join(base, "plugins", "HMCCosmetics", "menus", "witching_hour.yml"), menu)
    rp = os.path.abspath("dist/_rp")
    copy_assets(os.path.join(rp, "assets", NS))
    json.dump({"pack": {"pack_format": 46, "supported_formats": {"min_inclusive": 46, "max_inclusive": 999},
                        "description": "Witching Hour by Mistbloom Studios"}}, open(os.path.join(rp, "pack.mcmeta"), "w"), indent=1)
    zipdir(rp, os.path.join(base, f"{PACK}_ResourcePack.zip"))
    shutil.rmtree(rp)
    os.makedirs(os.path.join(root, "Blockbench"))
    for m, *_ in entries:
        GROUP_NAME[0] = m.name
        bbmodel(os.path.join(assets, "assets", NS, "models", "cosmetics", m.name + ".json"),
                os.path.join(assets, "assets", NS, "textures", "cosmetics", m.name + ".png"),
                os.path.join(root, "Blockbench", m.name + ".bbmodel"), m.name)
    shutil.copytree("preview", os.path.join(root, "Previews"))
    for f in (os.listdir("listing") if os.path.isdir("listing") else []):
        shutil.copy(os.path.join("listing", f), os.path.join(root, "Previews", f))
    w(os.path.join(root, "README.md"), readme(entries, VERSION))
    shutil.copy("LICENSE.txt", root)
    zipdir(root, os.path.abspath(f"dist/{PACK}_v{VERSION}.zip"), PACK)
    shutil.rmtree(assets)
    print("built", len(entries), "cosmetics")


if __name__ == "__main__":
    main()
