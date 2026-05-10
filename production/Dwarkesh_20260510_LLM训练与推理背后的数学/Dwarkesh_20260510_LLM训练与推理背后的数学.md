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

# LLM 训练与推理背后的数学

> 原文：[Reiner Pope – The math behind how LLMs are trained and served](https://www.dwarkesh.com/p/reiner-pope)
> 来源：Dwarkesh Podcast | 2026-05-10
> 嘉宾：Reiner Pope（Maddox CEO，前 Google TPU 架构师）

---

## 索引

- [Roofline 分析：推理时间的两个下界](#roofline-分析推理时间的两个下界)
- [延迟与 batch size 的关系](#延迟与-batch-size-的关系)
- [成本与 batch size 的关系](#成本与-batch-size-的关系)
- [最优 batch size 的推导](#最优-batch-size-的推导)
- [稀疏性与 MoE 的收益](#稀疏性与-moe-的收益)
- [MoE 层在 GPU 集群上的布局](#moe-层在-gpu-集群上的布局)
- [Scale-up 与 Scale-out 网络](#scale-up-与-scale-out-网络)
- [Pipeline 并行与 micro-batch](#pipeline-并行与-micro-batch)
- [KV cache 无法被 pipeline 分摊](#kv-cache-无法被-pipeline-分摊)
- [Scale-up 域大小为何重要](#scale-up-域大小为何重要)
- [训练与推理的成本均衡](#训练与推理的成本均衡)
- [从 API 定价反推模型架构](#从-api-定价反推模型架构)
- [KV cache 的存储层级经济学](#kv-cache-的存储层级经济学)
- [上下文长度的天花板](#上下文长度的天花板)
- [神经网络与密码学的结构相似性](#神经网络与密码学的结构相似性)

---

## Roofline 分析：推理时间的两个下界 [02:09]

Reiner 的分析方法很简单：对于一次推理 forward pass，时间的下界由两个因素决定——**内存带宽**和**计算吞吐**，取两者中较大的那个。

计算时间：

> T_compute = batch_size × active_params / FLOPS

内存时间由两部分组成：

> T_mem = (total_params / mem_bandwidth) + (batch_size × context_len × bytes_per_token / mem_bandwidth)

第一项是**权重加载时间**——把所有模型参数从 HBM 读入芯片。第二项是 **KV cache 加载时间**——对 batch 中每个序列，读取其完整上下文的 KV 表示。

注意力计算本身的 FLOPS 相对于权重矩阵乘法很小，可以忽略。这个简单模型已经有很强的预测力。

---

## 延迟与 batch size 的关系 [08:00]

把上面的公式画成 batch size vs. time 的图：

- **T_compute** 是一条从原点出发的直线（线性于 batch size）
- **权重加载** 是一个常数（不依赖 batch size）
- **KV cache 加载** 也是线性于 batch size 的

总时间取 max(T_compute, T_mem_weights + T_mem_kv)。

关键洞察：存在一个**延迟下界**，就是把所有模型参数从 HBM 读一遍的时间。无论 batch size 多小，你都不可能比这更快。在典型硬件上，这个下界大约是 **15-20 毫秒**（HBM 容量 / HBM 带宽）。

Dwarkesh 问：为什么是 20 毫秒？

Reiner 解释：以 Rubin 为例，288 GB / 20 TB/s ≈ 15ms。这个数字在多代 HBM 上都相当稳定。你不会想让一次 forward pass 超过这个时间太多——因为那意味着你在重复读 HBM 里的东西，没有意义。

---

## 成本与 batch size 的关系 [12:54]

延迟图告诉你"一次 forward pass 要多久"，但我们更关心**每个 token 的成本**（= 时间 / batch size）。

把三条曲线都除以 batch size：

- T_compute / B → 常数（不随 batch 变化）
- KV fetch / B → 常数
- 权重加载 / B → **双曲线**（batch 越大越便宜）

结论：

1. **Batch size = 1 时成本趋近无穷**——权重加载没有被分摊
2. **Batch size 足够大时，成本趋近一个下界**——由计算时间决定
3. "Claude Code 慢速模式"不会便宜太多，因为 KV cache 和计算都是 per-sequence 的，无法跨 batch 分摊

---

## 最优 batch size 的推导 [16:11]

令 T_compute = T_mem（忽略 KV 项简化分析），解出：

> batch_size ≈ 300 × sparsity_ratio

其中 300 ≈ FLOPS / mem_bandwidth（在 FP4 下，这个比值在多代 GPU 上都约为 300）。sparsity_ratio = total_params / active_params。

对 DeepSeek（激活 32/256 个 expert）：sparsity ≈ 8，所以最优 batch ≈ 2400。

这意味着你需要约 **2000-3000 个并发序列**才能让 GPU 满载。换算成吞吐：2400 × (1/20ms) ≈ **128k tokens/s** per rack。

Dwarkesh 问：这看起来不多？

Reiner：Gemini 去年公布的全球流量是几亿 tokens/s。所以一个 rack 大约是 Gemini 的千分之一——这其实已经不少了。

---

## 稀疏性与 MoE 的收益 [28:07]

稀疏性越高，active_params 越少，计算成本越低。但代价是什么？

引用 "Unified Laws for Routed Language Models" 论文的结果：保持 active params 不变，增加 expert 数量，模型质量持续提升——但收益递减严重。例如，64 个 expert、370M active params 的模型才等价于 1.3B dense 模型。也就是说 **total params 增加 64 倍才换来 4 倍的 active params 等效质量**。

但从推理经济学看，这仍然是划算的：total params 增加只影响权重加载时间，而权重加载可以被 batch 分摊。只要你有足够多的用户，**稀疏性是纯赢**——一直加到用户不够为止。

唯一的硬约束是**内存容量**：更多 expert 意味着更多参数要存储。

---

## MoE 层在 GPU 集群上的布局 [32:09]

标准做法是 **expert parallelism**：不同 expert 放在不同 GPU 上。

DeepSeek 有 256 个 expert，放在 64 个 GPU 上（一个 Blackwell rack），每个 GPU 存 4 个 expert。Router 决定每个 token 去哪几个 expert，产生 **all-to-all** 通信模式——任意 GPU 可能需要和任意其他 GPU 通信。

Blackwell rack 内部的 NVLink（scale-up 网络）恰好提供了完全连接拓扑：所有 GPU 通过中间的 NV switch 两跳互联。这与 MoE 的 all-to-all 模式完美匹配。

问题出在**跨 rack**：scale-out 网络带宽只有 scale-up 的 **1/8**。如果 MoE 层跨两个 rack，一半 token 需要走慢速网络，成为瓶颈。

---

## Scale-up 与 Scale-out 网络 [36:57]

一个 rack 的物理约束：几米高、一两米宽，受限于供电、重量和散热。内部 GPU 通过 NVLink 连接到中间的 NV switch，形成全连接。离开 rack 则走 scale-out 网络（约 8 倍慢）。

为什么不把 scale-up 域做得更大？

- Hopper → Blackwell（8 → 72 GPU）：主要是产品决策，从 tray 改为 rack 形态
- Blackwell → Rubin（72 → ~500 GPU）：需要更复杂的物理设计来跑更多线缆

限制因素是**线缆密度**——连接器密度、弯曲半径、背板空间。现代 rack 在空间、重量、供电、散热上都推到了物理极限。

---

## Pipeline 并行与 micro-batch [56:56]

Pipeline 并行把不同层放在不同 rack 上。在推理中，它**不改善延迟也不恶化延迟**——只是把工作从一个 rack 移到另一个 rack。好处是减少每个 rack 的内存容量需求。

推理中的 pipeline 很自然：一个 batch 完成第一阶段后立即进入第二阶段，下一个 batch 紧跟着进入第一阶段，没有 bubble。

训练中则有 bubble 问题：forward 和 backward 之间需要同步，产生空闲时间。文献中有 zero-bubble、1F1B 等复杂调度方案。

---

## KV cache 无法被 pipeline 分摊 [01:10:43]

关键推导：pipeline 并行时，全局 batch = micro_batch_count × local_batch_size。micro_batch_count = pipeline_stages。

代入内存公式后发现：

- **权重的 per-GPU 内存** 随 pipeline stages 增加而下降 ✓
- **KV cache 的 per-GPU 内存** 保持不变 ✗

原因：虽然每个 rack 只存部分层的 KV，但为了保持所有 rack 忙碌，同时在飞的序列数也等比增加了。两者精确抵消。

结论：KV cache 既不能跨 batch 分摊（每个序列独有），也不能通过 pipeline 分摊。这是推理中最顽固的内存瓶颈。

---

## Scale-up 域大小为何重要 [01:17:02]

Pipeline 解决了容量问题，但**带宽问题**只能靠更大的 scale-up 域解决。

权重加载时间 = total_params / (scale_up_size × per_GPU_bandwidth)

scale_up 从 8 GPU（Hopper）到 72 GPU（Blackwell）是 **9 倍**的带宽提升，远超单 GPU 带宽的代际增长（~1.5-2x）。这直接降低了推理延迟的下界。

这也解释了为什么模型参数量在 GPT-4 之后停滞了两三年——不是训练做不到更大，而是**推理部署**需要足够大的 scale-up 域才能在合理延迟内服务更大的模型。Blackwell rack 的 10-20 TB 内存终于让 5T 参数模型 + KV cache 成为可能。

---

## 训练与推理的成本均衡 [01:19:00]

启发式原则：当总成本 = 成本A + 成本B 时，最优点往往在两者相等处。

将训练成本分为三部分：

- 预训练：6 × active_params × data_pretrain
- RL：α × active_params × data_RL（α ≈ 2-6，因为 RL 包含低效的 decode）
- 推理：2 × active_params × data_inference

令三者大致相等，可以推出：

1. **推理 token 数 ≈ 预训练 token 数 ≈ RL token 数**（量级相同）
2. 假设 active params ≈ 100B，Chinchilla 最优训练量 ≈ 2T tokens
3. 实际推理量估算：50M tokens/s × 2 个月 ≈ 200T tokens
4. 所以模型被**过训练约 100 倍**（相对 Chinchilla 最优）

这意味着：GPT-5 的预训练 token 数应该和它在生命周期内服务的总 token 数在同一量级。换句话说，**每个前沿模型在其生命周期内应该生成相当于全部人类知识的输出量**。

---

## 从 API 定价反推模型架构 [01:33:04]

**上下文长度定价**：Gemini 3.1 超过 200K context 后贵 50%。这暗示 200K 大约是 KV cache 内存时间追上计算时间的拐点。

由此可以反推 bytes_per_token：

> bytes_per_token = active_params / (300 × context_length) ≈ 100B / (300 × 200K) ≈ 1.7 KB

这与 8 个 KV head × 128 维 × 2 bytes 的配置吻合。API 定价泄露了大量架构信息。

**输入 vs 输出定价**：输出（decode）比输入（prefill）贵约 5 倍。这说明 decode 严重受限于内存带宽——prefill 可以把多个 token 的计算打包在一起，有效分摊了权重加载成本。

---

## KV cache 的存储层级经济学 [01:49:05]

KV cache 有三种"生产"方式，成本递增：

| 方式 | 检索成本 | 持有成本 |
|------|----------|----------|
| 重新计算（rematerialization） | GPU 计算时间 | 0（已删除） |
| 存在 HBM | 0（已就位） | 占用 GPU 内存 |
| 存在 DDR/Flash | DDR→HBM 拷贝时间 | 占用 DDR 容量 |

选择哪个层级取决于**持有时间**。启发式规则：选择"drain time"（容量/带宽）与持有时间匹配的层级。

- HBM drain time ≈ 20ms → 太短，不适合长期存储
- DDR drain time ≈ 1-10 秒
- Flash drain time ≈ 1 分钟
- 机械硬盘 drain time ≈ 1 小时

Gemini 的 cache 定价有两档：5 分钟和 1 小时。这暗示对应的存储层级可能是 **Flash** 和**机械硬盘**——令人惊讶，但从经济学上说得通。

---

## 上下文长度的天花板 [01:52:30]

为什么所有模型都停在 100K-200K context？

- 计算成本随 context 增长很慢（attention 的二次项斜率极低，要到百万 token 才明显）
- 真正的瓶颈是 **KV cache 的内存带宽和容量**

Sparse attention 能帮忙（DeepSeek 的方案把线性项变成平方根），但不是无限改善——太稀疏会丢质量。

Reiner 的判断：**看不到突破内存墙的好路径**。HBM 带宽就在那里，不会大幅改善。这意味着 Dario 说的"不需要持续学习，in-context learning 就够"如果成立，需要某种根本性的架构变革才能实现百万级 context。

---

## 神经网络与密码学的结构相似性 [02:04:03]

Reiner 有一篇博文讨论了这个有趣的类比：

**相似点**：两者都需要在所有输入之间"搅拌"信息。密码学是为了让输出看起来像随机噪声；神经网络是为了从看似随机的数据中提取结构。机制相似，目标相反。

**差分密码分析 vs 梯度下降**：密码学中最强的攻击之一是对密码做"微分"——看输入的微小变化如何影响输出。好的密码要让这个影响尽可能大（雪崩效应）。神经网络则相反——residual connection 和 layer norm 都是为了让梯度保持可控。

**Feistel 网络 → RevNets**：密码学中的 Feistel 构造（用不可逆函数构建可逆函数）被直接移植到了神经网络。RevNets（2017-18）用这个构造让整个 transformer 可逆——forward pass 之后可以从输出完美重建所有中间激活，省去了训练时存储激活的内存开销。代价是多花一倍计算。

这是"花计算换内存"的又一个例子——与 KV cache（花内存换计算）恰好相反。
