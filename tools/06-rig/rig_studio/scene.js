// three.js stage: orbit view, ground + FRONT arrow (+Z is where the model must face), model loading, skeleton overlay.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { FBXLoader } from "three/addons/loaders/FBXLoader.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";

export const canvas = document.getElementById("view");
export const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
export const scene = new THREE.Scene();
export const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
export const ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 100);
export const controls = new OrbitControls(camera, canvas);
export const view = { free: false, side: 0 };                                // ortho by default, like Mixamo; free = 3D orbit
export const active = () => (view.free ? camera : ortho);
export const pivot = new THREE.Group(); scene.add(pivot);               // the model turns here while orienting
scene.add(new THREE.HemisphereLight(0xffffff, 0x8890a0, 1.3));            // soft fill, never dark
const head = new THREE.DirectionalLight(0xffffff, 1.6); scene.add(head, head.target);      // follows the view
const ground = new THREE.Group(); scene.add(ground);
let model = null, helper = null;

export const hooks = { frame: [] };
function resize() {
  const r = canvas.parentElement.getBoundingClientRect();
  renderer.setSize(r.width, r.height, false); camera.aspect = r.width / r.height; camera.updateProjectionMatrix(); fitOrtho();
}
let fit = { c: new THREE.Vector3(), h: 1 };
function fitOrtho() {
  const a = canvas.clientWidth / Math.max(1, canvas.clientHeight), hh = fit.h * 0.62;
  Object.assign(ortho, { left: -hh * a, right: hh * a, top: hh, bottom: -hh }); ortho.updateProjectionMatrix();
}
export function setView(free, side = view.side) {                         // side 0 front, 1 left of model, 2 back, 3 right
  view.free = free; view.side = side; controls.object = active(); controls.enableRotate = free;
  const a = side * Math.PI / 2, d = fit.h * 3;
  if (!free) { ortho.position.set(fit.c.x + Math.sin(a) * d, fit.c.y, fit.c.z + Math.cos(a) * d); ortho.lookAt(fit.c); controls.target.copy(fit.c); }
  controls.update();
}
addEventListener("resize", resize); resize();
renderer.setAnimationLoop(() => { hooks.frame.forEach(f => f()); head.position.copy(active().position); head.target.position.copy(controls.target); controls.update(); renderer.render(scene, active()); });

export function load(url, name = "") {
  const ext = (name || url.split("?")[0]).split(".").pop().toLowerCase();
  return new Promise((res, rej) => {
    const done = o => res(o.scene || o);
    if (ext === "fbx") new FBXLoader().load(url, done, null, rej);
    else if (ext === "obj") new OBJLoader().load(url, done, null, rej);
    else new GLTFLoader().load(url, done, null, rej);
  });
}

export function show(obj) {
  if (model) pivot.remove(model);
  if (helper) { scene.remove(helper); helper = null; }
  pivot.rotation.set(0, 0, 0); model = obj; pivot.add(obj); obj.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(obj), size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
  controls.target.copy(c); camera.position.set(c.x, c.y, c.z + size.y * 2.4);
  camera.near = size.y / 100; camera.far = size.y * 50; camera.updateProjectionMatrix();
  fit = { c: c.clone(), h: size.y }; ortho.near = size.y / 100; ortho.far = size.y * 50; fitOrtho(); setView(view.free, view.side);
  ground.clear(); groundAt(box, size.y);
  return { box, h: size.y, center: c };
}

function groundAt(box, h) {                                               // grid + arrow toward +Z (fixed, whatever the model's turn)
  const cx = (box.min.x + box.max.x) / 2, cz = (box.min.z + box.max.z) / 2, y = box.min.y;
  const grid = new THREE.GridHelper(h * 2, 20, 0x2dd4a0, 0x39414d); grid.position.set(cx, y, cz);
  const tip = new THREE.Vector3(cx, y, cz + h * 0.55);
  ground.add(grid, new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), tip, h * 0.35, 0x2dd4a0, h * 0.1, h * 0.07));
}
export const meshes = () => { const m = []; model && model.traverse(o => o.isMesh && m.push(o)); return m; };

export function skeleton(on) {
  if (helper) { scene.remove(helper); helper = null; }
  if (!on || !model) return;
  helper = new THREE.SkeletonHelper(model); helper.material.depthTest = false; helper.renderOrder = 9; scene.add(helper);
}

const FAX = [0, 0, 1];                                                    // finger curl axis in bone space
export function wave(on) {                                                // swings arms and legs to check the weights
  hooks.frame = hooks.frame.filter(f => !f.wave);
  const bones = {}; model && model.traverse(o => o.isBone && (bones[o.name.replace(/^mixamorig:?/, "")] = o));
  const rest = Object.fromEntries(Object.entries(bones).map(([k, b]) => [k, b.quaternion.clone()]));
  if (!on) { Object.entries(rest).forEach(([k, r]) => bones[k].quaternion.copy(r)); return; }
  const swing = { LeftArm: [0, 0, 1], RightArm: [0, 0, -1], LeftUpLeg: [1, 0, 0], RightUpLeg: [-1, 0, 0], LeftForeArm: [0, 1, 0], RightLeg: [1, 0, 0] };
  const q = new THREE.Quaternion(), t0 = performance.now(), fing = Object.keys(bones).filter(k => /Hand(Thumb|Index|Middle|Ring|Pinky)[123]$/.test(k));
  const curl = () => fing.forEach(k => bones[k].quaternion.copy(rest[k]).multiply(
    q.setFromAxisAngle(new THREE.Vector3(...FAX), 0.5 + 0.5 * Math.sin((performance.now() - t0) / 300))));
  const f = () => curl() || Object.entries(swing).forEach(([k, ax]) => bones[k] && bones[k].quaternion.copy(rest[k]).multiply(
    q.setFromAxisAngle(new THREE.Vector3(...ax), 0.7 * Math.sin((performance.now() - t0) / 400))));
  f.wave = true; hooks.frame.push(f);
}
window.studio = { camera, ortho, controls, setView, view };                    // handle for debugging from the console
