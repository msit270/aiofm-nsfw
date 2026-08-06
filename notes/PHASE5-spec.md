# Phase 5 — the landing steps, specified so they are mechanical

**Do not execute any of this while Phase 1/3 arms are in flight.** The graph is
frozen until every measuring agent has reported. That rule exists because last
run a mid-flight edit (`74c0f11`) invalidated a conclusion about the shipping
artifact.

---

## 5a. Apply denoise 0.35 on `#114`

Decided by the owner off the R1 sheet, picked independently and blind to which
arm was which. Steps stay at 8.

**Verified read-only against the current file (`a811b5d6…`)** — `#114
FaceDetailer`, `widgets_values` has **29** entries:

```
[ 5] 8      steps        (2e4e8e9, already applied)
[ 9] 0.8    denoise      <-- CHANGE THIS TO 0.35
[15] 1.5    bbox_crop_factor  (74c0f11, already applied)
```

**The edit, with the formatting rule that has already been broken once.** Writing
this file minified produced a 10,939-line diff on the first attempt at the steps
change; it must be written back with `indent=2, ensure_ascii=False` and the
trailing newline preserved:

```python
import json
p = 'OFMTech-NSFW/OFMTech_NSFW.json'
raw = open(p, encoding='utf-8').read()
d = json.loads(raw)

def rec(o, out):
    if isinstance(o, dict):
        if o.get("id") == 114 and "widgets_values" in o: out.append(o)
        for v in o.values(): rec(v, out)
    elif isinstance(o, list):
        for v in o: rec(v, out)

found = []; rec(d, found)
assert len(found) == 1, found
wv = found[0]["widgets_values"]
assert len(wv) == 29 and wv[5] == 8 and wv[9] == 0.8 and wv[15] == 1.5, wv
wv[9] = 0.35

out = json.dumps(d, indent=2, ensure_ascii=False)
if raw.endswith('\n') and not out.endswith('\n'): out += '\n'
open(p, 'w', encoding='utf-8').write(out)
```

Then confirm the diff touches **one** line, and re-run
`python3 tools/preflight/integrity.py OFMTech-NSFW/OFMTech_NSFW.json`.

One commit, on its own, reasoning in the message.

---

## 5b. The cold timing number — **and why the existing one is not usable**

The owner: *"Z0 ran with 0 cached nodes and Z1/Z2/Z3 each had 57, so I do not
currently have a defensible number and I am not putting one in front of a buyer
until I do."*

He is right, and there is a **second** defect in the existing pair that is worth
naming because it is not the cache one:

| arm | config | cold | warm |
|---|---|---|---|
| `Z0` | cf 1.5, steps 8, denoise **0.80** — *the shipping config* | 270.5 s (0 cached) | 150.5 / 149.9 s (57) |
| `Z2` | cf 1.5, steps 8, denoise **0.35** — *the proposed config* | 262.6 s | 145.6 s (57) |

`Z0` **is the tap arm**. It was carrying six `SaveImage` nodes writing
full-resolution PNGs, which is exactly why R1 withdrew the `−118 s` crop-factor
figure that leaned on it. So `270.5 − 262.6 = −7.9 s` is **not** the denoise
lever; it is the denoise lever plus six PNG writes, pointing the wrong way.

**What to run:** a clean `Z0` (no taps, shipping config, denoise 0.80) and a clean
`Z2` (denoise 0.35), **both cold**, `/free` before each, both confirmed
`execution_cached: []`, differing by exactly one input under a graph diff
(`620:114.denoise`). Report the delta and, given that ~120–200 s of a cold render
here is model loading, say plainly whether it clears that variance.

**Prior expectation, so it is on record before the measurement:** matched-cache
warm says denoise costs **0.4 s** (145.2 vs 145.6 s). So the honest expectation is
that the cold delta is **indistinguishable from zero** and that the correct public
statement is *"denoise 0.35 is free"*. If the cold pair shows a large delta, that
is a reason to suspect the measurement, not to believe the number — three cold
deltas have already been withdrawn in this project for exactly that.

---

## 5c. Re-cut the pack

- `tools/build_pack.sh`, then fix `PACK_TOP` so archive name and unpack directory
  match.
- Record the new sha256 and byte count; verify the workflow **as extracted from
  the archive**, not off the tree.
- Verify by piping the live gist into an empty ComfyUI: no token, bad archive,
  happy path.
- File-count check: `tar -tzf | wc -l` counts **directories too**. The current
  artifact is 196 entries = **170 files + 26 dirs**. Quote files, not entries.
- Update the `hf upload` command in `HANDOFF.md` with the new hash and a commit
  message naming the change. **Upload nothing.**
