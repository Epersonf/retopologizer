# Publishing on Fab (Publisher Portal) with browser-harness

Done end to end for the sword (`docs/08-cases/sword.md`) in the user's own logged-in Chrome. Prepare the files first:
`render_thumbnail`/`listing_shots` (images), `description.md`, `fab_package.py` (zip) - see `delivery.md`, "Store listing".
Not every field can be scripted blind: **look at a screenshot after each group of fields**.

## Setup (once)
- Use **browser-harness** (CDP on the user's real Chrome), not the Claude-in-Chrome extension: the user chose it and corrected the agent
  who started with the extension. Repo: `C:\Users\epers\Documents\Repositories\OpenSource\browser-harness`.
- The agent needs its own venv there (`python -m venv .venv`, install the package and its deps; `cdp_use` is one of them). Run through a
  wrapper that sets the runtime dirs, reads the code from stdin and prints the result:
  ```
  cd <browser-harness> && export BH_HOME="$PWD/.browser-harness-dev" BH_RUNTIME_DIR="$BH_HOME/runtime" BH_TMP_DIR="$BH_HOME/tmp"
  exec ./.venv/Scripts/python -m browser_harness.run "$@"        # usage: wrapper <<'PY' ... PY
  ```
- **Ask the user to enable debugging**: Chrome -> `chrome://inspect/#remote-debugging` -> tick "Allow remote debugging", then click
  Allow on the prompt. Without it the daemon cannot attach.
- Helpers in the code: `js(expr)`, `click_at_xy(x, y)`, `type_text(s)`, `press_key(k)`, `upload_file(css_selector, path)`, `capture_screenshot(path, max_dim=900)`,
  `wait(s)`, `page_info()`. Writing a Python regex with `\n` inside a heredoc broke the JS: avoid it.
- Cheap screenshots: `max_dim=900`, then multiply the coordinates by ~1.707 (viewport 1536x730) to click. Prefer reading the DOM
  (`js(...)` with `getBoundingClientRect`) over guessing coordinates: after a scroll, a click by remembered coordinates once landed on the
  sidebar and navigated away.

## The form (`/portal/listings/<id>/edit`, a draft is created from "Create listing")
React ids (`:r5:`) change on every render: select by **placeholder** or by text.
| field | how |
|---|---|
| title | input placeholder "Enter a title" |
| description | rich-text editor: click inside, `type_text` the paragraphs (`description.md`) |
| category / type | 3D / "Weapons & Combat" |
| licence | Standard |
| prices | **comboboxes**: typing does nothing; click the field and click the option "1.99 (USD)" in the list. Personal and Professional are two fields; the UEFN one is "reference only". The card in the sidebar shows the account's currency ("From R$..."), not USD |
| tags | input "Search a tag": type ONE tag, wait ~1.3 s, click the chip whose text equals it, repeat. Typing without picking accumulates text in the box (clear it: focus, `select()`, Backspace). Only catalogue tags exist: `low poly`, `game ready`, `rpg` were refused, 10 of 13 stayed |
| thumbnail | `upload_file("input[type=file]", thumbnail.jpg)`; 1920x1080 min, <= 3 MB |
| media gallery | click Upload -> Images; that adds `input[type=file][multiple]`; `upload_file` each image, then Confirm in the modal |
| forum post, mature | defaults (No / not mature) kept |
| generative AI | a radio question. The user answered **No**; the shape came from an AI reference, so tell the user and let them decide |

## Product files
1. "Add new format" -> the modal lists formats (scroll it): choose **FBX** -> Next.
2. The upload input is `input[type=file][multiple]` with an empty `accept`: `upload_file` the FBX zip (`fab_package.py`; one format per zip) -> Confirm.
3. Fab creates a second group "GLTF, GLB, USDZ": open it, pick FBX as the source, then press **Convert files** below the 3D preview
   (the "Confirm selection" button stayed disabled and was not needed). The converted `.zip`, `.glb`, `.usdz` appear listed. No second upload.
4. **Technical details** of the FBX (auto-filled: total triangles, quads, vertices). Fill the rest, honestly:
   pack of multiple assets No, assets 1, LODs No, collision No, bounding box X/Y/Z **in cm** (read them from the GLB: Y-up, 33.3 x 119 x 6),
   texture resolution 2048, materials 1, textures 5, normal map **OpenGL (Y+)**, UV channels 1, clean UV No, overlapping UV **Yes** if the UV is
   mirrored, custom shaders / UDIM / vertex colours / scanned No, animation fields No. The number inputs share the placeholder "number":
   index them in DOM order, set a value with focus + `select()` + Backspace + `type_text`, then **print all values back** (one wrong index
   overwrote "2048" with "20486").
5. The radios are in DOM order too (`input[type=radio]`, Yes then No per question); print their `checked` bits to verify.

## Submit
"Submit for review" (top right) -> a modal asks Automatic or Manual publication (default automatic) -> Confirm -> status **Pending approval**
(review takes 1-2 business days; "Cancel submission" undoes it). Submitting is the user's go-ahead: they asked to publish. Report the result and what
was left default or refused (tags, AI answer).

## Mistakes to avoid (all happened)
- Fab asks for one format at a time and says a zip must contain that format's files: use one zip per format (a mixed zip was not tried); upload only FBX.
- The scepter's Fab upload failed once (cause not recorded) and was left to the user; for the sword `upload_file` on the `input[type=file]` worked every time.
- Do not retry a failing selector in a loop: take a screenshot and read the page text.

## Animated model (alligator, 2026-11) and what changed
- The user may already have a draft open at `/portal/listings/<id>/edit` (check `page_info()` before creating one).
- **Ask the user first**: price (Personal/Professional, USD), the generative-AI answer, and the format list. Do not stop in the middle of the form.
- **Category** is a tree: click the chevron of "Characters & Creatures", then "Animals", then "Other" (there is no reptile entry).
- **Tags**: `fab_form.fab_tags([...])`; accepted 10 of 12 (`hand painted` and `game ready` are not in the catalogue, same as before).
- **Gallery**: Upload -> Images, `upload_file("input[type=file][multiple]", jpg)` for each image, Confirm; the thumbnail input is the single (non-multiple) one.
- **Technical details of an animated FBX**: Fab detects triangles, quads, vertices, animated, rigged and the number of animation tracks (it read 6 clips).
  Still to fill: assets 1, LODs No, collision No, bounding box X/Y/Z in cm **Y-up** (Blender X/Z/Y), custom shaders No, UV channels 1, normal orientation OpenGL,
  clean UV and overlapping UV (about 20 px overlap = clean No, overlapping Yes), UDIM/scanned/vertex colours No, solid/scale/IK No, baked animation Yes, characters 1.
  Print `fab_state()` and look at the screenshot: indexes shift.
- **GLTF/GLB/USDZ**: open the second format, choose FBX as the source, **Confirm selection** (it worked this time), wait for the 3D preview (~15 s) so "Convert files"
  enables, then convert (~25 s: zip, glb, usdz appear).
- **Accident**: a click by remembered coordinates after `scrollIntoView` hit the sticky "Submit for review" and the listing went to "Pending publication" before the
  AI question was read back. `fab_form.fab_click` refuses submit and clicks elements, not coordinates; the only way to submit is `fab_submit()`.
  Cancel submission is possible while pending; read the form back (`fab_state`, screenshots) before the user's go-ahead.
- Run harness code through `tools/general/bh.sh` (Git Bash paths and PowerShell BOM both broke the plain command). The first call after Chrome restarts asks the
  user to Allow remote debugging.
