"""Drive Blockbench + Minecraft Title Generator headless and save renders.
usage: python3 title.py jobs.json outdir"""
import asyncio, sys, json, base64, os
from playwright.async_api import async_playwright

JOBS = json.load(open(sys.argv[1])); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)

SETUP = """async (src) => {
  window.confirm = () => true
  await new Plugin().loadFromFile({path:'minecraft_title_generator.js', name:'minecraft_title_generator.js', content: src}, true)
  return 'ok'
}"""

BUILD = """async (job) => {
  const M = window.__mtg
  if (Project) { Project.close && await Project.close(true) }
  newProject(M.format)
  if (!window.__fontsReady) {
    BarItems.minecraft_title_add_text.click()
    await M.initialLoad
    for (const d of Dialog.stack.slice()) { if (d.content_vue && 'textureSource' in d.content_vue) window.__mtgDialog = d; try { d.hide() } catch(e) {} }
    window.__fontsReady = true
  }
  let args
  if (job.dialogDefaults) {
    const d = Dialog.stack.concat(Object.values(Dialog.all||{})).find(d => d && d.content_vue && 'textureSource' in d.content_vue) || (window.__mtgDialog)
    const vue = d.content_vue
    args = {}
    for (const [k] of Object.values(M.variables).flat().flatMap(Object.entries)) args[k] = vue[k]
    if (vue.textureSource !== 'gradient') for (let x = 0; x < 5; x++) args['gradientColour' + x] = null
    args.variant = vue.textureSource === 'premade' ? vue.variant : null
    args.tileable = null; args.tileableVariant = null; args.customTexture = null; args.customOverlay = null
    Object.assign(args, job.args)
    window.__lastArgs = {font: args.font, texture: args.texture, overlay: args.overlay, type: args.type, textureSource: vue.textureSource}
  } else {
    args = M.getDefaultDialogArgs()
    Object.assign(args, job.args)
  }
  await M.getFontTextures(args.font)
  for (const e of (job.more||[])) if (e.args.font) await M.getFontTextures(e.args.font)
  args.ignoreStats = true
  if (!job.dialogDefaults) { if (!(args.texture in M.fonts[args.font].textures)) args.texture = 'flat'
  if (job.overlay !== undefined) args.overlay = job.overlay; else args.overlay = 'none' }
  await M.addText(job.text, args)
  for (const extra of (job.more || [])) {
    const a2 = job.dialogDefaults ? Object.assign({}, args, {type: 'top', row: 0}) : M.getDefaultDialogArgs(); Object.assign(a2, extra.args); a2.ignoreStats = true; if (!job.dialogDefaults) { if (!(a2.texture in M.fonts[a2.font].textures)) a2.texture='flat'; a2.overlay = a2.overlay || 'none' }
    await M.addText(extra.text, a2)
  }
  if (job.cam) { Preview.selected.loadAnglePreset({name:'c', id:'c', position: job.cam, target: [0, 0, 0]}) } else M.loadRenderAngle()
  if (job.zoom) { Preview.selected.camera.zoom = job.zoom; Preview.selected.camera.updateProjectionMatrix() }
  return {cubes: Cube.all.length, used: window.__lastArgs}
}"""

SHOT = """async (w) => {
  const p = Preview.selected
  try { unselectAllElements(); } catch(e) {}
  try { Transformer.visible = false; Transformer.detach && Transformer.detach() } catch(e) {}
  const r = p.renderer
  const oldSize = new THREE.Vector2(); r.getSize(oldSize)
  const h = Math.round(w * 0.5)
  p.camera.aspect = w / h; p.camera.updateProjectionMatrix()
  r.setPixelRatio(1); r.setSize(w, h, false)
  r.setClearColor(0x000000, 0)
  const vis = []
  Canvas.scene.traverse(o => { if ((o.type === 'Line' || o.type==='LineSegments' || o.name==='pivot_marker' || o===three_grid) && o.visible) { vis.push(o); o.visible = false } })
  p.render()
  r.render(Canvas.scene, p.camera)
  const url = r.domElement.toDataURL('image/png')
  vis.forEach(o => o.visible = true)
  r.setSize(oldSize.x, oldSize.y, false)
  return url
}"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": 1600, "height": 1000})
        logs = []
        pg.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
        pg.on("console", lambda m: m.type == "error" and logs.append(m.text))
        await pg.goto("http://localhost:8765/bb/index.html")
        await pg.wait_for_function("typeof Blockbench !== 'undefined' && typeof newProject === 'function'", timeout=60000)
        await pg.wait_for_timeout(3000)
        print(await pg.evaluate(SETUP, open("/root/mtg/mtg.js").read()))
        for job in JOBS:
            try:
                info = await pg.evaluate(BUILD, job)
                await pg.wait_for_timeout(1500)
                # fit camera: frame selection
                await pg.evaluate("() => { Canvas.updateAll(); }")
                url = await pg.evaluate(SHOT, job.get("w", 2400))
                open(os.path.join(OUT, job["name"] + ".png"), "wb").write(base64.b64decode(url.split(",")[1]))
                print(job["name"], info)
            except Exception as e:
                print(job["name"], "FAILED", str(e)[:400])
        print("\n".join(l for l in logs if "TUNNEL" not in l and "404" not in l)[-3000:])
        await b.close()
asyncio.run(main())
