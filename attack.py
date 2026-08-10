# -*- coding: utf-8 -*-
import requests, json, time, os, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
HDR = {
    "User-Agent": UA,
    "Origin": "https://loiship.com",
    "Referer": "https://loiship.com/",
}
out = []


def log(s):
    print(s, flush=True)
    out.append(str(s))


try:
    r = requests.post(
        "https://api.moegoat.com/api/user/login",
        headers=HDR,
        json={"email": "3124323585@qq.com", "password": "9876543210."},
        timeout=15,
    )
    log("login: %s %s" % (r.status_code, r.text[:150]))
    tok = ""
    if r.status_code == 200:
        tok = (r.json().get("access_token") or "").replace("bearer ", "")
    log("token: " + tok[:30])
    H = dict(HDR, Authorization="Bearer " + tok)
    time.sleep(1)
    for ep in [
        "download_v6",
        "download_v5",
        "download_v4",
        "online_play_v2",
        "online_play_v1",
    ]:
        try:
            r = requests.get(
                "https://api.moegoat.com/api/user/loi/%s/6422" % ep,
                headers=H,
                timeout=15,
            )
            log("%s/6422: %s %s" % (ep, r.status_code, r.text[:200]))
        except Exception as e:
            log("%s: EXC %s" % (ep, type(e).__name__))
        time.sleep(0.8)
    for pg in [1, 2]:
        try:
            r = requests.get(
                "https://api.moegoat.com/api/lois?page=%d" % pg, headers=H, timeout=15
            )
            log("lois p%d: %s %s" % (pg, r.status_code, r.text[:120]))
        except Exception as e:
            log("lois p%d: EXC %s" % (pg, type(e).__name__))
        time.sleep(0.8)
except Exception as e:
    log("FATAL %s %s" % (type(e).__name__, str(e)[:150]))
with open("results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("results written", flush=True)
