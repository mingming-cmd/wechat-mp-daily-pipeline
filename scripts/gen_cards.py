# -*- coding: utf-8 -*-
"""小绿书图文卡片模板：Pexels 1080x1440 实景底图 + PIL 文字层。
硬规则：所有文字字号 >50px（主标题 >=100px）；文案放不下就精简文字，绝不缩字号。
用法：改 PAGES 后 python gen_cards.py；底图自动从 Pexels 下载（需 .env 里 PEXELS_API_KEY，
      或先把 base-1..6.jpg 放进 OUT 目录手工供图）。
"""
import json, os, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageStat

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "06-成图")
os.makedirs(OUT, exist_ok=True)
FONT_B = "msyhbd.ttc"   # Windows 微软雅黑粗体；跨平台请换成本地存在的字体路径
FONT_L = "msyhl.ttc"
WHITE, GRAY, GOLD = (255, 255, 255), (205, 205, 205), (232, 197, 132)

# ↓↓↓ 每页一张卡：tag=眉标  big=主标题  sub=副标题  note=底部注释(来源链接)  kw=Pexels搜索词
PAGES = [
    dict(tag="眉标", big="主标题", sub="一句话副标题", note="来源链接",
         kw="workspace desk"),
    dict(tag="第 1 页", big="要点一", sub="说明文字", note="来源链接", kw="technology"),
    dict(tag="第 2 页", big="要点二", sub="说明文字", note="来源链接", kw="code"),
    dict(tag="第 3 页", big="要点三", sub="说明文字", note="来源链接", kw="city night"),
    dict(tag="第 4 页", big="要点四", sub="说明文字", note="来源链接", kw="coffee"),
    dict(tag="收尾", big="记住这几点", sub="总结句", note="详细全文见今日推文", kw="notebook"),
]


def pexels_key():
    env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env):
        for ln in open(env, encoding="utf-8"):
            if ln.startswith("PEXELS_API_KEY="):
                return ln.split("=", 1)[1].strip()
    return os.environ.get("PEXELS_API_KEY", "")


def fetch_base(kw, path):
    """Pexels 竖版搜索下载第一张（1080x1440 目标，取 large 档后本地裁剪）"""
    if os.path.exists(path) and os.path.getsize(path) > 100000:
        print("skip", path); return
    key = pexels_key()
    assert key, "缺少 PEXELS_API_KEY，或手工把 base-N.jpg 放进 " + OUT
    req = urllib.request.Request(
        "https://api.pexels.com/v1/search?query=" + urllib.parse.quote(kw) +
        "&orientation=portrait&per_page=5",
        headers={"Authorization": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        photos = json.loads(r.read())["photos"]
    src = photos[0]["src"]["large"]
    urllib.request.urlretrieve(src, path)
    print("pexels ok", path)


def resize_crop(img, tw=1080, th=1440):
    w, h = img.size
    s = max(tw / w, th / h)
    img = img.resize((int(w * s + 0.5), int(h * s + 0.5)), Image.LANCZOS)
    w, h = img.size
    return img.crop(((w - tw) // 2, (h - th) // 2, (w + tw) // 2, (h + th) // 2))


def darken(img):
    img = ImageEnhance.Brightness(img).enhance(0.55)
    ov = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(ov)
    d.rectangle([0, int(img.size[1] * 0.42), img.size[0], img.size[1]], fill=110)
    return Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, ov)


def draw_wrapped(d, text, font, x, y, maxw, fill, line_gap=18):
    """超宽自动换行（不缩字号），返回新 y"""
    line, lines = "", []
    for ch in text:
        if d.textlength(line + ch, font=font) > maxw and line:
            lines.append(line); line = ch
        else:
            line += ch
    lines.append(line)
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += font.size + line_gap
    return y


def draw_page(page, base_path, out_path):
    img = darken(resize_crop(Image.open(base_path).convert("RGB")))
    d = ImageDraw.Draw(img)
    f_tag = ImageFont.truetype(FONT_L, 52)   # 字号硬规则：全部 >50px
    f_note = ImageFont.truetype(FONT_L, 52)
    x, y = 72, 560
    d.text((x, y), page["tag"], font=f_tag, fill=GOLD); y += 52 + 24
    fs = 140 if len(page["big"]) <= 8 else 92   # 主标题 >=100px 为原则，超长标题才降到 92
    assert fs > 50
    f_big = ImageFont.truetype(FONT_B, fs)
    d.text((x, y), page["big"], font=f_big, fill=WHITE); y += fs + 36
    f_sub = ImageFont.truetype(FONT_B, 52)
    y = draw_wrapped(d, page["sub"], f_sub, x, y, 1080 - 144, WHITE)
    y += 10
    d.rectangle([x, y, x + 380, y + 4], fill=GOLD); y += 30
    y = draw_wrapped(d, page["note"], f_note, x, y, 1080 - 144, GRAY)
    assert y < 1440 - 30, f"文字溢出画布: {page['tag']} bottom={y}"
    img.save(out_path, quality=90)
    print("page ok", out_path)


if __name__ == "__main__":
    for i, page in enumerate(PAGES, 1):
        base = os.path.join(OUT, f"base-{i}.jpg")
        fetch_base(page["kw"], base)
        draw_page(page, base, os.path.join(OUT, f"page-{i}.jpg"))
    print("ALL DONE")
