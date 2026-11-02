# -*- coding: utf-8 -*-
"""重出图文后原位更新草稿：6 图重新 add_material + draft/update（media_id 不变）。
原草稿被删/已发布（40007）时自动回退 draft/add 新建并更新 newspic_media_id.txt。
用法：python update_newspic.py --account tech --dir 图文目录 --title 标题
"""
import argparse, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_helper import stable_token, add_material, draft_update, draft_get, draft_add


def run(account, base, title):
    print(f"\n##### {account} {title} #####")
    mid_file = os.path.join(base, "newspic_media_id.txt")
    assert os.path.exists(mid_file), "缺少 newspic_media_id.txt，请先用 upload_newspic.py 新建"
    media_id = open(mid_file).read().strip()
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
    article = {
        "article_type": "newspic",
        "title": title,
        "content": content,
        "image_info": {"image_list": [{"image_media_id": m} for m in ids]},
        "need_open_comment": 1, "only_fans_can_comment": 0,
    }
    res = draft_update(tk, media_id, article)
    print("draft/update:", res)
    if res.get("errcode") == 40007:  # 原草稿已不在（被删/已发布），回退新建
        print("原草稿不存在，回退 draft/add 新建")
        res = draft_add(tk, {"articles": [article]})
        media_id = res["media_id"]
        open(mid_file, "w").write(media_id)
    else:
        assert res.get("errcode") == 0, res
    time.sleep(2)
    g = draft_get(tk, media_id)
    ni = g["news_item"][0]
    print("VERIFY media_id:", media_id[:16], "| type:", ni.get("article_type"),
          "| imgs:", len(ni["image_info"]["image_list"]), "| title:", ni["title"])
    return media_id


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--title", required=True)
    a = ap.parse_args()
    print("media_id:", run(a.account, a.dir, a.title))
