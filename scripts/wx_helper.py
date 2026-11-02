# -*- coding: utf-8 -*-
"""微信 API 封装：stable_token / 素材 / 草稿。凭据从本文件同目录 wx_accounts.json 读取（不入库）。"""
import json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE, "wx_accounts.json")

def _accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        sys.exit("缺少 scripts/wx_accounts.json，请复制 wx_accounts.example.json 并填入凭据")
    return json.load(open(ACCOUNTS_FILE, encoding="utf-8"))

def _curl(args, timeout=60):
    r = subprocess.run(["curl", "-s", "--max-time", str(timeout)] + args, capture_output=True, text=True)
    return r.stdout

def stable_token(account):
    acc = _accounts()[account]
    out = _curl(["-X", "POST", "https://api.weixin.qq.com/cgi-bin/stable_token",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps({"grant_type": "client_credential", **acc, "force_refresh": False})])
    d = json.loads(out)
    assert "access_token" in d, d  # 40125 = secret 失效，向用户要新的，勿重试
    return d["access_token"]

def add_material(token, path, mtype="image"):
    out = _curl([f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type={mtype}",
                 "-F", f"media=@{path}"])
    return json.loads(out)

def uploadimg(token, path):
    """正文图换 mmbiz URL（https，http 会 40035）"""
    out = _curl([f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}", "-F", f"media=@{path}"])
    return json.loads(out)

def draft_add(token, payload):
    p = os.path.join(os.environ.get("TMPDIR", "."), "draft_payload_tmp.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)  # ensure_ascii=False 防中文乱码
    out = _curl([f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
                 "-H", "Content-Type: application/json; charset=utf-8",
                 "--data-binary", f"@{p}"], timeout=90)
    return json.loads(out)

def draft_update(token, media_id, article, index=0):
    """原位更新草稿（media_id 不变）"""
    p = os.path.join(os.environ.get("TMPDIR", "."), "draft_payload_tmp.json")
    payload = {"media_id": media_id, "index": index, "articles": article}
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    out = _curl([f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}",
                 "-H", "Content-Type: application/json; charset=utf-8",
                 "--data-binary", f"@{p}"], timeout=90)
    return json.loads(out)

def draft_batchget(token, offset=0, count=10, no_content=0):
    out = _curl([f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps({"offset": offset, "count": count, "no_content": no_content})], timeout=90)
    return json.loads(out)

def draft_get(token, media_id):
    out = _curl([f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps({"media_id": media_id})], timeout=90)
    return json.loads(out)

def draft_verify_pull(token, media_id, out_dir):
    """回读草稿正文，生成 390px 预览 HTML，返回 (content, img_count)"""
    import re
    g = draft_get(token, media_id)
    ni = g["news_item"][0]
    content = ni.get("content", "")
    open(os.path.join(out_dir, "draft_content.html"), "w", encoding="utf-8").write(content)
    pv = re.sub(r'<img([^>]*?)\s+data-src="', r'<img\1 src="', content)
    wrap = ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
            '<body style="margin:0;background:#fff;max-width:390px;margin:0 auto;padding:12px;">')
    open(os.path.join(out_dir, "draft_preview.html"), "w", encoding="utf-8").write(wrap + pv + "</body></html>")
    return content, len(re.findall(r"<img", content))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    acc = sys.argv[2] if len(sys.argv) > 2 else "main"
    if cmd == "token":
        print(stable_token(acc))
    elif cmd == "drafts":
        bg = draft_batchget(stable_token(acc), no_content=1)
        for it in bg.get("item", []):
            ni = it["content"]["news_item"][0]
            print(it["media_id"], "|", ni.get("article_type"), "|", ni.get("title"))
