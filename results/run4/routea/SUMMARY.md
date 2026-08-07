# Route (a) test evidence — buyer-side Civitai fetch (2026-08-07)

Every case ran against the shipped `aiofm_setup.sh` bytes. Cases i/ii/iv/vi-a/v
ran the FULL script (a skeleton `COMFYUI_DIR` with real `comfyui_version.py` +
`nodes.py` so the earlier stages pass, empty `models/`); each died in the
"Base checkpoint preflight (Civitai)" stage — i.e. before any model download.
Cases vi-b/P/P2 ran `fetch_lustify` extracted VERBATIM (sed line-range, stored
as `scratch civitest/extracted_lustify.sh`, lines 386–507 of the script at the
time of the run) with display helpers stubbed, driving a real download of a
24,655-byte public Civitai file (EasyNegative, version 9208) so the
download/verify/place path runs for real without 6.9 GB per case. The full
6.9 GB happy path is exercised once, in the fresh-install gate.

| case | scenario | expected | observed | evidence |
|---|---|---|---|---|
| i | no Civitai key | fatal, names cause + how-to-fix | exit 1, "✗ no Civitai API key found…" + 5-step key instructions | neg_i_no_token.out |
| ii | bad key | fatal, names 401 + new-key steps | exit 1, "✗ Civitai rejected your API key (HTTP 401)" | neg_ii_bad_token.out |
| iv | version id gone | fatal, names LUSTIFY! GGWP (V7) + support action | exit 1, "✗ LUSTIFY! GGWP (V7) did not resolve on Civitai (HTTP 404…" | neg_iv_version_gone.out |
| vi-a | upstream file swapped under same version id | fatal, both hashes shown, refuse install | exit 1, "…NO LONGER the one this pack was built and verified against", expected+actual SHA printed | neg_via_upstream_swap.out |
| vi-b | corrupted resume (garbage partial + real tail) | fatal post-download SHA256, bad file deleted | exit 1, "the downloaded file is NOT the LUSTIFY! GGWP (V7) release…", checkpoints dir empty after | neg_vib_sha_mismatch.out |
| v | disk too small | fatal BEFORE download, need vs free named | exit 1, "✗ not enough free disk… need 93133.3 GB / free 203.1 GB" (need inflated via `LUSTIFY_BYTES` override; real tmpfs mounts are blocked in this container) | neg_v_disk_full.out |
| P | clean download | exit 0, SHA verified, file placed | exit 0, 24,655 bytes placed, "installed from Civitai and SHA256-verified" | pos_tiny_download.out |
| P2 | re-run with file present | exit 0, skip | exit 0, "already installed … nothing to fetch" | pos_idempotent.out |

None of these paths uses `warn` — every failure is `die` (exit 1), satisfying
the no-swallowed-failures rule. `.exitcode` files sit beside each `.out`.

Also verified this session, before implementation (probe transcript in the
session log): download endpoint answers 401 with no/bad key and 307 to the
R2 CDN with a valid one, via BOTH `Authorization: Bearer` and `?token=`; a
ranged one-step `curl -L` with the Bearer header reaches the CDN and returns
206, so the single-step fetch with resume is sound. Metadata endpoint needs no
key (200), bogus version answers 404.
