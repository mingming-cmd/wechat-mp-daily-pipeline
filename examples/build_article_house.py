# -*- coding: utf-8 -*-
"""house 引擎排版脚本示例（渲染 + 本地预览，不含上传）。
上传用 upload_articles.py --build build_article_house.py（脚本需读 mmbiz_map.json 输出 article_upload.html）。
运行前设环境变量 HOUSE_STYLES_DIR 指向 house_styles.py 所在目录。
fig_map 键必须是终稿 markdown 的 `## ` 小标题原文（含中文弯引号时用 re.sub 不用 replace）。
"""
import json, os, sys

HOUSE_STYLES_DIR = os.environ.get("HOUSE_STYLES_DIR", r"C:\path\to\house_styles")
sys.path.insert(0, HOUSE_STYLES_DIR)
from house_styles import build_article

BASE = os.path.dirname(os.path.abspath(__file__))  # 文章目录：终稿.md / images/ / cover.jpg
md = open(os.path.join(BASE, "终稿.md"), encoding="utf-8").read()

# 已上传图床则用之，否则用本地路径排版（仅供本地预览）
mmbiz = {}
mp = os.path.join(BASE, "mmbiz_map.json")
if os.path.exists(mp):
    mmbiz = json.load(open(mp, encoding="utf-8"))

fig_map = {
    # "终稿里的小节标题原文": (mmbiz.get("终稿里的小节标题原文", ""), "图注"),
    # 例："263种格式随便转，不要钱，断网也能用": (mmbiz.get("263种格式随便转，不要钱，断网也能用", ""), "深夜的键盘"),
}
fig_map = {k: (v[0] or os.path.join(BASE, "images", k + ".jpg"), v[1]) for k, v in fig_map.items()}

RISK = ""  # 政策/金融类文章填风险提示文本，将自动拼接合规收尾卡

html = build_article(style=10,  # 按账号风格表选择，见 style_pool.json
                     md_text=md, fig_map=fig_map,
                     title="文章标题", subtitle=None,
                     account="main", risk_text=RISK)
open(os.path.join(BASE, "article_upload.html"), "w", encoding="utf-8").write(html)
print("build ok", len(html))
