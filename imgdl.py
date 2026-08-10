# -*- coding: utf-8 -*-
"""图片下载: 从 details 提取 images URL, 下载到 imgs/ (每轮 100 张)"""

import urllib.request, json, os, sys, ssl, hashlib

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
out = []


def log(s):
    print(s, flush=True)
    out.append(str(s))


# 收集所有 details 的 images URL
all_imgs = []
for f in os.listdir("."):
    if f.startswith("details_") and f.endswith(".jsonl"):
        try:
            with open(f) as fh:
                for ln in fh:
                    if not ln.strip():
                        continue
                    try:
                        d = json.loads(ln)
                    except Exception:
                        continue
                    det = d.get("detail")
                    if isinstance(det, dict):
                        all_imgs.extend(det.get("images") or [])
        except Exception:
            pass
all_imgs = list(dict.fromkeys(all_imgs))
log("total images: %d" % len(all_imgs))

# 已下载记录
done = set()
try:
    with open("img_done.txt") as f:
        done = set(f.read().splitlines())
except Exception:
    pass

os.makedirs("imgs", exist_ok=True)
ctx = ssl.create_default_context()
n = 0
for u in all_imgs:
    if n >= 100:
        break
    if u in done:
        continue
    fn = u.split("images.moegoat.com/")[-1]
    out_path = os.path.join("imgs", fn)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
        done.add(u)
        continue
    try:
        r = urllib.request.Request(
            u, headers={"User-Agent": UA, "Referer": "https://loiship.com/"}
        )
        resp = urllib.request.urlopen(r, timeout=20, context=ctx)
        data = resp.read()
        if data[:3] in (b"\xff\xd8\xff", b"\x89PNG") or data[:2] == b"GIF":
            with open(out_path, "wb") as f:
                f.write(data)
            done.add(u)
            n += 1
            log("OK %s (%d)" % (fn[:30], len(data)))
        else:
            log("BAD %s %s" % (fn[:30], data[:4].hex()))
    except Exception as e:
        log("EXC %s %s" % (fn[:30], type(e).__name__))
    if n % 20 == 0:
        time.sleep(0.5)

with open("img_done.txt", "w") as f:
    f.write("\n".join(done))
log("downloaded %d this round" % n)
with open("imglog.txt", "w") as f:
    f.write("\n".join(out))
