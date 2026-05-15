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

# 不再被锁定

> 原文：[Not so locked in any more](https://simonwillison.net/2026/May/14/not-so-locked-in/)
> 来源：Simon Willison | 2026-05-14
> 作者：Simon Willison

---

Mitchell Hashimoto 关于 Bun 从 Zig 迁移到 Rust 的那条引用，让我想起了上周在一个会议上的类似对话。

我当时在和一个人聊天，他在一家中型科技公司工作，公司有一对 legacy/legendary 的 iPhone 和 Android 应用。

他告诉我，他们刚刚完成了一次由 **coding agent 驱动的重写**——把两个应用都迁移到了 React Native。

我问他们为什么选择这个方案，毕竟 coding agent 理论上降低了维护两套独立 iPhone 和 Android 应用的成本。

他们说 React Native 在过去几年改进了很多，覆盖了他们应用需要做的所有事情。而且……如果这个决定最终是错的，他们将来可以再迁回原生。

正如 Mitchell 所说：

> 编程语言曾经是一种 LOCK IN（锁定），但它们越来越不是了。

---
