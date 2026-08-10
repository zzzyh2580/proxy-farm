# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, ssl

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
out = []


def log(s):
    print(s, flush=True)
    out.append(str(s))


def req(method, path, data=None, headers=None, timeout=15):
    h = {
        "User-Agent": UA,
        "Origin": "https://loiship.com",
        "Referer": "https://loiship.com/",
    }
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(
        "https://api.moegoat.com" + path, data=body, headers=h, method=method
    )
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(r, timeout=timeout, context=ctx)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return "EXC", type(e).__name__


shard = int(sys.argv[1]) if len(sys.argv) > 1 else 1
total = int(sys.argv[2]) if len(sys.argv) > 2 else 8
res_file = "results_%d.jsonl" % shard
prog_file = "progress_%d.txt" % shard
det_file = "details_%d.jsonl" % shard

start_page = shard
try:
    with open(prog_file) as f:
        start_page = int(f.read().strip()) + total
except Exception:
    pass
log("shard%d start: %d" % (shard, start_page))

st, body = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
log("login: %s" % st)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
time.sleep(1)

try:
    with open(res_file) as f:
        seen = set(json.loads(l)["id"] for l in f if l.strip())
except Exception:
    seen = set()

new_items = []
end_page = start_page
for k in range(3):
    pg = start_page + k * total
    st, b = req("GET", "/api/lois?page=%d" % pg, headers=H)
    log("shard%d p%d: %s" % (shard, pg, st))
    if st != 200:
        break
    try:
        items = json.loads(b).get("data") or []
    except Exception:
        break
    if not items:
        break
    for it in items:
        if it.get("id") not in seen:
            new_items.append(it)
            seen.add(it.get("id"))
    end_page = pg
    time.sleep(0.8)

# 详情: 完整 JSON (含 images 数组)
det_lines = []
for it in new_items:
    lid = it.get("id")
    st, b = req("GET", "/api/lois/%s" % lid, headers=H)
    log("shard%d detail %s: %s" % (shard, lid, st))
    if st == 200:
        try:
            full = json.loads(b)
            det_lines.append(
                json.dumps(
                    {"id": lid, "detail": full.get("data", {})}, ensure_ascii=False
                )
            )
        except Exception:
            det_lines.append(
                json.dumps({"id": lid, "detail": b[:1500]}, ensure_ascii=False)
            )
    else:
        det_lines.append(
            json.dumps({"id": lid, "detail_status": st}, ensure_ascii=False)
        )
    time.sleep(0.5)

with open(res_file, "a", encoding="utf-8") as f:
    for it in new_items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
with open(det_file, "a", encoding="utf-8") as f:
    for d in det_lines:
        f.write(d + "\n")
with open(prog_file, "w") as f:
    f.write(str(end_page))
with open("latest.txt", "w") as f:
    f.write("\n".join(out))
log("shard%d DONE %d" % (shard, len(seen)))
