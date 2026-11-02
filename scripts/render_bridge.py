# -*- coding: utf-8 -*-
"""双引擎排版桥接：house_styles 与 davinci wechat-article-pipeline 双引擎 + 按日轮转。
house 引擎需环境变量 HOUSE_STYLES_DIR 指向 house_styles.py 所在目录；
pipeline 引擎需环境变量 PIPELINE_DIR 指向 davinci-seven/wechat-article-pipeline 检出目录。
"""
import datetime, json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
POOL_FILE = os.path.join(BASE, "style_pool.json")

DEFAULT_POOL = [
    {"engine": "house", "style": 10},
    {"engine": "pipeline", "theme": "olive-journal"},
    {"engine": "house", "style": 1},
    {"engine": "pipeline", "theme": "graphite-minimal"},
    {"engine": "house", "style": 7},
    {"engine": "pipeline", "theme": "red-white"},
    {"engine": "house", "style": 5},
    {"engine": "pipeline", "theme": "moyu-green"},
    {"engine": "house", "style": 4},
    {"engine": "pipeline", "theme": "zen-whitespace"},
]


def load_pool():
    """style_pool.json 为轮换池列表；缺省用内置 DEFAULT_POOL"""
    if os.path.exists(POOL_FILE):
        return json.load(open(POOL_FILE, encoding="utf-8"))
    return DEFAULT_POOL


def pick_style(account="main"):
    pool = load_pool()
    day = (datetime.date.today() - datetime.date(2026, 1, 1)).days
    return pool[day % len(pool)]


def _insert_figs(md_text, fig_plan, article_dir):
    """把 ![](file) 插到对应小节第一段之后；路径用相对 article_dir 的写法，供渲染器解析"""
    lines = md_text.split("\n")
    for fig in fig_plan:
        target, inserted = fig["section"], False
        rel = os.path.relpath(fig["file"], article_dir).replace("\\", "/")
        for i, ln in enumerate(lines):
            if ln.strip().startswith("## ") and target in ln:
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].strip().startswith("![") and not lines[j].strip().startswith("## "):
                        lines.insert(j + 1, "")
                        lines.insert(j + 2, "![" + fig["caption"] + "](" + rel + ")")
                        inserted = True
                        break
                break
        if not inserted:
            raise RuntimeError("pipeline 插图失败，找不到小节: " + target)
    return "\n".join(lines)


def render_pipeline(theme, md_text, article_dir, fig_plan, account, title, subtitle=None, risk_text=None):
    """pipeline 引擎渲染 + 正文图传微信换 mmbiz。返回 (clean_html, upload_ready_html, integrity)。"""
    pipe = os.environ.get("PIPELINE_DIR", "")
    py = os.environ.get("PYTHON311", sys.executable)
    assert pipe, "pipeline 引擎需设置 PIPELINE_DIR（davinci-seven/wechat-article-pipeline 检出目录）"
    render_md = os.path.join(article_dir, "_pipeline_render.md")
    md = _insert_figs(md_text, fig_plan, article_dir)
    open(render_md, "w", encoding="utf-8").write(md)
    out_root = os.path.join(article_dir, "pipeline排版")
    r = subprocess.run([py, os.path.join(pipe, "tools", "render_wechat.py"),
                        "--markdown", render_md, "--output-root", out_root, "--theme", theme],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("pipeline 渲染失败: " + r.stdout[-500:] + r.stderr[-500:])
    integ = json.load(open(os.path.join(out_root, "source-integrity.json"), encoding="utf-8"))
    if not integ.get("source_unchanged"):
        raise RuntimeError("原稿 SHA256 不一致，中止")
    if integ.get("missing_image_count", 0):
        raise RuntimeError(f"缺图 {integ['missing_image_count']} 张，中止")
    clean = open(integ["clean_html"], encoding="utf-8").read()
    html = clean
    if fig_plan:
        sys.path.insert(0, BASE)
        from wx_helper import stable_token, uploadimg
        tk = stable_token(account)
        for fig in fig_plan:
            up = uploadimg(tk, fig["file"])
            url = up["url"]
            # 渲染器把 src 重写到 assets/ 前缀，必须按 alt(图注) 正则匹配替换，不能按文件名 replace
            pat = re.compile(r'(<img\s+src=")assets/[^"]*(" alt="' + re.escape(fig["caption"]) + r'")')
            html, n = pat.subn(lambda m: m.group(1) + url + m.group(2), html, count=1)
            if n != 1:
                raise RuntimeError("图片替换失败: " + fig["caption"])
    if 'src="assets/' in html:
        raise RuntimeError("仍有未替换的本地图片")
    return clean, html, integ


def render(spec, md_text, article_dir, fig_plan, account, title, subtitle=None, risk_text=None,
           fig_map_resolved=None):
    """统一入口：spec 来自 pick_style()。返回上传就绪 HTML。"""
    if spec["engine"] == "pipeline":
        return render_pipeline(spec["theme"], md_text, article_dir, fig_plan, account, title, subtitle, risk_text)[1]
    hs = os.environ.get("HOUSE_STYLES_DIR", "")
    assert hs, "house 引擎需设置 HOUSE_STYLES_DIR（house_styles.py 所在目录）"
    sys.path.insert(0, hs)
    from house_styles import build_article
    return build_article(style=spec["style"], md_text=md_text, fig_map=fig_map_resolved or {},
                         title=title, subtitle=subtitle, account=account, risk_text=risk_text or "")


if __name__ == "__main__":
    acc = sys.argv[1] if len(sys.argv) > 1 else "tech"
    print(json.dumps(pick_style(acc), ensure_ascii=False))
