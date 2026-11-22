// Wizard like Mixamo's auto-rigger: Upload -> Orient -> Markers (or fully automatic) -> Preview. Talks to server.py.
import * as THREE from "three";
import { pivot, load, show, skeleton, wave, setView, view } from "./scene.js";
import * as MK from "./markers.js";

const $ = id => document.getElementById(id);
const HELP = {
  upload: "Upload a character in T-pose or A-pose (FBX, OBJ or GLB), standing, no animation needed.",
  orient: "For best results the character stands upright and faces the green arrow (front). Turn it with the buttons: left, right, upside down.",
  markers: "Choose Automatic, or place markers: drag each circle onto the model (chin, wrists, elbows, knees, groin). Orientation is fixed here (go back to Orient to turn the model); Free 3D only changes your point of view. Drag a placed marker to adjust it.",
  preview: "Skeleton and skin from the auto-rigger. Switch the skeleton on and off or run the test pose to check the weights.",
};
const ORDER = ["upload", "orient", "markers", "preview"];
pivot.rotation.order = "YXZ";                                             // yaw after the flip, as prep.py does
const S = { step: "upload", id: "", name: "", yaw: 0, flip: false, info: null, busy: false };

function status(t) { $("status").textContent = t || ""; }
function go(step) {
  S.step = step; const i = ORDER.indexOf(step);
  document.querySelectorAll("#steps li").forEach(li => li.classList.toggle("on", li.dataset.s === step));
  $("help").textContent = HELP[step];
  $("drop").hidden = step !== "upload"; $("orient").hidden = step !== "orient"; $("legend").hidden = step !== "markers";
  $("opts").hidden = step !== "markers"; $("views").hidden = step !== "markers"; $("ref").toggleAttribute("hidden", step !== "markers"); setView(step === "markers" ? $("free").checked : true); $("after").hidden = step !== "preview";
  $("back").style.visibility = i === 0 || step === "preview" ? "hidden" : "visible";
  $("next").style.visibility = step === "upload" || step === "preview" ? "hidden" : "visible";
  $("next").textContent = step === "markers" ? "Rig it" : "Next";
  MK.show(step === "markers");
  if (step === "preview") $("back").style.visibility = "visible";
}

async function prep(body) {
  status("Preparing the model…"); S.busy = true;
  const q = new URLSearchParams({ id: S.id, name: S.name, yaw: S.yaw, flip: S.flip ? 1 : 0 });
  const r = await (await fetch("/prep?" + q, { method: "POST", body: body || new Uint8Array() })).json();
  S.busy = false; status(r.ok ? "" : "prep failed: " + r.log);
  if (!r.ok) return false;
  S.id = r.id; S.yaw = 0; S.flip = false;
  S.info = show(await load(r.glb, "m.glb")); MK.config.setCenter(S.info.center.x);
  return true;
}

async function upload(file) {
  S.name = file.name; S.id = "";
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["fbx", "obj", "glb", "gltf"].includes(ext)) return status("Unsupported file: " + ext);
  if (await prep(await file.arrayBuffer())) go("orient");
}

function turn(dy, flip) {
  $("yaw").value = ((S.yaw + dy) % 360 + 360) % 360 > 180 ? ((S.yaw + dy) % 360 + 360) % 360 - 360 : ((S.yaw + dy) % 360 + 360) % 360;                                                 // visual only until Next bakes it in
  if (flip) { S.flip = !S.flip; pivot.rotation.x = S.flip ? Math.PI : 0; return; }
  S.yaw += dy; pivot.rotation.y = THREE.MathUtils.degToRad(S.yaw);
}

async function rig() {
  const manual = document.querySelector('input[name="mode"]:checked').value === "manual";
  $("busy").hidden = false;
  const body = { id: S.id, markers: manual && MK.count() ? MK.get() : null, lod: $("lod").value, symmetry: $("sym").checked };
  const r = await (await fetch("/rig", { method: "POST", body: JSON.stringify(body) })).json();
  $("busy").hidden = true; status("");
  if (!r.ok) return status(/KeyError/.test(r.log) ? "Could not find the limbs: the model must stand upright and face the green arrow (go back to Orient)." : "rig failed: " + r.log.slice(-300));
  show(await load(r.glb, "r.glb")); skeleton($("bones").checked); wave(false); $("wave").checked = false;
  $("dl").href = r.fbx; $("qa").textContent = JSON.stringify(r.qa, null, 1); go("preview");
}

$("file").onchange = e => e.target.files[0] && upload(e.target.files[0]);
const drop = $("drop");
["dragover", "dragenter"].forEach(t => drop.addEventListener(t, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach(t => drop.addEventListener(t, () => drop.classList.remove("over")));
drop.addEventListener("drop", e => { e.preventDefault(); e.dataTransfer.files[0] && upload(e.dataTransfer.files[0]); });
$("rotL").onclick = () => turn(90); $("rotR").onclick = () => turn(-90); $("flip").onclick = () => turn(0, true);
$("yaw").onchange = e => { S.yaw = 0; turn(+e.target.value); };
$("free").onchange = e => setView(e.target.checked);
$("done").onclick = async () => {
  await fetch("/done", { method: "POST", body: JSON.stringify({ id: S.id }) }); status("Saved. You can close this tab.");
  window.close();
};
$("reset").onclick = () => { $("yaw").value = 0; S.yaw = 0; S.flip = false; pivot.rotation.set(0, 0, 0); };
$("sym").onchange = e => MK.config.setSymmetry(e.target.checked);
$("bones").onchange = e => skeleton(e.target.checked); $("wave").onchange = e => wave(e.target.checked);
$("next").onclick = async () => {
  if (S.busy) return;
  if (S.step === "orient") { if (S.yaw || S.flip) await prep(); go("markers"); MK.buildLegend($("legend"), S.info.h * 0.012); MK.clear(); }
  else if (S.step === "markers") await rig();
};
$("back").onclick = async () => {
  if (S.step === "preview") { MK.clear(); await prep(); go("markers"); MK.buildLegend($("legend"), S.info.h * 0.012); }
  else go(ORDER[ORDER.indexOf(S.step) - 1]);
};
go("upload");
fetch("/startup").then(r => r.json()).then(async j => {                  // opened with --model: skip the upload
  if (j.name) await upload(new File([await (await fetch("/startup/file")).arrayBuffer()], j.name));
}).catch(() => {});
