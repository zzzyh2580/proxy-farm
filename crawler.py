# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, json, time, sys, ssl, os

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
out = []


def log(s):
    print(s, flush=True)
    out.append(str(s))


def req(method, path, data=None, headers=None):
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
        resp = urllib.request.urlopen(r, timeout=15, context=ctx)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return "EXC", type(e).__name__


# 1. 读游标
start_page = 1
try:
    with open("progress.txt") as f:
        start_page = int(f.read().strip()) + 1
except Exception:
    pass
log("start page: %d" % start_page)

# 2. 登录
st, body = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
log("login: %s" % st)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
time.sleep(1)

# 3. 累积文件
try:
    with open("results.jsonl") as f:
        seen = set(json.loads(l)["id"] for l in f if l.strip())
except Exception:
    seen = set()

new_items = []
end_page = start_page
for pg in range(start_page, start_page + 3):
    st, b = req("GET", "/api/lois?page=%d" % pg, headers=H)
    log("page %d: %s" % (pg, st))
    if st != 200:
        log("窗口关或错误, 停")
        break
    try:
        items = json.loads(b).get("data") or []
    except Exception:
        break
    if not items:
        log("到底了, 完成全量")
        break
    added = 0
    for it in items:
        if it.get("id") not in seen:
            new_items.append(it)
            seen.add(it.get("id"))
            added += 1
    log("page %d: %d 条, 新增 %d, 累计 %d" % (pg, len(items), added, len(seen)))
    end_page = pg
    time.sleep(0.8)

# 4. 写累积
with open("results.jsonl", "a", encoding="utf-8") as f:
    for it in new_items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
with open("progress.txt", "w") as f:
    f.write(str(end_page))
with open("latest.txt", "w") as f:
    f.write("\n".join(out))
log("DONE 总累计 %d" % len(seen))
