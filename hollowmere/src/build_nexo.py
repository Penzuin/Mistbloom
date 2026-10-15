import os, shutil, re, importlib
import configs
ROOT = "dist/Nexo"
shutil.rmtree("dist", ignore_errors=True)
models = []
for mod in "hero3 harvest witchy graveyard critters market".split():
    models += importlib.import_module(mod).all_models()
for m in models:
    m.check(); m.export(f"{ROOT}/pack")
os.makedirs(f"{ROOT}/items", exist_ok=True)
txt = configs.nexo()
open(f"{ROOT}/items/hollowmere.yml", "w").write(txt)
ok = {m.name for m in models}
refs = set(re.findall(r"hollowmere:([a-z_]+)", txt))
assert refs <= ok, refs - ok
print(len(models), "models;", len(configs.SPEC), "items; unused models:", ok - refs)
