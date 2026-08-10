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

# 已收集的 id(去重判断)
try:
    with open(res_file) as f:
        seen = set(json.loads(l)["id"] for l in f if l.strip())
except Exception:
    seen = set()

# 1 页列表(推进游标)
new_items = []
end_page = start_page
st, b = req("GET", "/api/lois?page=%d" % start_page, headers=H)
log("page %d: %s" % (start_page, st))
if st == 200:
    try:
        items = json.loads(b).get("data") or []
        for it in items:
            if it.get("id") not in seen:
                new_items.append(it)
                seen.add(it.get("id"))
        end_page = start_page
    except Exception:
        pass
    time.sleep(0.8)

# 详情完整 JSON (最多 10 条)
det_lines = []
for it in new_items[:10]:
    lid = it.get("id")
    st, b = req("GET", "/api/lois/%s" % lid, headers=H)
    log("detail %s: %s" % (lid, st))
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
log(
    "shard%d DONE 列表%d 详情%d 累计%d"
    % (shard, len(new_items), len(det_lines), len(seen))
)
