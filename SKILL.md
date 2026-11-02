---
name: wechat-official-account-delivery
version: 1.0.0
license: MIT
description: Use when 给自己的微信公众号产文章/小绿书图文并上传草稿箱。双排版引擎按日轮转、Pexels 图文卡、定时全自动。
---

# 公众号交付管线

## When to Use

用户要求给自己的公众号写文章、写图文、排版、配图或上传微信草稿箱时使用。默认单账号。

## 前置配置

1. `scripts/wx_accounts.json`（复制 example 后填 AppID/AppSecret，**此文件永不入库**）
2. 可选 `.env`：`GLM_API_KEY`（智谱 MCP 联网搜索）、`PEXELS_API_KEY`（免密钥时手工供图）
3. 如需预览截图：`Python311 -m playwright install chromium`

## 交付流程（顺序执行，失败即停）

1. **选题+事实**：联网搜索用 `mcp_search.py`（智谱 MCP `web_search_prime` 端点，JSON-RPC 2.0 握手）。政策类以官网原文为准，事实存 `选题目录/fact_notes.md`。
2. **终稿**：写 `终稿.md`；按你自己的写作规范去 AI 腔（短句、口语、具体数字、禁止排比三连）。字数 1800-2500。
3. **排版**：`render_bridge.py` 统一入口。`pick_style()` 按年内第 N 天取模轮转；engine=house 走 house_styles，engine=pipeline 走 davinci 渲染器。**pipeline 稿件只用 标题/正文/粗体/列表/引用/图片 六种语法**（遇不支持语法会停整个流程）。封面始终另配（2.35:1，900×383）。
4. **配图**：正文图 3-4 张宽 1080；图文卡用 `gen_cards.py`（Pexels 1080×1440 实景底图 + PIL 文字层）。
5. **上传**：文章 `upload_articles.py`；图文 `upload_newspic.py`（6 图 add_material 永久素材 + draft/add article_type=newspic）。图文 title ≤20 字；文章 API 标题 ≤64 字节，超了用短版。
6. **验证**：draft/get 回读确认无乱码、无本地路径泄漏；data-src→src 后 Playwright 截 390px 长图。
7. **回填**：文章发布后，把真实文章链接用 `update_newspic.py` 原位回填到图文占位处（media_id 不变；原草稿被删时自动回退新建）。

## 硬规则

- **图文卡片所有文字字号 >50px**（主标题 ≥100px）；文案放不下就精简，绝不缩字号。
- 正文 mmbiz 图片必须 https，http 会 40035。
- stable_token 缓存 7200 秒，全程复用。
- 订阅号正文不可放可点外链：链接做黑底图片卡，引导复制。
- **微信草稿无法删除**：传之前先本地截 HTML 自查；任何失败如实报告，禁止编造 media_id。
- pipeline 渲染后本地 img src 被重写到 assets/ 前缀：换图床 URL 按 `<img>` 的 alt（图注）正则逐个匹配，不按文件名 replace。
- house 体系 fig_map 按小标题匹配：标题含中文弯引号时用 re.sub 不用 replace。
- secret 轮换报 40125 = secret 失效，向用户要新的，不要重试。

## 自动化

用你自己 Agent 的定时器每天触发本技能（示例：Hermes cronjob_manage 每天 07:30，deliver=origin）。每日固定产出：1 文章 + 1 图文。
