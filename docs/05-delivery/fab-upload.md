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
