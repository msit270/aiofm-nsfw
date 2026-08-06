"""TRACK E probe pack.

Read-only instrumentation. Registers NO nodes and changes NO numerics: every
wrapper below calls the original function and only *inspects* the tensors that
pass through it, appending one JSON line per event to $TRACKE_LOG.

Why these taps, specifically:
  * comfy.sd.VAE.decode        -- the latent handed to the decoder and the image
                                  that comes out. This is the last place a NaN is
                                  still visible.
  * impact.utils.tensor_resize -- ComfyUI-Impact-Pack/modules/impact/utils.py:129
                                  goes through tensor2pil ->
                                  np.clip(255.*x,0,255).astype(np.uint8), which
                                  turns NaN into an exact 0 and erases the
                                  evidence. enhance_detail() calls it on the
                                  decoded crop before pasting it back.
  * comfy.samplers.KSAMPLER.sample -- the sampler's own output latent, so the
                                  sampler and the VAE can be told apart.
  * comfy.sd.CLIP.encode_from_tokens -- the conditioning as the graph itself
                                  produces it, in situ.
"""
import os, json, time, threading

LOG = os.environ.get("TRACKE_LOG", "/workspace/trackE/logs/probe.jsonl")
_lock = threading.Lock()


def _emit(rec):
    rec["t"] = round(time.time(), 3)
    try:
        with _lock:
            with open(LOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _stat(t, name):
    import torch
    if t is None:
        return {name: None}
    if not isinstance(t, torch.Tensor):
        return {name: str(type(t))}
    tf = t.detach().float()
    nan = int(torch.isnan(tf).sum().item())
    inf = int(torch.isinf(tf).sum().item())
    good = tf[torch.isfinite(tf)]
    d = {name + "_shape": list(t.shape), name + "_dtype": str(t.dtype),
         name + "_nan": nan, name + "_inf": inf, name + "_n": int(tf.numel())}
    if good.numel():
        d[name + "_min"] = float(good.min().item())
        d[name + "_max"] = float(good.max().item())
        d[name + "_absmax"] = float(good.abs().max().item())
        d[name + "_mean"] = float(good.mean().item())
        d[name + "_exact0"] = int((good == 0).sum().item())
    return d


def _install():
    import comfy.sd
    import comfy.samplers

    # ---- VAE.decode -------------------------------------------------------
    _dec = comfy.sd.VAE.decode

    def decode(self, samples_in, *a, **k):
        rec = {"ev": "vae.decode"}
        rec.update(_stat(samples_in, "lat"))
        out = _dec(self, samples_in, *a, **k)
        rec.update(_stat(out, "img"))
        _emit(rec)
        return out
    comfy.sd.VAE.decode = decode

    # ---- KSAMPLER.sample --------------------------------------------------
    _ks = comfy.samplers.KSAMPLER.sample

    def ks_sample(self, model_wrap, sigmas, extra_args, callback, noise, latent_image=None, denoise_mask=None, disable_pbar=False):
        rec = {"ev": "ksampler.sample", "sampler": getattr(self, "sampler_function", None).__name__
               if getattr(self, "sampler_function", None) else None,
               "n_sigmas": int(sigmas.shape[-1]),
               "sigma0": float(sigmas[0].item()), "sigmaN": float(sigmas[-1].item())}
        try:
            conds = extra_args.get("cond", None) or []
            shapes = []
            for c in conds:
                cc = c.get("model_conds", {}).get("c_crossattn", None)
                if cc is not None:
                    shapes.append(list(cc.cond.shape))
            rec["cond_shapes"] = shapes
        except Exception as e:
            rec["cond_err"] = str(e)
        rec.update(_stat(latent_image, "lat_in"))
        out = _ks(self, model_wrap, sigmas, extra_args, callback, noise,
                  latent_image=latent_image, denoise_mask=denoise_mask, disable_pbar=disable_pbar)
        rec.update(_stat(out, "lat_out"))
        _emit(rec)
        return out
    comfy.samplers.KSAMPLER.sample = ks_sample

    # ---- CLIP.encode_from_tokens -----------------------------------------
    _enc = comfy.sd.CLIP.encode_from_tokens

    def enc(self, tokens, return_pooled=False, return_dict=False):
        out = _enc(self, tokens, return_pooled=return_pooled, return_dict=return_dict)
        rec = {"ev": "clip.encode"}
        try:
            k = list(tokens.keys())[0]
            rec["ntok"] = len(tokens[k][0])
            rec["tok_key"] = k
        except Exception:
            pass
        c = out
        if isinstance(out, dict):
            c = out.get("cond", None)
        elif isinstance(out, tuple):
            c = out[0]
        rec.update(_stat(c, "cond"))
        _emit(rec)
        return out
    comfy.sd.CLIP.encode_from_tokens = enc

    # ---- impact.utils.tensor_resize (the uint8 launder) -------------------
    try:
        import impact.utils as iu
        _tr = iu.tensor_resize

        def tensor_resize(image, w, h):
            rec = {"ev": "impact.tensor_resize", "w": w, "h": h}
            rec.update(_stat(image, "in"))
            out = _tr(image, w, h)
            rec.update(_stat(out, "out"))
            _emit(rec)
            return out
        iu.tensor_resize = tensor_resize
        import impact.core as ic
        ic.utils.tensor_resize = tensor_resize
        _emit({"ev": "install", "impact": True})
    except Exception as e:
        _emit({"ev": "install", "impact": False, "err": repr(e)})


try:
    _install()
    _emit({"ev": "install", "core": True, "log": LOG})
except Exception as e:  # never break the server
    _emit({"ev": "install", "core": False, "err": repr(e)})

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
