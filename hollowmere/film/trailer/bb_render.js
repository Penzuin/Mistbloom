// Render a BeepBox JSON song to a 48 kHz stereo WAV, offline (node bb_render.js song.json out.wav [tailSeconds])
const fs = require("fs"), vm = require("vm");
global.window = global; global.self = global;
vm.runInThisContext(fs.readFileSync("/home/claude/bbtool/beepbox/bundle/beepbox_synth.js", "utf8"));
const { Song, Synth } = global.beepbox;
const song = new Song();
song.fromJsonObject(JSON.parse(fs.readFileSync(process.argv[2], "utf8")));
const synth = new Synth(song);
synth.samplesPerSecond = 48000;
synth.loopRepeatCount = 0;
const tail = parseFloat(process.argv[4] || "4");
const songSamples = Math.ceil(synth.getSamplesPerBar() * song.barCount);
const total = songSamples + Math.round(tail * 48000);
const L = new Float32Array(total), R = new Float32Array(total);
synth.warmUpSynthesizer(song);
const CH = 4096;
for (let i = 0; i < total; i += CH) {
  const n = Math.min(CH, total - i);
  const l = new Float32Array(n), r = new Float32Array(n);
  synth.synthesize(l, r, n, i < songSamples);
  L.set(l, i); R.set(r, i);
}
let peak = 1e-9; for (let i = 0; i < total; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
const buf = Buffer.alloc(44 + total * 4);
buf.write("RIFF", 0); buf.writeUInt32LE(36 + total * 4, 4); buf.write("WAVEfmt ", 8);
buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(48000, 24);
buf.writeUInt32LE(48000 * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write("data", 36); buf.writeUInt32LE(total * 4, 40);
const g = 0.89 / peak;   // normalise to about -1 dBFS
for (let i = 0; i < total; i++) {
  buf.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(L[i] * g * 32767))), 44 + i * 4);
  buf.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(R[i] * g * 32767))), 46 + i * 4);
}
fs.writeFileSync(process.argv[3], buf);
console.log("bars", song.barCount, "song s", (songSamples / 48000).toFixed(2), "peak", peak.toFixed(3));
