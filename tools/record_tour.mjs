// Record the dashboard's own tour to dashboard/tour.webm with headless Chrome and ffmpeg (no npm packages).
//   node tools/record_tour.mjs <work dir> [output]
// Serves dashboard/ on 127.0.0.1, blocks every other host (so the recording doubles as an offline check),
// starts the page's tour, screenshots as fast as the browser allows, and lets ffmpeg hold each frame for
// its real duration so the video runs at the tour's speed.
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const [WORK, OUT = `${ROOT}/dashboard/tour.webm`] = process.argv.slice(2);
if (!WORK) { console.error("usage: node tools/record_tour.mjs <work dir> [output]"); process.exit(2); }
const HTTP = 8771, CDP = 9336, frames = `${WORK}/frames`;
rmSync(frames, { recursive: true, force: true }); mkdirSync(frames, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const server = spawn("python3", ["-m", "http.server", String(HTTP), "--bind", "127.0.0.1", "--directory", `${ROOT}/dashboard`], { stdio: "ignore" });
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${CDP}`, `--user-data-dir=${WORK}/profile`,
  "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1", "--window-size=1280,800", "about:blank"], { stdio: "ignore" });
let failed = null;
try {
  let ok; for (let i = 0; i < 50 && !ok; i++) { try { ok = await (await fetch(`http://127.0.0.1:${CDP}/json/version`)).json(); } catch { await sleep(200); } }
  const targets = await (await fetch(`http://127.0.0.1:${CDP}/json`)).json();
  const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pending = new Map(); const errors = [];
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
  };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const evaluate = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true })).result?.result?.value;
  await send("Page.enable"); await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: `http://127.0.0.1:${HTTP}/index.html` });
  for (let i = 0; i < 100; i++) { if (await evaluate("typeof window.startTour === 'function' && !!document.querySelector('#board circle')")) break; await sleep(100); }
  const ready = await evaluate("JSON.stringify({ d3: typeof d3, tour: typeof window.startTour, board: document.querySelectorAll('#board circle').length, map: document.querySelectorAll('#usmap path').length, cands: document.querySelectorAll('#cands .cand').length })");
  console.log("page without network:", ready, "script errors:", JSON.stringify(errors));
  if (!ready || JSON.parse(ready).tour !== "function") throw new Error("the page did not load its tour");
  await evaluate("window.startTour(); 1");
  const t0 = Date.now(); const stamps = [];
  while (Date.now() - t0 < 90000) {
    const st = await evaluate("document.body.dataset.demo || ''");
    const r = await send("Page.captureScreenshot", { format: "jpeg", quality: 82 });
    const name = `f${String(stamps.length).padStart(5, "0")}.jpg`;
    writeFileSync(`${frames}/${name}`, Buffer.from(r.result.data, "base64")); stamps.push([name, Date.now()]);
    if (st && st !== "running") break;
  }
  ws.close();
  const list = stamps.map(([name, t], i) => `file '${name}'\nduration ${(((stamps[i + 1] || [0, t + 200])[1] - t) / 1000).toFixed(3)}`).join("\n") + `\nfile '${stamps[stamps.length - 1][0]}'\n`;
  writeFileSync(`${frames}/list.txt`, list);
  const seconds = (stamps[stamps.length - 1][1] - stamps[0][1]) / 1000;
  console.log(JSON.stringify({ frames: stamps.length, seconds: +seconds.toFixed(1), fps: +(stamps.length / seconds).toFixed(1) }));
  const ff = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", `${frames}/list.txt`, "-vf", "fps=12,scale=1280:-2",
    "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "38", "-pix_fmt", "yuv420p", OUT], { stdio: "inherit" });
  console.log(JSON.stringify({ ffmpeg_exit: ff.status, output: OUT }));
} catch (e) { failed = e; } finally { chrome.kill(); server.kill(); }
if (failed) { console.error(String(failed)); process.exit(1); }
