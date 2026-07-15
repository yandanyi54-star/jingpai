# 净排 JingPai

> 纯本地 · 不登录 · 文章不出本机，排版照样好看

**净排**是一站式微信公众号 Markdown 排版工具。纯静态页面，所有数据存于浏览器本地，无需注册、无服务器、文章内容绝不离开你的设备。

## 为什么用净排

- **隐私安全** — 纯前端运行，你的文章内容从不过服务器
- **所见即所得** — 左侧 Markdown 编辑，右侧实时预览，支持分屏或全屏
- **一键复制** — 渲染为微信公众号兼容的内联 HTML，复制直接粘贴到公众号后台
- **AI 辅助写作** — 支持 OpenAI 兼容 API，自带 DeepSeek/OpenRouter 预设，浏览器直连厂商
- **丰富主题** — 10 套内置配色主题，支持自定义品牌色和字体
- **装饰元素** — 封面块、分割线、引用区的容器语法，一键插入

## 快速开始

```bash
# 安装依赖
pnpm install     # 或 npm install

# 启动开发服务器
pnpm run dev     # 或 npm run dev

# 浏览器打开 http://localhost:3000
```

Windows 用户可直接双击 `start.bat`。

## 技术栈

| 层 | 技术 |
|---|------|
| 框架 | Vue 3 + Vite |
| 编辑器 | md-editor-v3 (CodeMirror 内核) |
| Markdown 渲染 | marked + DOMPurify |
| 主题系统 | CSS 自定义属性 + 内联样式 |
| 构建输出 | 纯静态 HTML/JS/CSS |

## AI 配置

净排支持 OpenAI 兼容格式的 AI API。在设置面板中填入你的 API Key 即可启用 AI 写作辅助。

**推荐方案：** 使用 [OpenRouter](https://openrouter.ai/)（CORS 友好，无需代理）。

内置预设：
- **DeepSeek**（默认）— `https://api.deepseek.com`
- **OpenAI** — `https://api.openai.com/v1`
- **OpenRouter** — `https://openrouter.ai/api/v1`
- **自定义** — 任意 OpenAI 兼容端点

> AI 请求由浏览器直接发起，净排不经过任何中间服务器。

## 隐私承诺

- 不设后端服务器，不收集任何用户数据
- 文章草稿存于浏览器 `localStorage`
- API Key 存于本地，仅从浏览器直连 AI 厂商
- 配图/导入/导出等操作均为纯本地处理

## 许可证

MIT
