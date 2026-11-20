"""Fiber Card Gen state: a Python port of src/store/studio.store.ts of epersonf/fiber-card-gen (commit eccffc9). The keys are the app's, so a preset
JSON can be pasted into the app ("copy/paste state") and back. BLONDE is the cuca's hair: only what differs from the defaults.
  load()                  the defaults       load("preset.json")  a preset over the defaults       load(None, hair_amount_max=60)  overrides"""
import json
from pathlib import Path

DESIGN_SHEET = 2048
DEFAULTS = dict(
    baseSize=DESIGN_SHEET, percentage=1.0, cardsPerSheet=12, background_alpha=0,
    strand_points_count=25, gradient_color_enabled=False, hair_color=[0.40, 0.20, 0.20, 1],
    hair_gradient_stops=[{"pos": 0, "color": "#3b2e1a"}, {"pos": 1, "color": "#d2b48c"}], glossiness=0.11, sheen=0.30,
    root_thickness=0.02, tip_thickness=0.0, fixed_length_size=True, combined_length=20, minimum_length=1, maximum_length=14,
    spread_amount_offset=22.4, clump_root=0, clump_tip=0, hairline_shape=0.0,
    enable_frizz_hair=False, frizz_scale=1.34, frizz_curve_enabled=False, frizz_curve_points=[{"x": 0, "y": 0}, {"x": 0.45, "y": 0.7}, {"x": 1, "y": 1}],
    enable_hair_curl=False, curl_count=5, curl_amount=0.0, curl_scale=0.0, curl_shape=0.0, messiness_scale=1.0,
    spawn_enabled=True, spawn_radius_ratio_x=0.12, spawn_radius_ratio_y=0.04, spawn_tilt_deg=-6,
    hair_amount_max=80, hair_amount_min_percent=0.06, hair_amount_curve="quad")

BLONDE = dict(
    gradient_color_enabled=True, hair_gradient_stops=[{"pos": 0, "color": "#8c6a32"}, {"pos": 0.45, "color": "#d9b96c"}, {"pos": 1, "color": "#f6e7b0"}],
    root_thickness=0.026, tip_thickness=0.010, spawn_radius_ratio_x=0.22, spawn_radius_ratio_y=0.05,
    clump_root=300, clump_tip=1500, hairline_shape=0.7, enable_hair_curl=True, curl_count=1.2, curl_amount=12.0, curl_scale=1.4,
    enable_frizz_hair=True, frizz_scale=1.6, hair_amount_max=130, hair_amount_min_percent=0.10)


def load(path=None, **over):
    s = dict(DEFAULTS)
    if path:
        s.update({k: v for k, v in json.loads(Path(path).read_text()).items() if k in DEFAULTS})
    s.update(over)
    return s
