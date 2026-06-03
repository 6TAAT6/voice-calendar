# ===== DeepSeek 语义解析模块 =====
# 把用户说的自然语言，解析成结构化的日程数据
#
# 输入： "明天下午三点开产品评审会"
# 输出： { title: "产品评审会", event_time: "2026-06-04T15:00:00", event_type: "会议" }
#
# 工作原理：
#   1. 把用户说的话拼进一段提示词（prompt）
#   2. 发给 DeepSeek 大模型
#   3. DeepSeek 理解语言 → 返回结构化 JSON
#   4. 我们解析 JSON → 直接存数据库

import json
import re
import httpx
from config import DEEPSEEK, DEEPSEEK_API_URL


# ══════════════════════════════════════════════════
# 系统提示词（System Prompt）— 告诉 DeepSeek 它的角色和规则
# ══════════════════════════════════════════════════
SYSTEM_PROMPT = """你是一个智能日程解析助手。用户会用中文口语描述日程安排，你需要将其解析为结构化的 JSON。

规则：
1. 提取标题（title）：事件的核心内容，如"开会""跑步""生日聚会"
2. 提取时间（event_time）：ISO 8601 格式 yyyy-MM-ddTHH:mm:ss
   - "明天下午三点" → 今天的日期+1天，时间15:00:00
   - "下周五上午十点" → 计算下周该天的日期，时间10:00:00
   - "后天晚上八点半" → 今天+2天，时间20:30:00
   - 如果没说明具体时间，默认为 09:00:00
   - 如果没说明日期，默认为明天
3. 提取类型（event_type）：会议/运动/生日/约会/提醒/购物/就医/旅行/学习/其他
4. 提取备注（description）：除了标题和时间以外的补充信息
5. 判断是否需要提醒（remind）：大多数情况设为 true
6. 识别重复规则（recurrence）：
   - "每天早上跑步" → recurrence: "daily"
   - "每周一开会" → recurrence: "weekly"
   - "每月1号发工资" → recurrence: "monthly"
   - 没有重复描述 → recurrence: "none"

你必须只返回一个合法的 JSON 对象，不要包含任何其他文字：
{
  "title": "事件标题",
  "event_time": "yyyy-MM-ddTHH:mm:ss",
  "event_type": "类型",
  "description": "备注",
  "remind": true,
  "recurrence": "none"
}

当前日期时间：{current_datetime}"""


def build_user_prompt(user_text: str) -> str:
    """构造发给 DeepSeek 的用户消息"""
    return f"请解析以下日程描述：{user_text}"


async def parse_schedule(user_text: str, current_datetime: str = "") -> dict:
    """用 DeepSeek 解析用户的语音文字

    Args:
        user_text: 用户说的话，如 "明天下午三点开产品评审会"
        current_datetime: 当前日期时间，用于计算相对时间

    Returns:
        {
            "title": "产品评审会",
            "event_time": "2026-06-04T15:00:00",
            "event_type": "会议",
            "description": "产品评审",
            "remind": true
        }

    Raises:
        Exception: 解析失败时抛出
    """
    api_key = DEEPSEEK["api_key"]
    model = DEEPSEEK["model"]

    # 检查是否已配置
    if not api_key:
        raise Exception("请先在 backend/.env 中配置 DEEPSEEK_API_KEY（参考 .env.example）")

    # 构造消息列表
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.replace("{current_datetime}", current_datetime),
        },
        {
            "role": "user",
            "content": build_user_prompt(user_text),
        },
    ]

    # 调用 DeepSeek API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,     # 低温度 → 输出更稳定、更可预测
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=body,
        )

    if response.status_code != 200:
        raise Exception(f"DeepSeek API 错误 (HTTP {response.status_code}): {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # 清理 DeepSeek 返回的内容，提取 JSON
    # DeepSeek 可能返回 ```json {...} ``` 包装的内容
    # 也可能返回纯 JSON 文本
    content = content.strip()

    # 去掉 markdown 代码块标记
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    # 解析 JSON
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise Exception(f"DeepSeek 返回内容无法解析为 JSON: {content}")

    # 校验必填字段
    if "title" not in parsed or "event_time" not in parsed:
        raise Exception(f"DeepSeek 返回的 JSON 缺少必填字段: {parsed}")

    return parsed


# ══════════════════════════════════════════════════
# AI 对话修正 — "不对，改成xxx"
# ══════════════════════════════════════════════════

CORRECT_PROMPT = """你是一个智能日程修正助手。用户之前说了一段日程描述，然后又说了一段修正指令。

你的任务：
1. 理解用户的修正意图（比如"改成后天"、"不是开会是吃饭"、"时间改成上午"等）
2. 把修正应用到原始描述上，得出最终的正确日程
3. 输出修正后的结构化 JSON

原始描述：{original_text}
修正指令：{correction_text}

规则和 parse_schedule 一样：
- 提取 title、event_time（ISO 8601）、event_type、description、remind
- 只返回 JSON，不要其他文字

当前日期时间：{current_datetime}"""


async def nlp_correct(
    original_text: str,
    correction_text: str,
    current_datetime: str = "",
) -> dict:
    """AI 对话修正：理解用户说的"不对，改成xxx"，合并到原始日程

    Args:
        original_text: 第一次识别/解析的文字
        correction_text: 用户修正说的话
        current_datetime: 当前日期时间

    Returns:
        修正后的结构化日程
    """
    api_key = DEEPSEEK["api_key"]
    model = DEEPSEEK["model"]

    if not api_key:
        raise Exception("请先在 backend/.env 中配置 DEEPSEEK_API_KEY（参考 .env.example）")

    messages = [
        {
            "role": "system",
            "content": CORRECT_PROMPT.format(
                original_text=original_text,
                correction_text=correction_text,
                current_datetime=current_datetime,
            ),
        },
        {
            "role": "user",
            "content": "请输出修正后的日程 JSON。",
        },
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"DeepSeek API 错误 (HTTP {response.status_code}): {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()

    # 去掉 markdown 代码块
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise Exception(f"DeepSeek 修正结果无法解析为 JSON: {content}")

    if "title" not in parsed or "event_time" not in parsed:
        raise Exception(f"修正结果缺少必填字段: {parsed}")

    return parsed
