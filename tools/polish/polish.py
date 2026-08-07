#!/usr/bin/env python3
"""Run-3 inert polish edits, one per invocation, each with its own asserts.

    polish.py <step> <in.json> <out.json>

steps:
  drop_anatomy   delete bypassed root host 623 + the "7. Anatomy" subgraph def,
                 rewiring 622 out 0 straight to 419.image_b and 505.images
                 (which is exactly what bypass resolved to at conversion time)
  clean_comparer reset root 419's saved rgthree state (stale temp-image URLs)
  strip_cyrillic remove every localized_name whose value contains Cyrillic
  expand_620     ship host 620 expanded so its enter-subgraph button is visible

Output format matches shipping: json.dump(indent=2, ensure_ascii=False), no
trailing newline.
"""
import json, sys, re, collections

CYR = re.compile(r'[Ѐ-ӿ]')


def load(src):
    return json.load(open(src, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)


def save(d, dst):
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


def drop_anatomy(d):
    SG7 = "ccb4441d-dc47-4039-a721-49f8f129d684"
    host = next(n for n in d["nodes"] if n["id"] == 623)
    assert host["type"] == SG7 and host["mode"] == 4, (host["type"], host["mode"])
    # inputs: clip 1439 <-619:2, image 1440 <-622:0, model 1441 <-619:1, vae 1442 <-619:3
    in_links = sorted(i["link"] for i in host["inputs"])
    assert in_links == [1439, 1440, 1441, 1442], in_links
    out_links = sorted(host["outputs"][0]["links"])
    assert out_links == [1437, 1445], out_links

    links = {l[0]: l for l in d["links"]}
    assert links[1440][1] == 622 and links[1440][2] == 0
    # repoint 1437 (-> 419.image_b) and 1445 (-> 505.images) to originate at 622:0
    for lid in (1437, 1445):
        assert links[lid][1] == 623, links[lid]
        links[lid][1] = 622
        links[lid][2] = 0
    # drop the four feeder links and the host
    d["links"] = [l for l in d["links"] if l[0] not in (1439, 1440, 1441, 1442)]
    d["nodes"] = [n for n in d["nodes"] if n["id"] != 623]
    # producers lose the feeder link ids; 622 gains the repointed ones
    for n in d["nodes"]:
        if n["id"] == 619:
            for o in n["outputs"]:
                o["links"] = [x for x in (o.get("links") or []) if x not in (1439, 1441, 1442)]
        if n["id"] == 622:
            o = n["outputs"][0]
            o["links"] = [x for x in (o.get("links") or []) if x != 1440] + [1437, 1445]
    before = len(d["definitions"]["subgraphs"])
    d["definitions"]["subgraphs"] = [s for s in d["definitions"]["subgraphs"] if s["id"] != SG7]
    assert len(d["definitions"]["subgraphs"]) == before - 1 == 6
    assert "ccb4441d" not in json.dumps(d)
    return d


def clean_comparer(d):
    n = next(n for n in d["nodes"] if n["id"] == 419)
    assert n["type"] == "Image Comparer (rgthree)"
    assert "rgthree.compare._temp" in json.dumps(n["widgets_values"])
    n["widgets_values"] = []
    assert "rgthree.compare._temp" not in json.dumps(d), "stale refs remain elsewhere"
    return d


def strip_cyrillic(d):
    removed = 0

    def scrub(obj):
        nonlocal removed
        if isinstance(obj, dict):
            ln = obj.get("localized_name")
            if isinstance(ln, str) and CYR.search(ln):
                del obj["localized_name"]
                removed += 1
            for v in obj.values():
                scrub(v)
        elif isinstance(obj, list):
            for v in obj:
                scrub(v)
    scrub(d)
    assert removed in (120, 126), removed  # 126 full file; 120 after the anatomy def (6 of them) is dropped
    assert not CYR.search(json.dumps(d, ensure_ascii=False)), "Cyrillic remains"
    return d


def expand_620(d):
    n = next(n for n in d["nodes"] if n["id"] == 620)
    assert n["flags"].get("collapsed") is True
    n["flags"]["collapsed"] = False
    return d


STEPS = {"drop_anatomy": drop_anatomy, "clean_comparer": clean_comparer,
         "strip_cyrillic": strip_cyrillic, "expand_620": expand_620}

if __name__ == "__main__":
    step, src, dst = sys.argv[1:4]
    save(STEPS[step](load(src)), dst)
