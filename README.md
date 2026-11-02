# 微信公众号每日生产线：1 篇文章 + 1 条小绿书图文，排版风格按日自动轮转

每天给自己的公众号发 1 篇文章 + 1 条小绿书图文。最烦的不是写，是写完之后那一整套：搜事实、配图、排版、传草稿、验证、回填链接——每天两小时起步，一个字没多写，人先烦了。

这套流水线把那一整套接了起来：AI Agent 从选题跑到草稿箱，每天 2 个交付物自动产出，排版风格在多套方案之间按日轮换，不再审美疲劳。

不是概念验证，是正在每天跑的生产系统。

## 先把东西给你

仓库在这：本仓库。MIT 协议，拿去用。

你需要的：

- Python 3.10+（Pillow 必需；Playwright 仅预览截图需要）
- 一个支持 Skills 的 AI Agent（Claude Code / Codex / Cursor / Hermes 任选）
- 你的微信公众号开发者凭据（AppID + AppSecret，在公众号后台「开发-基本配置」拿）
- 可选：智谱 GLM API Key（联网搜索）、Pexels API Key（免密钥可降级为手工供图）

```bash
cp scripts/wx_accounts.example.json scripts/wx_accounts.json   # 填入你自己的 AppID/AppSecret
cp .env.example .env                                            # 可选：填入搜索/配图 Key
```

对 Agent 说「跑今天的公众号生产线」，或者挂上定时任务每天自动跑（见下文「自动化」）。

## 这条链路长什么样

```
选题(MCP联网搜索) → 终稿(去AI腔) → 排版(双引擎按日轮转) → 配图(Pexels实景底图)
      → 传草稿箱(微信API) → 回读验证 → 390px长图预览 → 定时交付
```

七个环节，每一环都有明确产出和失败即停的断言。任何一步挂了（secret 失效、缺图、渲染中止），如实报错，不编造 media_id——因为**微信草稿删不掉**，错稿只能永久躺在草稿箱里。

## 排版：双引擎，按日轮转

单调是最快的审美疲劳。池子里放了两类引擎，每天自动换一个：

| 引擎 | 风格数 | 特点 |
|---|---|---|
| house_styles | 10 | 组件化：导语卡、小节插图、GitHub 链接自动转黑底卡片、风险提示卡 |
| wechat-article-pipeline | 6 | 整版视觉：橄榄手记 / 石墨极简 / 摸鱼绿 / 红白色系 / 留白禅意 / 摸鱼票据 |

轮换表就是一个 JSON（`style_pool.json`），改池子不用动代码：

```json
[
  {"engine": "house", "style": 10},
  {"engine": "pipeline", "theme": "olive-journal"},
  {"engine": "house", "style": 1}
]
```

`render_bridge.py` 是统一入口：`pick_style()` 按年内第 N 天取模选风格，`render()` 对调用方屏蔽引擎差异。pipeline 引擎渲染前会校验原稿 SHA256，缺图即停。

## 小绿书图文（newspic）

文章之外，每天再产 1 条 6 页图文，与当日文章同主题互相导流：

- 底图：Pexels 实景照片（1080×1440），底部文字区压暗保证可读性
- **字号硬规则：所有文字 >50px，主标题 ≥100px**；文案放不下就精简文字，绝不缩字号
- 超宽自动换行，溢出画布直接断言失败
- 末尾页带来源链接（开源项目给 GitHub 地址）
- 图文里放文章链接占位，文章发布后 `update_newspic.py` 原位回填（media_id 不变）

## 传草稿箱与验证

- 正文图走 `uploadimg` 换 mmbiz URL（http 会 40035，必须 https）
- 图文 6 页走 `add_material` 永久素材 + `draft/add article_type=newspic`
- `stable_token` 服务端缓存 7200 秒，全程复用同一 token
- 权威预览 = `draft/get` 拉回的正文截 390px 长图，不是本地 HTML 的样子
- 订阅号正文不能放可点外链，链接做成黑底图片卡引导复制

## 自动化

仓库不内置 cron，用你自己 Agent 的定时器。以 Hermes 为例：

```
cronjob_manage: create, schedule="every day at 7:30am",
skills=["wechat-official-account-delivery"], workdir=<本仓库>
```

每天固定产出：1 文章 + 1 图文，media_id 清单 + 预览图自动推送到你的会话。

## 边界说清楚

- 这套东西管的是**你自己账号的内容生产**，微信凭据只在你的机器上，不上传任何第三方
- pipeline 六主题换的是配色和排印，文章结构共用；要每套组件都不同请用原版 gzh-design
- house_styles 的 10 套风格是自用积累，和 pipeline 引擎职责不同：前者管组件，后者管整版视觉
- 写作环节的去 AI 腔规范因人而异，仓库里给的是通用原则，换成你自己的范文效果更好

## 致谢

整条链路站在三个开源项目的肩膀上：

- [davinci-seven/wechat-article-pipeline](https://github.com/davinci-seven/wechat-article-pipeline) — 六主题渲染器与质检流程，本仓库通过运行时调用接入，未复制其源码
- 其底层 [gzh-design](https://github.com/isjiamu/gzh-design-skill)（AGPL-3.0，作者甲木、摸鱼小李）解决公众号编辑器兼容性
- 微信官方草稿/素材 API（md2wechat 的思路，作者极客杰尼）

难的部分是他们做的。这套仓库花时间的部分，只是把选题、写作、双引擎排版、图文卡、上传、验证、回填、定时这一整条接起来、踩坑、测试。

觉得省事，记得顺手去给上面几个项目点 star。

## 目录

```
├── README.md                 本文
├── SKILL.md                  Agent 技能版（装进任何支持 Skills 的 Agent）
├── scripts/
│   ├── wx_helper.py          微信 API 封装（token/素材/草稿/原位更新）
│   ├── wx_accounts.example.json
│   ├── render_bridge.py      双引擎排版桥接 + 按日轮转
│   ├── mcp_search.py         智谱 MCP 联网搜索
│   ├── upload_articles.py    文章：换图床→重建HTML→draft/add→回读
│   ├── upload_newspic.py     图文：6图素材→draft/add(newspic)→回读
│   ├── update_newspic.py     图文原位更新（含草稿丢失自动回退新建）
│   └── gen_cards.py          图文卡片模板（>50px 硬规则内建）
├── examples/
│   ├── style_pool.example.json
│   └── build_article_house.py
└── .env.example
```

跑通了、或者哪一步卡住了，开个 issue，或者直接在评论区告诉我。
