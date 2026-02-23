我们现在的核心目标是实现一个本地Chrome的命令行控制系统。我们希望完成一个Local Chrome Server，他通过控制Chrome上的插件，做到：
1. 实时获取当前chrome界面截图。
2. 通过执行 JavaScript 来操作浏览器（点击、输入、滚动、提取数据等）。
3. 管理浏览器标签页（打开、关闭、切换等）。

这个Server可能可以以命令行的形式拉起，获取用户命令；也可以以REST API获取命令。大致上，分为几种命令：

1. **JavaScript 执行** (核心功能)
   - 执行任意 JavaScript 代码
   - 点击元素：`document.querySelector('button').click()`
   - 输入文本：`document.querySelector('#input').value = 'text'`
   - 提取数据：`document.title`, `document.body.innerText`
   - 滚动页面：`window.scrollBy(0, 500)`
   - 等待元素：使用 Promise 和 setTimeout

2. **标签页管理**
   - 打开新标签页（url：xxx）
   - 列出所有当前的标签页
   - 关闭某一个标签页
   - 切换到某个标签页
   - 刷新标签页

3. **截图获取**
   - 获取当前页面截图（1280x720 分辨率）
   - 用于视觉反馈和页面状态确认

**核心理念**：所有页面操作都通过 JavaScript 执行完成，不使用基于像素的鼠标/键盘模拟。这种方式更可靠、更快速、更易于调试。

这个Server主要通过chrome浏览器插件和本地浏览器交互。插件使用 TypeScript 实现，参考 reference/AIPex 项目的 Chrome DevTools Protocol (CDP) 集成方式。

在实现的时候，server层用python实现，用uv维护python的环境；插件用typescript实现。

## 实现状态更新 (2025-02-17)

### ✅ 已实现的核心功能

1. **JavaScript 执行系统**
   - 完整的 JavaScript 执行能力（CDP Runtime.evaluate）
   - 支持返回 JSON 序列化结果
   - 支持捕获 console 输出（log, warn, error 等）
   - 返回值验证和错误处理

2. **改进的 CLI 工具**
   - 交互模式支持箭头键编辑（readline集成）
   - 新增 `tabs init/open/close/switch/refresh/list` 命令
   - 修复了命令导入错误和装饰器问题

3. **WebSocket 连接稳定性**
   - 修复了 403 Forbidden 错误
   - 扩展自动重连机制
   - Content script 自动注入

4. **高级标签组管理**
   - **标签组隔离**：受控标签页组织在"OpenBrowser"标签组中，实现视觉隔离
   - **显式会话初始化**：`tabs init <url>` 命令显式启动控制会话
   - **过滤标签列表**：`tabs list` 在会话初始化后只显示受控标签页
   - **向后兼容性**：未初始化时显示所有标签页并标记管理状态
   - **状态可视化**：标签组标题显示实时状态（🔵 活动, ⚪ 空闲, 🔴 断开连接）
   - **MANUS 设计灵感**：参考 MANUS Chrome 插件的标签组隔离概念

### 🔧 技术实现细节

- **扩展架构**：Background script 处理命令，Content script 提供视口信息和图像处理
- **通信协议**：WebSocket 实时双向通信，JSON 命令格式
- **错误处理**：自动恢复机制，详细的调试日志

### 🚀 使用示例

```bash
# 启动服务器
uv run local-chrome-server serve --log-level DEBUG

# 显式初始化控制会话（创建标签组）
uv run chrome-cli tabs init https://example.com

# 交互式控制（支持箭头键编辑）
uv run chrome-cli interactive

# 执行 JavaScript 操作
uv run chrome-cli execute javascript --script "document.querySelector('button').click()"

# 精确控制特定标签页
uv run chrome-cli tabs list
uv run chrome-cli execute javascript --script "document.title" --tab-id <ID>
```

### 📋 设计原则验证

✅ **JavaScript 优先**：所有操作通过 JavaScript 执行，无需 HTML 选择器辅助  
✅ **实时反馈**：截图提供视觉反馈  
✅ **易于调试**：详细的日志和交互式命令行工具  
✅ **稳定性**：边界检查、错误恢复、自动重连机制