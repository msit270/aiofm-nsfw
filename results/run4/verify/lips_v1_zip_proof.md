# lips_v1.pt identification — zip-member hash proof (2026-08-07)

The Civitai by-hash endpoint 404s for `lips_v1.pt`'s sha256 because Civitai
indexes the hash of the **uploaded archive**, and model 142240 publishes a
zip. Proof of identity, run this session on this pod:

    $ curl -sL -H "Authorization: Bearer <buyer key>" -o adetailer_lips.zip \
        "https://civitai.com/api/download/models/157700"        # version 157700 of model 142240
    $ python3 - <<'EOF'
    import zipfile, hashlib
    z = zipfile.ZipFile('adetailer_lips.zip')
    for n in z.namelist():
        data = z.read(n)
        print(hashlib.sha256(data).hexdigest(), len(data), n)
    EOF
    ce9fe145352af12c072ee11536a3d0de9425280096c4367e7a08636f57c7fe99 6222638 lips_v1.pt

The pack's file (`models/ultralytics/lips_v1.pt`, LFS oid in
`results/run4/hf_tree_before.json`):

    ce9fe145352af12c072ee11536a3d0de9425280096c4367e7a08636f57c7fe99  6,222,638 bytes

Identical sha256, identical size, identical member filename. The zip itself
is deliberately NOT stored in this repo — committing it would be another
redistribution of the file whose flags (model 142240:
`allowCommercialUse ['Image','RentCivit']`, no `Sell` —
`results/run4/verify/civitai_model_142240.json`) are the problem being
documented.

Model page: https://civitai.com/models/142240 — "ADetailer (After Detailer)
Lips Model", creator mooseh111, type Other, one version (v1.0, id 157700,
file `adetailerAfterDetailer_v10.zip`, sizeKB 5523.77, archive SHA256
DC37038E1FC655F49946…).
