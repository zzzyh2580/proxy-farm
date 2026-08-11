# -*- coding: utf-8 -*-
"""采集完整 JWT 样本(爆破 secret 用)"""

import urllib.request, json, time, sys, ssl

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

# 登录拿完整 JWT
st, b = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
log("login: %s" % st)
tok = ""
if st == 200:
    try:
        j = json.loads(b)
        tok = (j.get("access_token") or "").replace("bearer ", "")
    except Exception:
        pass
log("TOKEN: %s" % tok)
if tok:
    with open("jwt_sample.txt", "w") as f:
        f.write(tok)
    log("jwt saved len=%d" % len(tok))

with open("jwt_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("done")
