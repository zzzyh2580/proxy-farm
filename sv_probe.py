# -*- coding: utf-8 -*-
"""download_v6 响应完整性专项: 不同身份/参数下抓完整 JSON, 找 sv_list/bdp 字段"""

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
        return e.code, e.read().decode("utf-8", "replace")[:250]
    except Exception as e:
        return "EXC", type(e).__name__


shard = int(sys.argv[1]) if len(sys.argv) > 1 else 1
res = []

# 身份1: 正常登录
st, b = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(b).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
log("login: %s" % st)
time.sleep(1)

# 抓 download_v6 完整响应(带 token)
for lid in [6422, 6420, 6419]:
    st, b = req("GET", "/api/user/loi/download_v6/%d" % lid, headers=H)
    res.append({"t": "dl-%d" % lid, "s": st, "b": b[:800]})
    log("dl %d (token): %s %s" % (lid, st, b[:300].replace("\n", " ")))
    time.sleep(0.4)

# 身份2: 游客
st, b = req("POST", "/api/user/guest-signup")
gt = ""
try:
    gj = json.loads(b)
    gt = (gj.get("access_token") or "").replace("bearer ", "")
except Exception:
    pass
log("guest-signup: %s" % st)
if gt:
    GH = {"Authorization": "Bearer " + gt}
    st, b = req("GET", "/api/user/loi/download_v6/6422", headers=GH)
    res.append({"t": "dl-guest", "s": st, "b": b[:800]})
    log("dl guest: %s %s" % (st, b[:300].replace("\n", " ")))
    time.sleep(0.4)

# 身份3: 无 token
st, b = req("GET", "/api/user/loi/download_v6/6422")
res.append({"t": "dl-anon", "s": st, "b": b[:800]})
log("dl anon: %s %s" % (st, b[:300].replace("\n", " ")))
time.sleep(0.4)

# 身份4: 新注册账号(可能是"体验会员"?)
suf = str(int(time.time()))[-6:]
st, b = req(
    "POST",
    "/api/user/signup",
    {"username": "test%s" % suf, "email": "%s@qq.com" % suf, "password": "Test1234!"},
)
log("signup: %s %s" % (st, b[:120]))
nt = ""
if st == 200:
    try:
        j = json.loads(b)
        nt = (j.get("signup_token") or j.get("access_token") or "").replace(
            "bearer ", ""
        )
    except Exception:
        pass
if nt:
    NH = {"Authorization": "Bearer " + nt}
    st, b = req("GET", "/api/user/loi/download_v6/6422", headers=NH)
    res.append({"t": "dl-newuser", "s": st, "b": b[:800]})
    log("dl newuser: %s %s" % (st, b[:300].replace("\n", " ")))
    st, b = req("GET", "/api/user/loi/online_play_v2/6422", headers=NH)
    res.append({"t": "op-newuser", "s": st, "b": b[:800]})
    log("op newuser: %s %s" % (st, b[:300].replace("\n", " ")))

with open("sv_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sv_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("sv shard%d done" % shard)
