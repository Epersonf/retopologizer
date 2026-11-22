# Post mortem (mandatory last stage)

Every delivery ends with a post mortem: putting the model in a game, publishing it on a store (Fab), handing the files to the user.
**The asset is not done until the post mortem is written and the old docs are corrected.** It is stage 10 of the pipeline
and the last line of the definition of done (`README.md`). Without it the next asset repeats the same mistakes (the alligator cost
four rounds on a normal map, two on a rotation axis and one accidental store submission, all of them already knowable).

## When
Right after the last delivery of the asset (game wired, listing submitted, files sent), before saying "done" to the user.
If the user keeps asking for changes, do it at the end of the session; a long session also gets one at each big milestone
(e.g. after the texture, after the game integration) because the context gets compacted and details are lost.

## How (do all of it, in this order)
1. `python tools/general/post_mortem.py <project> --delivery godot,fab` creates `projects/<project>/POST_MORTEM.md` and lists what is owed.
2. **Reread everything again**, do not summarize from memory: the user's messages (corrections are the most valuable data),
   the recordings (`projects/<p>/session/rec_NN`, `docs/00-rules-and-tools/session-recorder.md`), the scripts you wrote and their
   failures, the renders you showed. Ask for each user correction: what rule would have prevented it?
3. Fill the 7 sections of `POST_MORTEM.md` (template below). Numbers, not adjectives.
4. **Tools**: anything done by hand twice, or fixed by trial and error, becomes a tool in `tools/<stage>/` (docstring with usage and WHY,
   at most 150 lines) and a row in `tools/README.md`. Prefer extending a general tool over a new one (user preference), and extend the
   tools of the *other* repo too (e.g. the game's `model_viewer`, not a new viewer).
5. **Docs**: update the old guides that this project proved wrong, incomplete or silent (name them in section 6). Add the case to
   `docs/08-cases/<project>.md` and its row to `docs/README.md`. If a rule is new and non-negotiable, put it in `README.md`.
6. **Memory**: record user preferences and corrections that apply to every project (the agent's memory), not just this one.
7. Run `post_mortem.py` again until it lists nothing owed, then commit the retopologizer repo (only if the user asked to commit; otherwise say it is pending).

## Template (sections of `POST_MORTEM.md`)
1. **What was delivered**: tris/budget, UV, bake, bones, clips, texture sizes, files, where (game, listing id). What was NOT checked.
2. **Timeline and where the time went**: stage, rounds, cause of each long loop.
3. **Mistakes**: symptom, wrong guess, real cause, rule. (The wrong guess matters: it is how you recognise the next one.)
4. **What the user did that the agent did not**: from recordings and corrections. Each becomes a tool or a rule.
5. **Tools**: created, extended, still missing.
6. **Docs updated**, old ones included.
7. **Next time**: the 5 lines to read before the next asset of this kind.

## Good post mortems are specific
- Bad: "rig had issues". Good: "Root bone local Z = armature Y (the animal's length); rotating local Y by 180 yawed the animal; `pose_actions.local_axis` finds it".
- Every mistake has a rule or a tool next to it. If it has neither, the post mortem is incomplete.
- Say what the user would be annoyed by again (slow rounds without images, new tools instead of extending the general one, a diagnosis that
  blames the mesh when it is the normal map) and what you changed so it does not happen.
