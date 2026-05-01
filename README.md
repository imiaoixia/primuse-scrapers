# primuse-scrapers

公网托管的元数据刮削源配置。仅包含接口地址与字段映射；任何源专属的转换算法由 App 端 `nativeResolver` 提供。

## 结构

```
.
├── index.json        # 索引：所有源的元信息 + 单文件 URL
├── bundle.json       # 一次性下载所有源（{ schema, updatedAt, sources: [...] }）
├── netease.json      # 单源配置
├── qqmusic.json
├── kugou.json
├── kuwo.json
├── migu.json
└── tools/
    └── build.py      # 由单源文件重新生成 index/bundle
```

## 使用

部署到 Cloudflare Pages（或任意静态托管）后，三种入口：

- 全量：`GET <base>/bundle.json` → 一次拿到所有源
- 索引：`GET <base>/index.json` → 拿到列表后按需 `GET <base>/<id>.json`
- 直链：`GET <base>/netease.json` 等

`index.json` 中 `url` 字段为相对路径，相对于 `index.json` 自身解析。

## 修改流程

1. 编辑某个 `<id>.json`（或新增一个文件）
2. 在该文件里 `version` 字段 +1，提示 App 端重新拉取
3. `python3 tools/build.py` 重新生成 `index.json` 和 `bundle.json`
4. `git commit && git push` — Cloudflare Pages 自动部署

## 配置 schema

每个源是一个 `ScraperConfig`：

```jsonc
{
  "id": "netease",                 // 唯一标识，App 端用作 key
  "name": "网易云音乐",            // 展示名
  "version": 3,                    // 整数版本号，递增触发更新
  "icon": "cloud",                 // SF Symbol 名（可选）
  "color": "#E60026",              // 展示色（可选）
  "rateLimit": 1000,               // 单源最小请求间隔 (ms)
  "capabilities": ["metadata", "cover", "lyrics"],
  "headers": { "User-Agent": "...", "Referer": "..." },
  "sslTrustDomains": ["..."],      // 可选：跳过证书校验的域名
  "search":  { "url": "...", "method": "GET", "params": {...}, "script": "..." },
  "detail":  { ... },
  "cover":   { ... },
  "lyrics":  { ... }
}
```

`script` 是在 JSContext 中执行的 JS 字符串，可访问：

- `response` — 解析后的 JSON（请求成功时）
- `responseText` — 原始字符串
- `externalId` / `response._externalId` — 详情/封面/歌词请求传入的 ID
- `nativeResolver.*` — App 注入的源专属转换函数（如 `nativeResolver.neteaseCover(picId, size)`）

## 部署到 Cloudflare Pages

1. 推到 GitHub 私有/公开仓库
2. Cloudflare Dashboard → Pages → Connect to Git → 选这个仓库
3. Build command 留空，Output dir 填 `/`
4. 自定义域名（可选）：Pages 项目 → Custom domains
