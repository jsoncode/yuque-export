# yuque-export

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

批量导出[语雀](https://www.yuque.com)知识库文档为 Markdown，并自动下载文档中的 CDN 图片等资源到本地。

## 功能特性

- 通过 Cookie 登录，无需额外接入语雀开放平台
- 自动解析知识库目录（TOC），批量导出全部文档
- 调用语雀官方导出接口，输出标准 Markdown
- 自动下载 `cdn.nlark.com/yuque` 资源，并重写为本地相对路径
- 保存完整 `appData.json`，便于排查目录结构与文档计数差异
- 导出失败时输出详细日志，方便定位问题

## 环境要求

- Python 3.10+
- 可访问 `yuque.com` 的网络环境
- 拥有目标知识库访问权限的语雀账号

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/jsoncode/yuque-export.git
cd yuque-export
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

建议使用虚拟环境：

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置

复制示例配置并填写你的信息：

```bash
cp config.example.yaml config.yaml
```

`config.yaml` 示例：

```yaml
username: your_namespace   # 语雀用户名/团队空间
project: your_repo         # 知识库 slug

# 浏览器登录语雀后，从开发者工具复制完整 Cookie
cookie: "your_cookie_here"

# 导出根目录，实际输出为 {output_dir}/{book.name}/{title}/
output_dir: ./output
```

#### 如何获取 Cookie

1. 在浏览器中登录 [语雀](https://www.yuque.com)
2. 打开开发者工具（F12）→ **Network（网络）**
3. 刷新任意语雀页面，选中一条请求
4. 在 **Request Headers** 中找到 `Cookie`，复制完整值粘贴到配置文件

> **注意：** Cookie 包含登录凭证，请勿提交到 Git 或公开分享。本项目已在 `.gitignore` 中忽略 `config.yaml`。

### 4. 运行导出

```bash
python main.py
```

可选参数：

```bash
# 指定配置文件
python main.py -c config.yaml

# 输出详细日志
python main.py -v
```

## 输出目录结构

```
output/
└── {book.name}/              # 来自 appData.book.name
    ├── appData.json          # 原始 appData，用于排查
    ├── 文档标题 A/
    │   ├── index.md
    │   └── assets/
    │       └── image.png
    └── 文档标题 B/
        ├── index.md
        └── assets/
```

> 目录名使用知识库显示名称（`appData.book.name`），而非配置中的 `project` slug。若 name 为空则回退为 `project`。

## 工作原理

1. 访问 `https://www.yuque.com/{username}/{project}`，从页面解析 `window.appData`
2. 读取 `appData.book.toc`，提取所有 `type=DOC` 的文档节点
3. 对每个文档调用导出接口获取 Markdown 下载地址
4. 下载 Markdown，提取其中的 `https://cdn.nlark.com/yuque/...` 资源链接
5. 将资源保存到 `assets/`，并把 Markdown 中的链接替换为 `./assets/...`

### 关于文档 ID

语雀 TOC 节点包含多种标识，其中页面路由标识与导出 API 所需标识不同。**导出 API 需使用数值型文档 ID，不可使用页面路由标识。** 本项目已按此规则处理。

### 关于文档数量

侧边栏显示的节点数可能包含 `type=TITLE` 的目录标题，这类节点不是可导出的文档。实际可导出数量以 `book.items_count` 及 TOC 中 `type=DOC` 的条目为准。运行时会输出统计信息，也可查看 `appData.json` 核对。

## 项目结构

```
yuque-export/
├── main.py                 # CLI 入口
├── config.example.yaml     # 配置示例
├── requirements.txt
├── yuque_export/
│   ├── config.py           # 配置加载
│   ├── client.py           # 语雀 API 客户端
│   ├── assets.py           # 资源下载与链接替换
│   └── exporter.py         # 导出主流程
└── LICENSE
```

## 常见问题

**Q: 导出报 404 Not Found**

通常是误用了页面路由标识调用导出接口。请查看 `appData.json` 中 TOC 节点的数值型文档 ID 是否正确。

**Q: 提示未找到 appData**

Cookie 可能已过期，请重新登录语雀并更新 `config.yaml` 中的 Cookie。

**Q: 部分图片未下载**

目前仅匹配 `https://cdn.nlark.com/yuque/...` 格式的资源链接。如有其他 CDN 域名，欢迎提交 Issue 或 PR。

## 免责声明

- 本工具通过模拟浏览器请求调用语雀 Web 接口，**非语雀官方产品**
- 请遵守语雀服务条款，仅导出你有权访问的内容
- 语雀接口可能随时变更，导致工具失效；使用时请自行评估风险
- Cookie 属于敏感信息，请妥善保管

## 贡献

欢迎提交 Issue 和 Pull Request。

## 开源协议

本项目采用 [MIT License](LICENSE) 开源。
