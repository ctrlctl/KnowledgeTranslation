<style>
body, .markdown-body {
  font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif;
  font-size: 15px;
  line-height: 2;
  max-width: 38em;
  margin: 0 auto;
  padding: 2em;
  color: #2c2c2c;
  background: #faf8f5;
}
</style>

> 原文：[Beyond permission prompts: making Claude Code more secure and autonomous](https://www.anthropic.com/engineering/claude-code-sandboxing)
> 来源：Anthropic Engineering | 2025-10-20
> 作者：David Dworken, Oliver Weller-Davies 等

## 索引

- [问题：权限疲劳](#问题权限疲劳)
- [沙箱方案](#沙箱方案)
- [沙箱化 Bash 工具](#沙箱化-bash-工具)
- [Claude Code on the Web](#claude-code-on-the-web)

---

## 问题：权限疲劳

Claude Code 运行在基于权限的模型上：默认只读，修改文件或运行命令前都要请求权限。虽然 `echo` 或 `cat` 等安全命令会自动放行，但大多数操作仍需显式批准。

不断点击"approve"会拖慢开发节奏，还会导致**权限疲劳**（approval fatigue）——用户不再仔细审查批准的内容，反而让开发变得更不安全。

---

## 沙箱方案

沙箱（sandboxing）创建预定义的边界，让 Claude 在边界内自由工作，而不是每个动作都请求权限。启用沙箱后，权限弹窗大幅减少，安全性反而提升。

内部使用中，沙箱**安全地减少了 84% 的权限弹窗**。

沙箱基于操作系统级特性，实现两个边界：

- **文件系统隔离**（Filesystem isolation）：确保 Claude 只能访问或修改特定目录。这对防止被 prompt injection 攻击的 Claude 修改敏感系统文件尤为重要。

- **网络隔离**（Network isolation）：确保 Claude 只能连接到批准的服务器。这防止被攻击的 Claude 泄露敏感信息或下载恶意软件。

有效的沙箱**必须同时具备两者**。没有网络隔离，被攻陷的 agent 可以窃取 SSH 密钥等敏感文件；没有文件系统隔离，被攻陷的 agent 可以轻松逃逸沙箱获取网络访问。两种技术结合才能提供更安全、更快的 agentic 体验。

---

## 沙箱化 Bash 工具

新的沙箱运行时（beta 研究预览）让你精确定义 agent 可以访问哪些目录和网络主机，无需启动和管理容器。可用于沙箱化任意进程、agent 和 MCP server，并已开源。

在 Claude Code 中，这个运行时用于沙箱化 bash 工具，让 Claude 在你设定的限制内运行命令。在安全沙箱内，Claude 可以更自主地执行命令而无需权限弹窗。如果 Claude 尝试访问沙箱外的内容，你会立即收到通知，可以选择是否允许。

技术实现基于 OS 级原语：Linux 的 bubblewrap 和 macOS 的 seatbelt，在操作系统层面强制执行限制。覆盖范围不仅是 Claude Code 的直接交互，还包括命令生成的任何脚本、程序或子进程。

具体执行：

- **文件系统隔离**：允许对当前工作目录的读写访问，但阻止修改其外的任何文件。
- **网络隔离**：只允许通过连接到沙箱外代理服务器的 Unix domain socket 访问互联网。代理服务器对进程可连接的域名强制执行限制，并处理新请求域名的用户确认。支持自定义代理以对出站流量执行任意规则。

两个组件都可配置：可以轻松选择允许或禁止特定文件路径或域名。

沙箱确保即使 prompt injection 成功，也被**完全隔离**，不会影响整体用户安全。被攻陷的 Claude Code 无法窃取你的 SSH 密钥，也无法向攻击者的服务器回传数据。

---

## Claude Code on the Web

Claude Code on the Web 让用户在云端的隔离沙箱中运行 Claude Code。每个会话在隔离沙箱中执行，Claude 对其服务器有完全访问权限，但以安全方式运行。

关键设计：**敏感凭证（如 git 凭证或签名密钥）永远不在沙箱内与 Claude Code 共存**。即使沙箱内运行的代码被攻陷，用户也不会受到进一步伤害。

Git 集成使用自定义代理服务：

1. 沙箱内的 git 客户端用自定义构建的 scoped credential 向代理服务认证
2. 代理验证凭证和 git 交互内容（如确保只推送到配置的分支）
3. 然后附加正确的认证 token 再将请求发送到 GitHub

这样实现了安全的版本控制工作流，同时防止未授权推送。
