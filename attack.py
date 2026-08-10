# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, json, time, sys, ssl

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
    url = "https://api.moegoat.com" + path
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(r, timeout=15, context=ctx)
        return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return "EXC", type(e).__name__ + " " + str(e)[:100]


try:
    st, body = req(
        "POST",
        "/api/user/login",
        {"email": "3124323585@qq.com", "password": "9876543210."},
    )
    log("login: %s %s" % (st, body[:150]))
    tok = ""
    if st == 200:
        tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
    log("token: " + tok[:25])
    H = {"Authorization": "Bearer " + tok}
    time.sleep(1)
    for ep in [
        "download_v6",
        "download_v5",
        "download_v4",
        "online_play_v2",
        "online_play_v1",
    ]:
        st, b = req("GET", "/api/user/loi/%s/6422" % ep, headers=H)
        log("%s/6422: %s %s" % (ep, st, b[:180]))
        time.sleep(0.8)
    for pg in [1, 2]:
        st, b = req("GET", "/api/lois?page=%s" % pg, headers=H)
        log("lois p%s: %s %s" % (pg, st, b[:100]))
        time.sleep(0.8)
except Exception as e:
    log("FATAL %s %s" % (type(e).__name__, str(e)[:150]))

with open("results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("DONE, results=%d lines" % len(out), flush=True)
