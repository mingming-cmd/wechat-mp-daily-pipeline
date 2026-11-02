# -*- coding: utf-8 -*-
"""文章传草稿箱：封面 + 正文图换 mmbiz → 重建 HTML → draft/add → 回读验证 + 390px 预览
用法：python upload_articles.py --account tech --dir 文章目录 --title 标题 --digest 摘要
     [--cover cover.jpg] [--imgs "小节标题:图片路径;小节标题:图片路径"] [--build build.py]
文章目录需含：build 脚本（可选，读 mmbiz_map.json 重建 article_upload.html）或现成的 article_upload.html
"""
import argparse, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_helper import stable_token, add_material, uploadimg, draft_add, draft_verify_pull


def run(account, base, title, digest, cover, imgs, build):
    print(f"\n##### {account} {title} #####")
    tk = stable_token(account)
    thumb = add_material(tk, os.path.join(base, cover))["media_id"]
    print("thumb ok", thumb[:16])
    url_map = {}
    for section, local in imgs.items():
        u = uploadimg(tk, os.path.join(base, local))["url"]
        url_map[section] = u
        print("img ok", section[:12], u[:60])
    json.dump(url_map, open(os.path.join(base, "mmbiz_map.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if build:
        r = subprocess.run([sys.executable, os.path.join(base, build)], capture_output=True, text=True, cwd=base)
        print(r.stdout[-500:], r.stderr[-300:])
    html = open(os.path.join(base, "article_upload.html"), encoding="utf-8").read()
    assert "images/" not in html and "assets/" not in html and "pexels" not in html, "仍有本地图片引用!"
    payload = {"articles": [{"title": title, "thumb_media_id": thumb, "content": html,
                             "digest": digest, "content_source_url": "",
                             "need_open_comment": 1, "only_fans_can_comment": 0}]}
    res = draft_add(tk, payload)
    print("draft/add:", res)
    assert "media_id" in res, res
    time.sleep(2)
    content, n_img = draft_verify_pull(tk, res["media_id"], base)
    print("VERIFY imgs:", n_img, "| local leak:", ("images/" in content or "pexels" in content))
    open(os.path.join(base, "article_media_id.txt"), "w").write(res["media_id"])
    return res["media_id"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--title", required=True)   # ≤64 字节，超了用短版
    ap.add_argument("--digest", default="")
    ap.add_argument("--cover", default="cover.jpg")
    ap.add_argument("--imgs", default="", help='小节标题:路径;...（house 引擎插图用）')
    ap.add_argument("--build", default="", help="目录内重建 HTML 的脚本名（可选）")
    a = ap.parse_args()
    imgs = {}
    for pair in a.imgs.split(";"):
        if pair.strip():
            k, v = pair.split(":", 1)
            imgs[k.strip()] = v.strip()
    mid = run(a.account, a.dir, a.title, a.digest, a.cover, imgs, a.build)
    print("media_id:", mid)
