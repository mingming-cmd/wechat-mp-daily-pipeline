# -*- coding: utf-8 -*-
"""小绿书图文（newspic）传草稿箱：6 图永久素材 + draft/add + 回读验证
用法：python upload_newspic.py --account tech --dir 图文目录 --title 标题（≤20字）
图文目录需含：06-成图/page-1..6.jpg、图文文案.txt（首行可为「标题：...」）
"""
import argparse, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_helper import stable_token, add_material, draft_add, draft_get


def run(account, base, title):
    print(f"\n##### {account} {title} #####")
    tk = stable_token(account)
    ids = []
    for i in range(1, 7):
        p = os.path.join(base, "06-成图", f"page-{i}.jpg")
        d = add_material(tk, p)
        assert "media_id" in d, d
        ids.append(d["media_id"])
        print(f"img{i} ok", d["media_id"][:16])
    txt = open(os.path.join(base, "图文文案.txt"), encoding="utf-8").read()
    content = re.sub(r"^标题：.*\n", "", txt).strip()
    assert len(content) <= 1000, len(content)
    payload = {"articles": [{
        "article_type": "newspic",
        "title": title,
        "content": content,
        "image_info": {"image_list": [{"image_media_id": m} for m in ids]},
        "need_open_comment": 1, "only_fans_can_comment": 0}]}
    res = draft_add(tk, payload)
    print("draft/add:", res)
    assert "media_id" in res, res
    time.sleep(2)
    g = draft_get(tk, res["media_id"])
    ni = g["news_item"][0]
    print("VERIFY type:", ni.get("article_type"), "| imgs:", len(ni["image_info"]["image_list"]),
          "| title:", ni["title"])
    open(os.path.join(base, "newspic_media_id.txt"), "w").write(res["media_id"])
    return res["media_id"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--title", required=True)
    a = ap.parse_args()
    print("media_id:", run(a.account, a.dir, a.title))
