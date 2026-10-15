# Koi Garden build

`cd src && python3 pack.py` writes the finished buyer folder to `src/out/Koi-Garden/`
(copied here as `Koi-Garden/`). Zip that folder for the store.

- `pieces.py` still models, `addon.py` koi rigs, `pack.py` the pack (ModelEngine furniture, items file, README/LICENSE).
- Server install: copy `Koi-Garden/Nexo` and `Koi-Garden/ModelEngine` into `plugins/`, then `/meg reload` and `/nexo reload all`.
