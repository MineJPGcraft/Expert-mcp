# 🧠 Expert MCP

> 为你的 AI 模型配备一位"随时可以请教"的高级专家顾问。

当下游模型遇到复杂问题时，可以通过本 MCP 工具将问题转发给预先配置好的高级模型（如 GPT-5.5、Claude Opus 4.7 等），
获取深度分析与专业建议，再结合自身判断给出最终答案。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Streamable%20HTTP-green)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-MineJPGcraft%2FExpert--mcp-181717?logo=github)](https://github.com/MineJPGcraft/Expert-mcp)

---

## ✨ 功能特性

- 🔌 **OpenAI 兼容** — 对接任何 OpenAI 格式的上游端点（OpenAI / DeepSeek / Qwen / vLLM / Ollama 等）
- ⚙️ **配置文件驱动** — 所有参数在 `config.json` 中集中管理，无需改动代码
- 📡 **Streamable HTTP** — 符合 MCP 最新标准的流式 HTTP 传输，端点 `/mcp`
- 🛠️ **丰富的工具提示** — 精心设计的 `description`，引导下游模型在正确时机调用
- 🧩 **三段式入参** — `question`（必填）、`context`（背景）、`focus`（重点方向）
- 📊 **完整日志** — 请求日志 + Token 用量统计，便于监控与排查

---

## 🏗️ 工作原理

```text
┌─────────────────────────────────────────────────────────┐
│                      用户 (User)                         │
└───────────────────────────┬─────────────────────────────┘
                            │ 提问
                            ▼
┌─────────────────────────────────────────────────────────┐
│              下游模型 (Claude / GPT / Qwen …)            │
│                                                         │
│   遇到复杂问题？→ 调用 consult_advanced_model 工具       │
└───────────────────────────┬─────────────────────────────┘
                            │ MCP Streamable HTTP
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Expert MCP Server                     │
│               (本项目 server.py)                        │
└───────────────────────────┬─────────────────────────────┘
                            │ OpenAI API 请求
                            ▼
┌─────────────────────────────────────────────────────────┐
│         上游高级模型 (GPT-5.5、Claude Opus 4.7 …)      │
│                   返回深度分析意见                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/MineJPGcraft/Expert-mcp.git
cd Expert-mcp
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> 推荐使用 Python 3.10+，建议在虚拟环境中安装。

### 3. 编辑配置文件

复制并修改 `config.json`：

```json
{
  "host": "0.0.0.0",
  "port": 8765,
  "upstream": {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxx",
    "model": "gpt-5.5",
    "temperature": 0.3,
    "max_tokens": 4096,
    "timeout": 120,
    "system_prompt": "你是一位顶尖的资深专家顾问，请对问题进行深入、严谨、可执行的分析。"
  }
}
```

配置项说明见下方 [⚙️ 配置参考](#️-配置参考)。

### 4. 启动服务

```bash
python server.py
```

看到如下日志即表示启动成功：

```
2025-xx-xx | INFO    | mcp-advisor | 上游模型: gpt-4o @ https://api.openai.com/v1
2025-xx-xx | INFO    | mcp-advisor | MCP 监听: http://0.0.0.0:8765/mcp
```

MCP 端点地址：

```
http://127.0.0.1:8765/mcp
```

---

## 🔧 客户端接入

在支持 MCP Streamable HTTP 的客户端（Cherry Studio、Cline、Claude Code 等）中添加如下配置：

```json
{
  "mcpServers": {
    "expert-advisor": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

> **远程部署？** 将 `127.0.0.1` 替换为服务器的实际 IP 或域名，并确保防火墙放行对应端口。

---

## ⚙️ 配置参考

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `host` | string | `"0.0.0.0"` | 服务监听地址 |
| `port` | integer | `8765` | 服务监听端口 |
| `upstream.base_url` | string | — | 上游 API 的 base URL（OpenAI 兼容格式） |
| `upstream.api_key` | string | — | 上游 API Key |
| `upstream.model` | string | — | 上游模型名称，如 `gpt-5.5`、`claude-opus-4-7` |
| `upstream.temperature` | float | `0.3` | 生成温度，建议分析类任务保持较低值 |
| `upstream.max_tokens` | integer | `4096` | 单次回复最大 Token 数 |
| `upstream.timeout` | float | `120` | 请求超时秒数 |
| `upstream.system_prompt` | string | 内置默认值 | 高级模型的系统提示词，可完全自定义 |

### 使用环境变量切换配置文件

```bash
MCP_CONFIG=config.prod.json python server.py
```

---

## 🛠️ 工具说明

下游模型可以调用的工具：

### `consult_advanced_model`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `question` | string | ✅ | 待咨询的核心问题，尽量完整清晰 |
| `context` | string | ❌ | 背景信息，如代码片段、用户需求、已尝试方案等 |
| `focus` | string | ❌ | 希望高级模型重点回答的方向 |

**建议调用的场景：**

- 自身把握 < 80% 的问题
- 用户明确要求深度思考 / 严谨分析 / 最佳方案
- 涉及复杂权衡的多约束问题
- 需要逐步推理的数学、算法、系统设计、疑难 Bug
- 需要二次验证自己结论的情况

**不建议调用的场景：**

- 简单问候或纯粹的信息查询
- 答案显而易见的基础问题
- 高频重复的简单任务

---

## 🌐 对接上游服务

只需修改 `config.json` 中的 `upstream` 部分即可对接不同服务商


## 📋 依赖

```text
mcp>=1.2.0
openai>=1.40.0
```

---

## 📄 License

[MIT License](LICENSE) © 2026 [MCJPG](https://github.com/MineJPGcraft)
```
