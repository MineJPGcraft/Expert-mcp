"""
这是一个专家MCP！可以让偷懒的坏模型发挥接近Claude的能力！
"""

import json
import logging
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

# 这里是日志输出
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("mcp-advisor")

# 加载config.json
CONFIG_PATH = os.environ.get("MCP_CONFIG", "config.json")
config_file = Path(CONFIG_PATH)
if not config_file.exists():
    logger.error(f"找不到配置文件！: {config_file.resolve()}")
    sys.exit(1)

with config_file.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

UP = CONFIG["upstream"]
HOST = CONFIG.get("host", "0.0.0.0")
PORT = int(CONFIG.get("port", 8765))

UPSTREAM_MODEL = UP["model"]
UPSTREAM_BASE = UP["base_url"]
UPSTREAM_KEY = UP["api_key"]
TEMPERATURE = float(UP.get("temperature", 0.3))
MAX_TOKENS = int(UP.get("max_tokens", 4096))
TIMEOUT = float(UP.get("timeout", 120))
SYSTEM_PROMPT = UP.get(
    "system_prompt",
    "你是一位资深的高级模型，请对用户的问题进行深入、严谨、可执行的分析。",
)

logger.info(f"上游模型: {UPSTREAM_MODEL} @ {UPSTREAM_BASE}")
logger.info(f"MCP 监听: http://{HOST}:{PORT}/mcp")

# 给OpenAI模块传递参数
client = OpenAI(
    api_key=UPSTREAM_KEY,
    base_url=UPSTREAM_BASE,
    timeout=TIMEOUT,
    stream=True
)

# 初始化一个MCP服务器
mcp = FastMCP(
    name="advanced-model-advisor",
    host=HOST,
    port=PORT,
    # Streamable HTTP 默认路径是 /mcp 不要忘记！
)


# 给模型提供可以偷懒的工具
@mcp.tool(
    name="consult_advanced_model",
    description=(
        "【高级模型咨询工具】\n"
        "当你遇到自己不确定、需要深度推理、涉及复杂权衡、跨领域知识、关键决策、"
        "高风险代码/架构设计、棘手的数学/算法/调试问题，或者需要二次验证你自己结论时，"
        "请调用本工具向一位『更强的高级模型』寻求专家意见。\n\n"
        "【调用建议】\n"
        "- 把完整问题、相关背景、你已尝试的思路一起传入，避免信息缺失；\n"
        "- 高级模型的回答仅作为参考意见，你需要结合上下文和用户需求进行最终决策；\n"
        "- 不要把简单问题（如打招呼、纯查询、显而易见的答案）发给本工具，避免浪费；\n"
        "- 一次任务中如多次需要咨询，可分多次调用，每次聚焦一个具体问题。\n\n"
        "【何时务必调用】\n"
        "- 你对答案的把握 < 80%；\n"
        "- 用户明确要求『深度思考 / 严谨分析 / 给出最佳方案』；\n"
        "- 题目涉及多个相互冲突的约束需要权衡；\n"
        "- 需要逐步推理的复杂问题（数学证明、算法设计、系统设计、疑难 bug 等）。"
    ),
)
def consult_advanced_model(
    question: str,
    context: str = "",
    focus: str = "",
) -> str:
    """
    向预先配置好的高级模型请教问题，返回其建议。

    参数:
        question: 你想咨询的核心问题（必填，尽量完整、清晰）。
        context: 相关背景信息，例如代码片段、用户原始需求、已知约束、已尝试方案等。
        focus:   你最希望高级模型重点回答/聚焦的方向，例如"请重点对比方案A和方案B的工程可行性"。

    返回:
        高级模型给出的文本意见。
    """
    if not question or not question.strip():
        return "❌ 错误：question 不能为空。请把你想咨询的问题完整地写进来。"

    user_parts = []
    if context.strip():
        user_parts.append(f"## 背景信息\n{context.strip()}")
    user_parts.append(f"## 待咨询的问题\n{question.strip()}")
    if focus.strip():
        user_parts.append(f"## 重点关注\n{focus.strip()}")
    user_content = "\n\n".join(user_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    logger.info(f"→ 咨询高级模型 | question 长度={len(question)} | context 长度={len(context)}")

    try:
        resp = client.chat.completions.create(
            model=UPSTREAM_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        answer = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", None)
        if usage:
            logger.info(
                f"← 完成 | prompt={usage.prompt_tokens} "
                f"completion={usage.completion_tokens} total={usage.total_tokens}"
            )
        else:
            logger.info("← 完成（无 usage 信息）")

        # 在返回内容里附上模型标识，告诉坏模型这是『高级模型的意见』
        return (
            f"【来自高级模型 `{UPSTREAM_MODEL}` 的意见，仅供参考】\n\n"
            f"{answer.strip()}"
        )

    except Exception as e:
        logger.exception("调用高级模型失败")
        return f"❌ 调用高级模型失败：{type(e).__name__}: {e}"


# 启动服务器！
if __name__ == "__main__":
    # 我们使用 Streamable HTTP 传输！
    mcp.run(transport="streamable-http")
