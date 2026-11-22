"""Helpers for the Fab Publisher Portal form, for browser-harness (user's real Chrome). Load them at the top of the harness code:
  tools/general/bh.sh <<'PY'
  exec(open("C:/Users/epers/Desktop/retopologizer/tools/05-delivery/fab_form.py", encoding="utf-8").read())
  fab_inputs_dump()          # index, type, placeholder, value, checked, label of every input: read it before filling anything
  fab_title("..."); fab_description([...paragraphs]); fab_tags([...]); fab_price("Personal", "1.99"); fab_pick_category(...)
  fab_num(18, 51); fab_radio(7); fab_state()                 # technical details by DOM index; print the state back
  fab_click("Convert files")                                 # button by text; NEVER the submit button (see below)
  fab_submit()                                               # only when the user said "submit"; refuses otherwise
PY
Lessons (alligator listing, 2026-11): 1) a click by remembered coordinates after scrollIntoView landed on "Submit for review" (sticky header)
and submitted the listing before the AI question was answered. So: click ELEMENTS by text/rect (fab_click) and check the rect is inside the
viewport below the header (y > 90); take a screenshot before any click near the top bar; read the form back before submitting.
2) Indexes of `input` change when a format is added or a section collapses: dump again before using `fab_num`/`fab_radio`.
3) JS inside Python strings: a '\n' becomes a real newline and breaks the JS; use String.fromCharCode(10)."""
INPUTS = "[...document.querySelectorAll('input:not([type=file])')]"
HEADER_PX = 90


def _center(expr):
    return js("(()=>{const e=%s; if(!e) return null; e.scrollIntoView({block:'center'}); const b=e.getBoundingClientRect(); return [b.x+b.width/2,b.y+b.height/2]})()" % expr)


def fab_click(text, exact=True, allow_submit=False):
    """Click the visible button/option whose text matches; refuses 'Submit for review' unless allow_submit."""
    if "submit" in text.lower() and not allow_submit: raise RuntimeError("submit is the user's decision: use fab_submit()")
    cond = "t==%r" % text if exact else "t.includes(%r)" % text
    c = _center("[...document.querySelectorAll('button,[role=option],[role=radio],label,li')].find(e=>{const t=(e.innerText||'').trim(); const b=e.getBoundingClientRect(); return (%s)&&b.width>0})" % cond)
    if not c or c[1] < HEADER_PX: raise RuntimeError("%r not found or under the header (y=%s)" % (text, c and c[1]))
    click_at_xy(c[0], c[1]); wait(0.6)


def fab_inputs_dump():
    for r in js("""[...document.querySelectorAll('input:not([type=file])')].map((i,n)=>{let p=i.parentElement,t='';for(let k=0;k<5&&p;k++){t=(p.innerText||'').trim().split(String.fromCharCode(10))[0];if(t&&t.length<60&&!['Yes','No'].includes(t))break;p=p.parentElement}return [n,i.type,i.placeholder,i.value,i.checked,t]}).filter(x=>x[1]!='hidden'&&x[5])"""): print(r)


def fab_num(i, v):
    c = _center("%s[%d]" % (INPUTS, i)); click_at_xy(c[0], c[1])
    js("(()=>{const e=%s[%d]; e.focus(); e.select()})()" % (INPUTS, i)); press_key("Backspace"); type_text(str(v)); wait(0.3)


def fab_radio(i):
    c = _center("%s[%d]" % (INPUTS, i)); click_at_xy(c[0], c[1]); wait(0.3)


def fab_state(lo=0, hi=999):
    return js("JSON.stringify(%s.map((i,n)=>[n,i.type=='radio'||i.type=='checkbox'?i.checked:i.value]).filter(x=>x[0]>=%d&&x[0]<=%d))" % (INPUTS, lo, hi))


def fab_title(t):
    c = _center("document.querySelector('input[placeholder=\"Enter a title\"]')"); click_at_xy(c[0], c[1]); type_text(t); wait(0.5)


def fab_description(paragraphs):
    c = _center("document.querySelector('[contenteditable=true]')"); click_at_xy(c[0], c[1] + 20)
    for k, p in enumerate(paragraphs):
        type_text(p)
        if k < len(paragraphs) - 1: press_key("Enter")


def fab_tags(tags):
    """One tag at a time; only catalogue tags exist. Returns {tag: 'ok'|'no'} ('no' tags are cleared from the box)."""
    res = {}
    for t in tags:
        js("document.querySelector('input[placeholder=\"Search a tag\"]').focus()"); type_text(t); wait(1.4)
        c = js("(()=>{const e=[...document.querySelectorAll('button,[role=option],li,div,span')].filter(e=>e.childElementCount==0&&(e.innerText||'').trim().toLowerCase()==%r).find(x=>{const b=x.getBoundingClientRect();return b.width>0&&b.y>100}); if(!e) return null; const b=e.getBoundingClientRect(); return [b.x+b.width/2,b.y+b.height/2]})()" % t.lower())
        if c: click_at_xy(c[0], c[1]); res[t] = "ok"; wait(0.8)
        else:
            js("(()=>{const i=document.querySelector('input[placeholder=\"Search a tag\"]'); i.focus(); i.select()})()"); press_key("Backspace"); res[t] = "no"
    return res


def fab_price(which, usd):
    """which = 'Personal' | 'Professional'. Comboboxes: click the field, then the option text '1.99 (USD)' (typing does nothing)."""
    c = _center("[...document.querySelectorAll('*')].find(e=>e.childElementCount==0&&(e.innerText||'').trim()=='Select %s price')" % which)
    click_at_xy(c[0], c[1]); wait(1); fab_click("%s (USD)" % usd)


def fab_submit():
    """Submit for review. Call only after the user said so and fab_state()/screenshots confirm every field."""
    c = _center("[...document.querySelectorAll('button')].find(b=>(b.innerText||'').trim()=='Submit for review')")
    click_at_xy(c[0], c[1]); wait(2); print(js("document.body.innerText.slice(0,200)"))
