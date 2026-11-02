# -*- coding: utf-8 -*-
"""智谱 MCP 联网搜索（web_search_prime）。Key 从仓库根 .env 的 GLM_API_KEY 或环境变量读取。
用法：python mcp_search.py "查询词" [recency: one_day|one_week|one_month|no_limit]
"""
import json, os, sys, urllib.request

ENDPOINT = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"

def _key():
    env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env):
        for ln in open(env, encoding="utf-8"):
            if ln.startswith("GLM_API_KEY="):
                return ln.split("=", 1)[1].strip()
    return os.environ.get("GLM_API_KEY", "")

def _rpc(method, params=None, sid=None, key=""):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    if sid:
        req.add_header("mcp-session-id", sid)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read()), r.headers.get("mcp-session-id") or sid

def search(query, recency="no_limit"):
    key = _key()
    assert key, "缺少 GLM_API_KEY（.env 或环境变量）"
    _, sid = _rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "pipeline", "version": "1.0"}}, key=key)
    _rpc("notifications/initialized", sid=sid, key=key)
    r, _ = _rpc("tools/call", {"name": "search", "arguments": {"query": query, "recency": recency}}, sid=sid, key=key)
    out = []
    for item in r.get("result", {}).get("content", []):
        if item.get("type") == "text":
            out.append(item["text"])
    return "\n".join(out)

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "test"
    rec = sys.argv[2] if len(sys.argv) > 2 else "no_limit"
    print(search(q, rec))
