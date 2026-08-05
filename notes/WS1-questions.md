# WS1 — questions and judgement calls

Format: question, my best guess, the reasoning, and what I actually did. Every
call was taken in the direction safest for a first-time buyer.

---

**Q-WS1-1. Should the fix delete the passthroughs, or insert identity nodes
inside subgraph 647?**

*Called: delete.* Inserting three core `Reroute` nodes works — I proved it, it
converts and renders, and it is a two-line change. But it keeps the pointless
`619 → 647 → 619` detour and the host-level cycle it creates, and it makes the
shipped product depend on a frontend-only extension node that ComfyUI is
actively migrating away from (`src/utils/migration/migrateReroute.ts`,
`RerouteMigrationToast.vue` both ship in frontend 1.39.19). A buyer who accepts
that migration prompt would be rewriting the inside of a subgraph they were told
not to touch. Deleting leaves 647 as a pure source with zero inputs, which is
what its name claims it is. I kept the Reroute variant as the control.

---

**Q-WS1-2. The brief told me to rewire root consumers straight to whatever fed
647's inputs. That produces a `619 → 619` self-edge. Overrule?**

*Called: yes, overruled.* positive and negative are a self-loop on host 619
laundered through 647 — `#599`/`#606` leave subgraph 2 and come straight back
into `#592`/`#617` in subgraph 2. The correct destination for those wires is
*inside* subgraph 2, not on the root canvas. Main reached the same conclusion
independently and sent it mid-task; I had already derived it and verified every
link id before acting. MODEL is genuinely different — plain fan-out from `#618`
— so that one *was* wired directly at root, as originally suggested.

---

**Q-WS1-3. Is recomputing every subgraph's `linkIds` in scope, or scope creep?**

*Called: in scope, do it.* `linkIds` is authoritative at runtime, not derived
(`SubgraphSlotBase.ts:98` `Object.assign(this, slot)` overwrites the field
initialiser). Five slots on the subgraph I was already editing had corrupt
bookkeeping, three of them omitting the very links the bug is about. Leaving
half-corrected bookkeeping in the file I just fixed would be worse than either
extreme. It is provably inert — the API-graph diff covers it — and it swept the
two unrelated ghost ids (`"3. Hands…"` 1164, `"6. Eyes"` 1414) at zero risk.

---

**Q-WS1-4. `#614 PrimitiveBoolean "ENABLE IMAGE FILTERING?"` ships `true`, so
`#603 INSTARAW_ImageFilter` pauses every single render behind a popup the buyer
must click "Send" on, with a 600 s timeout that then sends *nothing*. Is that
the intended first-run experience?**

*Not mine to decide — flagging, not changing.* It is defensible as a feature
(the buyer picks which base image to detail). It is indefensible as a default if
the buyer does not know it is coming: the render appears to hang at ~0 % GPU
with a popup that starts with its Send button **disabled** until an image is
picked, and if they wait it out the pipeline proceeds with no image. My
guess is this should either default to `false` or ship with an on-canvas note.
I did not change it — it is not my thread and it would alter output.

---

**Q-WS1-5. `extra.frontendVersion` in the workflow is `1.41.20`; the installed
frontend is `1.39.19`. Does the newer editor emit `-10 → -20` links more
readily?**

*Unknown, and I could not test it — only 1.39.19 is installed here.* This
matters beyond the immediate fix: if deleting a bypassed node between a
subgraph's IO nodes reconnects input-to-output in 1.41.x, then **any future edit
of this file in a newer editor can reintroduce the exact same blocker**, and it
will again be invisible to any API-level test. Proposed pod experiment: install
frontend 1.41.20, open the fixed file, add a node between a subgraph input and
output, bypass it, delete it, save, and check whether a `-10 → -20` link
appears. If it does, that is an upstream bug worth reporting and a permanent
hazard worth a release-gate check.

---

**Q-WS1-6. Should the release gate include a graph lint?**

*My recommendation: yes, and it is cheap.* `results/ws1/integrity.py` runs with
no GPU, no ComfyUI and no browser, in well under a second, and it caught all 14
defects in the shipped file — including the three fatal ones — from the JSON
alone. It flags bare `-10 → -20` passthroughs by name. Whoever owns `tools/`
(WS2) should fold it into the harness so the class cannot ship again. It is not
a substitute for the browser run, which is what catches everything else.

---

**Q-WS1-7. Do other shipped artifacts carry the same construct?**

*Unverified.* I scanned only the seven subgraphs inside
`OFMTech-NSFW/OFMTech_NSFW.json`. If any other workflow, template or blueprint
ships with the pack, it should be run through the same check before release.
