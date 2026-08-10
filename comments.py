# -*- coding: utf-8 -*-
"""评论挖掘: 拉热门条目评论, 找用户分享的链接/播放地址"""

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
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return "EXC", type(e).__name__


shard = int(sys.argv[1]) if len(sys.argv) > 1 else 1
res = []

# 热门条目(高 download_count 的)
lids = [
    6422,
    6421,
    6420,
    6419,
    6418,
    6417,
    6416,
    6415,
    6414,
    6413,
    6412,
    6411,
    6365,
    6364,
    6363,
    6362,
    6361,
    6360,
    6359,
    6358,
    6357,
    6356,
    6355,
    6354,
    6269,
    6268,
    6267,
    6266,
    6265,
    6264,
    6263,
    6262,
    6261,
    6260,
]

log("=== 评论挖掘(匿名) ===")
for lid in lids:
    for pg in [1, 2, 3]:
        st, b = req("GET", "/api/comment/%d?page=%d&sort=like_number" % (lid, pg))
        res.append({"t": "cmt-%d-p%d" % (lid, pg), "s": st, "b": b[:600]})
        if st == 200:
            # 检测链接
            has_link = any(
                k in b.lower()
                for k in [
                    "http",
                    "pan.baidu",
                    "t.me",
                    "mega",
                    "aliyun",
                    "quark",
                    "lanzou",
                    "115.com",
                    "weiyun",
                    "url",
                    "链接",
                    "提取码",
                ]
            )
            log(
                ">>> comment %d p%d: %s%s"
                % (
                    lid,
                    pg,
                    b[:400].replace("\n", " "),
                    " <<<含链接!" if has_link else "",
                )
            )
            # 空则停
            try:
                if not (json.loads(b).get("data") or []):
                    break
            except Exception:
                break
        else:
            break
        time.sleep(0.35)
        if st == 403:
            log("窗口关, 停")
            raise SystemExit
    if st == 403:
        break

with open("cmt_%d.jsonl" % shard, "w", encoding="utf-8") as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("cmt_%d.txt" % shard, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
log("comments shard%d done" % shard)
