# Milkdown 迁移技术规格书（Spec）

> 版本：v1.0 · 日期：2026-07-15 · 状态：**计划评审，尚未执行**
>
> 关联文档：[原始方案草案](./milkdown-migration-plan.md)（2026-07-14）

---

## 0. 安全策略 —— 先读这节

### 为什么需要安全策略

当前项目**没有 git 仓库**，版本管理靠手动 `dist → dist-bak-xxx` 重命名。这不是问题（项目本来就是单文件组件，够用），但 Milkdown 迁移涉及核心编辑器替换，一旦中途出错，手动找回原始状态会很痛苦。

### 三步安全网

```
第 1 层：全量备份         第 2 层：增量检查点        第 3 层：即时回滚
┌──────────────┐       ┌──────────────┐         ┌──────────────┐
│ 启动前拷贝整  │  →   │ 每个 Phase 完  │  →    │ 任何阶段失败  │
│ 个项目到备份  │       │ 成后，npm run   │       │ → 删除工作目  │
│ 目录，确保有  │       │ build 成功才继  │       │   录，拷回备  │
│ 一份"干净底片"│       │ 续，不成功不进  │       │   份，恢复原  │
│              │       │ 下一阶段        │       │   状          │
└──────────────┘       └──────────────┘         └──────────────┘
```

**具体操作**：
- 备份目录命名：`公众号排版工具-v0.8.2-bak`（放入同级的 `WorkBuddy` 目录下）
- 每个 Phase 结束后执行 `npm run build`，构建不报错且零 warning 才进入下一 Phase
- 如果构建失败 3 次以上或出现难以排查的运行时异常 → 回滚

### 为什么不选 git

你之前的习惯是 `dist → dist-xxx` 手动备份，简单直接。为了一个迁移任务引入 git 工作流反而增加认知负担。备份目录 + 构建检查点足够安全。如果将来需要 git，另行设置。

---

## 一、背景与动机（为什么做这个迁移）

### 当前痛点

净排 v0.8.2 使用 `md-editor-v3`（底层是 CodeMirror 纯文本编辑器），用户看到的是 Markdown 源码：

```
编辑器显示：                   预览面板显示：
# 标题                       标题（大字号紫色）
::: cover                     ═══════════════
点击编辑文字                   点击编辑文字
:::                           ═══════════════
```

用户在脑子里做"源码 → 效果"的翻译。自定义语法 `::: cover` 在编辑器里是灰色纯文本（无任何视觉提示），体验割裂。

### 迁移目标

把净排变成**国内唯一一个纯本地、不登录、所见即所得的公众号排版工具**。

### 为什么选 Milkdown 而不是其他方案

| 方案 | 为什么否决 |
|------|-----------|
| 给 md-editor-v3 加自定义语法高亮 | 它的底层 CodeMirror 是纯文本编辑器，永远不会渲染成 WYSIWYG 效果，换什么配置都解决不了核心问题 |
| TipTap (Vue) | 也是 ProseMirror 封装，但 Markdown 导入/导出需额外处理，生态不如 Milkdown 对 Markdown 原生友好 |
| Milkdown | **专门为 Markdown WYSIWYG 设计**，底层同是 ProseMirror，自带 Markdown 往返能力（`getMarkdown()`），与我们"管道不变"的策略完美契合 |

### 为什么用"换编辑器，保管线"策略

净排的核心价值在**管线**（buildHtml → DOMPurify → 微信复制），不在编辑器。这个策略把迁移风险限制在编辑体验层，不动复制管线。Milkdown 的 `getMarkdown()` 输出标准 Markdown 喂给 `buildHtml()`，同一个函数、同一份 THEMES 数据、同一个 DOMPurify，复制到微信效果完全一样。

---

## 二、迁移流程总览

```
┌─ Phase 0 ─────┐   ┌─ Phase 1 ─────┐   ┌─ 检查点 1 ─┐
│ 备份 + POC    │ → │ 编辑器替换    │ → │ build通过? │
│ 验证3个核心   │   │ 保留预览面板  │   └──────┬─────┘
│ 假设          │   │ 作为对照工具  │          │ ✅继续
└───────────────┘   └───────────────┘          │ ❌修/回滚
                                               ↓
┌─ Phase 2 ─────┐   ┌─ 检查点 2 ─┐   ┌─ Phase 3 ─────┐
│ 工具栏适配    │ → │ build通过? │ → │ 移除预览面板  │
│ 装饰/AI/导入  │   │ 功能回归?  │   │ 布局简化      │
└───────────────┘   └──────┬─────┘   └───────────────┘
                           │ ✅继续
                           │ ❌修/回滚
                           ↓
                    ┌─ 检查点 3 ─┐
                    │ 完整验收    │
                    │ v0.9.0 ✅  │
                    └────────────┘
```

**关键设计决策：Phase 1 保留预览面板**

原始计划建议"Phase 1 + Phase 4 一起做"（替换编辑器同时删掉预览面板）。我改成了**先替换编辑器但保留预览面板**。

为什么？因为这样预览面板就成了一个**对照验证工具**：左边 Milkdown 编辑器是 WYSIWYG 渲染，右边预览面板是 buildHtml 输出，你可以逐行对比两者的差异。发现不一致就知道是 themeToCss 的问题。把对照工具删了再排查问题等于蒙着眼调色。

---

## 三、Phase 0：安全备份 + POC 验证（预计 30 分钟）

### 做什么

**Step 0A — 全量备份：**
```bash
# 执行前确认 vite build 能通过
npm run build

# 备份整个项目
cp -r "公众号排版工具" "公众号排版工具-v0.8.2-bak"

# 验证备份完整性
diff -rq "公众号排版工具" "公众号排版工具-v0.8.2-bak"
```

**Step 0B — POC 验证（在备份外做，不影响原项目）：**

在临时目录做 3 个最小验证，确认 Milkdown 能满足净排的核心需求，**再决定是否执行迁移**。

需要验证的 3 个假设：

| # | 假设 | 验证方法 | 通过标准 |
|---|------|---------|---------|
| H1 | `::: container` 语法往返正常 | 在 Milkdown 中输入 `::: cover\n标题\n:::`，调用 `getMarkdown()`，对比输入输出 | 输出与输入字符完全一致（含换行） |
| H2 | 中文输入法兼容 | 用搜狗/微软拼音在编辑器内输入一段中文，含换行和格式 | 候选框位置不跳动、确认后光标不偏移 |
| H3 | 主题 CSS 可注入 | 写一个最小 `themeToCss()`，把 `h1: 'font-size:24px;color:#534AB7'` 转为 CSS 注入 `.milkdown` 容器 | h1 渲染效果与 buildHtml 对比肉眼一致 |

### 为什么先做 POC

这是整个迁移的**唯一一次免费试错机会**。在临时目录做验证，不碰项目代码。如果任何一个假设失败，直接放弃迁移方案，零损失。

### 失败处理

- H1 失败 → 放弃或引入 remark-directive 插件处理 `:::`
- H2 失败 → 测试不同 Milkdown 版本（v7.15 → v7.19），若均失败则放弃
- H3 失败 → 调整 themeToCss 实现直到匹配，这是可修的问题

### 不可跳过的理由

如果跳过 POC 直接改 App.vue，H1 失败意味着已经改了上百行代码才发现路线走不通，白费功夫。

---

## 四、Phase 1：编辑器替换（预计 2-3 小时）

### 前置条件：Phase 0 全部假设通过

### 做什么

**改动范围：**

| 文件 | 改动 | 说明 |
|------|------|------|
| `package.json` | 依赖变更 | 删 `md-editor-v3`，加 `@milkdown/kit` + `@milkdown/vue` |
| `src/App.vue` | import + 模板 + 逻辑 | 核心改动，详见下方 |
| `vite.config.js` | 可能不需改 | Milkdown 是纯 ESM，Vite 原生支持 |

**App.vue 改动明细：**

```diff
# <script setup> 变化：
- import { MdEditor } from 'md-editor-v3'
- import 'md-editor-v3/lib/style.css'
+ import { Editor, rootCtx, defaultValueCtx, editorViewCtx } from '@milkdown/kit/core'
+ import { commonmark } from '@milkdown/kit/preset/commonmark'
+ import { gfm } from '@milkdown/kit/preset/gfm'
+ import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/vue'
+# 不引入 @milkdown/theme-nord（冲突风险，我们用自写主题 CSS）

# <template> 变化：
  <!-- 原 MdEditor（L476-481）替换为 -->
- <MdEditor ref="editorRef" v-model="markdownText" ... />
+ <MilkdownProvider>
+   <MilkdownVue />
+ </MilkdownProvider>

# 新增函数：
+ const themeToCss = (themeKey) => { ... }  // THEMES 数据 → CSS 规则字符串
+ const injectThemeCss = () => { ... }       // 注入到 .milkdown 内容区

# 双向数据绑定改造：
  // 原：v-model="markdownText"（MdEditor 原生支持）
  // 新：Milkdown onChange → markdownText.value = getMarkdown()
  //    外部写入 → editor.action(replaceAll(md))
```

**预览面板暂不删除：**
- 保留 L421-462 的 `.preview-section` 和 `.phone-frame`
- 保留 L596 的 `previewHtml` 和 L524 的 `showPreview`
- 保留 L1141-1149 的 `renderHtml()` 逻辑

### 为什么保留预览面板

预览面板此时的作用从"给用户看的"变成"给你（开发者）看的对照工具"。你可以同时看到 Milkdown 的 WYSIWYG 渲染和 buildHtml 的输出，逐元素对比差异。等确认两个渲染一致后再删。

### 为什么自写主题 CSS 而不是用 @milkdown/theme-nord

1. nord 有自己的 h1-h6/p/blockquote 样式，会和你的 10 套主题冲突
2. 用 `themeToCss` 直接从 THEMES 对象生成 CSS，确保和 buildHtml 的同源一致
3. 少一个依赖，少一个版本冲突点

### 成功标准

1. `npm run build` 零错误
2. 在浏览器中打开：Milkdown 编辑器正常显示，可以输入 Markdown 并渲染为 WYSIWYG
3. 打开预览面板：预览面板的渲染结果（buildHtml）与编辑器内的 WYSIWYG 渲染**肉眼一致**（至少 h1/h2/p/blockquote/列表的颜色、字号、间距一致）
4. `::: cover` 语法输入后，`getMarkdown()` 能原样输出（验证 POC 结论在生产代码中仍然成立）
5. 复制 HTML 到微信：格式与 v0.8.2 一致

### 失败处理

- 编辑器无法初始化 → 检查 Milkdown 版本、Vue 插件注册方式
- WYSIWYG 与预览不一致 → 调 themeToCss，增加 CSS reset 覆盖
- 构建报错 → 排查 ESM/CJS 兼容问题

如果 3 次修复仍不能通过全部成功标准 → **回滚到备份**。

---

## 五、Phase 2：工具栏适配（预计 1-2 小时）

### 前置条件：Phase 1 全部成功标准通过

### 做什么

把 4 个直接操作编辑器文本的函数从"操作 textarea/ref"改为"操作 Milkdown editor"：

| 函数 | 原实现 | 新实现 | 为什么 |
|------|--------|--------|--------|
| `insertDecorBlock()` (L1288) | 操作 `editorRef.$el.querySelector('textarea').selectionStart` | 获取当前光标位置 → 用 `editor.action(insert(content))` | Milkdown 没有 textarea，用 ProseMirror 的事务插入 |
| `insertImageByUrl()` (L1315) | `markdownText.value += '![](url)'` 追加到末尾 | `editor.action(insert('![](url)'))` 插入到光标处 | 修复旧行为（只能追加到末尾），同时适配新编辑器 |
| `callAI()` 和 AI 写入 (L1475) | `markdownText.value = result` 全量替换 | `editor.action(replaceAll(result))` | Milkdown 不能直接赋值 ref 来更新内容 |
| 导入提纯 `doImport()` | 同 AI 写入 | 同 AI 写入 | 同上 |
| `clearInlineStyles()` (L87) | 操作 `markdownText.value`，正则 strip style/class | 先 `getMarkdown()` 再 strip 再 `replaceAll()` | 操作对象从 DOM 变成文本流 |

### 为什么 Phase 2 放在 Phase 1 之后

这些操作的改动都依赖 Milkdown 已经正确初始化。先把编辑器换上去、确认没问题了，再一个一个适配工具栏函数，出问题时排查范围极小。

### 成功标准

1. `npm run build` 零错误
2. 点击"封面卡片"按钮 → 编辑器光标处正确插入 `::: cover` 容器语法
3. 点击"分割线"按钮 → 插入 `::: divider`
4. 点击"金句卡片"按钮 → 插入 `::: quote`
5. 粘贴图片 URL → 编辑器内插入 `![](url)`
6. AI 生成标题 → 结果替换编辑器内容（光标在文末）
7. 导入提纯 → 结果替换编辑器内容
8. 清除内联样式 → 正常工作

### 失败处理

- 单个函数失败 → 只回滚该函数，其他函数的改动不受影响
- 多个函数均失败 → 检查 editor 实例的上下文注入方式，可能是 editorRef 未正确绑定

---

## 六、Phase 3：移除预览面板（预计 30 分钟）

### 前置条件：Phase 2 全部通过，且 Phase 1 成功标准 #3（WYSIWYG = preview）在多次使用中持续成立

### 做什么

删除所有预览面板相关的代码和 CSS：

**模板删除（~60行）：**
- `.preview-section` 整个 `<section>`（L423-462）
- `.resize-handle` 拖拽分隔线（L465-471）
- 手机框内的预览切换 segment（L429-441）
- `phone-content` 的 `v-html="previewHtml"` 绑定（L459）
- 移动端预览浮钮 `mobile-preview-fab`（L497-499）

**脚本删除 / 简化（~50行）：**
- `showPreview` ref（L524）
- `previewPosition` ref（L525）
- `previewWidth` ref + 拖拽逻辑 `startResize/onResize/stopResize`（L540-590）
- `previewHtml` ref + `renderHtml()`（L596, L1141-1149）
- settings 持久化中 `previewPosition`/`showPreview` 字段（L631-634, L672-675）
- `watch` 中 preview 相关的 watch（L1604）
- 移动端预览切换逻辑（L1613）

**CSS 删除（~70行）：**
- `.preview-section` 全家桶
- `.phone-frame` / `.phone-topbar` / `.phone-status` / `.phone-content`
- `.resize-handle` 及其伪元素
- `.preview-segment` / `.preview-btn`
- 响应式预览面板覆盖样式

**模板简化：**
- `.main-content` 的 `:class` 绑定去掉 `preview-left` / `preview-hidden`
- 工具栏的预览按钮改为无操作或直接改为别用

### 为什么放在最后

只有前面所有阶段都确认稳定后，预览面板才完成历史使命。在此之前它是你的安全对照工具——不要过早删掉你的对照仪。

### 成功标准

1. `npm run build` 零错误
2. 页面只显示工具栏 + Milkdown 编辑器（在手机框内），无预览面板
3. 桌面端和移动端布局正常、无空白区域、无布局错乱
4. 复制 HTML / 导出功能正常

### 失败处理

手动回滚 App.vue 的预览面板相关改动（改动集中、容易定位）。

---

## 附录 A：回滚操作手册

### 完全回滚（任何阶段）

```bash
# 1. 删除当前工作目录
rm -rf "公众号排版工具"

# 2. 从备份恢复
cp -r "公众号排版工具-v0.8.2-bak" "公众号排版工具"

# 3. 验证恢复
cd 公众号排版工具 && npm run build
```

### 部分回滚（某个 Phase 失败）

方案一：回滚 App.vue —— 如果你在修改过程中保留了修改前的 App.vue 副本（建议每个 Phase 前手动 `cp src/App.vue src/App.vue.bak`）。

方案二：回滚整个项目 —— 如果改动散落多处不好定位，直接用完全回滚。

### 不建议的回滚方式

- 不要靠记忆手动改回来（人脑不可靠）
- 不要靠旧 dist 目录恢复源码（dist 是构建产物，不能反向恢复 Vue 源码）

---

## 附录 B：依赖变更清单

### 删除

```json
"md-editor-v3": "^4.14.0"
```

### 新增

```json
"@milkdown/kit": "^7.19.1",
"@milkdown/vue": "^7.19.1"
```

### 保留不变

```json
"vue": "^3.4.30",
"marked": "^18.0.5",
"dompurify": "^3.1.5",
"turndown": "^7.2.4",
"@vitejs/plugin-vue": "^5.0.5",
"vite": "^5.3.3"
```

### 为什么不装 @milkdown/theme-nord

见 Phase 1「为什么自写主题 CSS」。不需要，反而添乱。

---

## 附录 C：每阶段验收清单

### Phase 0 验收

- [ ] `公众号排版工具-v0.8.2-bak` 目录存在且 files 与源目录完全一致
- [ ] POC 项目：`::: cover` 语法 getMarkdown 往返正常
- [ ] POC 项目：中文输入不跳光标
- [ ] POC 项目：themeToCss 注入后 h1 渲染与 buildHtml 肉眼一致

### Phase 1 验收

- [ ] `npm run build` 零错误零 warning
- [ ] 浏览器：编辑器正常启动，可输入 Markdown
- [ ] 浏览器：WYSIWYG 渲染与预览面板 buildHtml 输出肉眼一致
- [ ] 浏览器：`::: cover` / `::: divider` / `::: quote` 语法 getMarkdown 往返正常
- [ ] 浏览器：复制 HTML → 粘贴到微信，格式与 v0.8.2 一致

### Phase 2 验收

- [ ] `npm run build` 零错误
- [ ] 封面卡片按钮 → 光标处正确插入
- [ ] 分割线按钮 → 插入 `::: divider`
- [ ] 金句卡片按钮 → 插入 `::: quote`
- [ ] 粘贴图片 URL → 插入正确
- [ ] AI 生成 → 编辑器内容更新
- [ ] 导入提纯 → 编辑器内容更新
- [ ] 清除样式 → 正常工作

### Phase 3 验收

- [ ] `npm run build` 零错误
- [ ] 页面无预览面板残留
- [ ] 桌面端 / 移动端布局正常
- [ ] 复制 / 导出功能正常
- [ ] 所有之前正常的功能回归正常
