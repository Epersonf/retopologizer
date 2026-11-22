// Joint markers like Mixamo's: drag a circle from the legend onto the model, drag it again to fine tune. With symmetry
// on, placing one side drops its mirror image too. Points go to the middle of the limb (entry and exit of the ray).
import * as THREE from "three";
import { canvas, active, scene, controls, meshes } from "./scene.js";

const DEFS = [["Chin", "Chin", 0x22d3ee], ["LeftWrist", "Wrist L", 0xa3e635], ["RightWrist", "Wrist R", 0xa3e635],
  ["LeftElbow", "Elbow L", 0xfacc15], ["RightElbow", "Elbow R", 0xfacc15], ["LeftKnee", "Knee L", 0xfb923c],
  ["RightKnee", "Knee R", 0xfb923c], ["Groin", "Groin", 0xf472b6]];
const PAIR = k => k.startsWith("Left") ? "Right" + k.slice(4) : k.startsWith("Right") ? "Left" + k.slice(5) : null;
const placed = {}, spheres = {}, ray = new THREE.Raycaster();
let cx = 0, symmetry = true, drag = null, legend = null;

export const config = { setCenter: x => { cx = x; }, setSymmetry: s => { symmetry = s; } };
export const get = () => Object.fromEntries(Object.entries(placed).map(([k, v]) => [k, v.toArray()]));
export const count = () => Object.keys(placed).length;

function pick(e) {                                                        // 3D point inside the model under the pointer
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), active());
  const hits = ray.intersectObjects(meshes(), false);
  if (!hits.length) return null;
  return hits.length > 1 ? hits[0].point.clone().add(hits[1].point).multiplyScalar(0.5) : hits[0].point.clone();
}

function put(key, p, size) {
  if (key === "Chin" || key === "Groin") p.x = cx;
  placed[key] = p;
  if (!spheres[key]) {
    const color = DEFS.find(d => d[0] === key)[2];
    spheres[key] = new THREE.Mesh(new THREE.SphereGeometry(size, 16, 12), new THREE.MeshBasicMaterial({ color, depthTest: false }));
    spheres[key].renderOrder = 10; spheres[key].userData.key = key; scene.add(spheres[key]);
  }
  spheres[key].position.copy(p);
  const chip = legend.querySelector('[data-k="' + key + '"]'); if (chip) chip.classList.add("used");
}

function place(key, p, size) {
  put(key, p, size);
  const o = PAIR(key);
  if (symmetry && o && !(drag && drag.free)) put(o, new THREE.Vector3(2 * cx - p.x, p.y, p.z), size);
}

export function buildLegend(el, size) {
  legend = el; el.innerHTML = "";
  DEFS.forEach(([k, label, color]) => {
    const row = document.createElement("div"); row.className = "row";
    row.innerHTML = '<span>' + label + '</span><div class="chip" data-k="' + k + '" style="border-color:#' + color.toString(16).padStart(6, "0") + '">+</div>';
    row.querySelector(".chip").addEventListener("pointerdown", e => {
      if (e.currentTarget.classList.contains("used")) return;
      drag = { key: k, size, fresh: true }; e.currentTarget.setPointerCapture(e.pointerId); controls.enabled = false;
    });
    el.appendChild(row);
  });
}

canvas.addEventListener("pointerdown", e => {                             // grab a placed marker to move it
  if (drag || !count()) return;
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), active());
  const hit = ray.intersectObjects(Object.values(spheres), false)[0];
  if (hit) { drag = { key: hit.object.userData.key, size: hit.object.geometry.parameters.radius }; controls.enabled = false; }
});
addEventListener("pointermove", e => { if (drag) { const p = pick(e); if (p) place(drag.key, p, drag.size); } });
addEventListener("pointerup", () => { drag = null; controls.enabled = true; });

export function clear() {
  Object.keys(placed).forEach(k => { scene.remove(spheres[k]); delete placed[k]; delete spheres[k]; });
  legend && legend.querySelectorAll(".chip").forEach(c => c.classList.remove("used"));
}
export const show = on => Object.values(spheres).forEach(s => { s.visible = on; });
