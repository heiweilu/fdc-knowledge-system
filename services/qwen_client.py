import base64
import json
import httpx
from typing import AsyncGenerator
from openai import OpenAI
from config import DASHSCOPE_API_KEY, QWEN_BASE_URL, MODEL_OMNI, MODEL_TEXT, MODEL_IMAGE_GEN, SYSTEM_PROMPT, IMAGE_PROMPTS


def _get_client() -> OpenAI:
    return OpenAI(api_key=DASHSCOPE_API_KEY, base_url=QWEN_BASE_URL)


def chat_stream(messages: list[dict], knowledge_context: str = "", enable_search: bool = False) -> AsyncGenerator[str, None]:
    """纯文本对话，流式返回。支持 qwen3.6-plus 的 thinking 模式。"""
    client = _get_client()

    system_msg = SYSTEM_PROMPT
    if knowledge_context:
        system_msg += f"\n\n【相关知识库参考资料】\n{knowledge_context}"

    full_messages = [{"role": "system", "content": system_msg}] + messages

    extra_body = {"enable_thinking": True}
    if enable_search:
        extra_body["enable_search"] = True

    completion = client.chat.completions.create(
        model=MODEL_TEXT,
        messages=full_messages,
        max_tokens=30000,
        stream=True,
        stream_options={"include_usage": True},
        extra_body=extra_body,
    )

    for chunk in completion:
        if chunk.choices:
            delta = chunk.choices[0].delta
            # 思考内容（reasoning_content）
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield json.dumps({"thinking": reasoning}, ensure_ascii=False)
                continue
            if delta.content:
                yield delta.content
        if hasattr(chunk, "usage") and chunk.usage:
            yield f"\n\n<!-- tokens: prompt={chunk.usage.prompt_tokens}, completion={chunk.usage.completion_tokens}, total={chunk.usage.total_tokens} -->"


def analyze_image_stream(
    images: list[str],
    user_text: str = "",
    analysis_type: str = "general",
    knowledge_context: str = "",
) -> AsyncGenerator[str, None]:
    """图片分析（支持多张），流式返回文本，支持 thinking 模式。"""
    client = _get_client()

    prompt_template = IMAGE_PROMPTS.get(analysis_type, IMAGE_PROMPTS["general"])
    user_prompt = prompt_template
    if user_text:
        user_prompt = f"{user_text}\n\n{prompt_template}"

    system_msg = SYSTEM_PROMPT
    if knowledge_context:
        system_msg += f"\n\n【相关知识库参考资料】\n{knowledge_context}"

    # 构建多图内容：先所有图，最后放文字
    content = []
    for b64 in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })
    content.append({"type": "text", "text": user_prompt})

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": content},
    ]

    completion = client.chat.completions.create(
        model=MODEL_OMNI,
        messages=messages,
        max_tokens=30000,
        stream=True,
        stream_options={"include_usage": True},
        extra_body={"enable_thinking": True},
    )

    for chunk in completion:
        if chunk.choices:
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield json.dumps({"thinking": reasoning}, ensure_ascii=False)
                continue
            if hasattr(delta, "content") and delta.content:
                yield delta.content
        if hasattr(chunk, "usage") and chunk.usage:
            yield f"\n\n<!-- tokens: prompt={chunk.usage.prompt_tokens}, completion={chunk.usage.completion_tokens}, total={chunk.usage.total_tokens} -->"


def generate_image(prompt: str, n: int = 1) -> list[str]:
    """使用 wan2.7-image 生成图像，返回图片URL列表。"""
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": MODEL_IMAGE_GEN,
        "input": {
            "messages": [{"role": "user", "content": [{"text": prompt}]}]
        },
        "parameters": {
            "result_format": "message",
            "n": n,
            "size": "1024*1024",
            "watermark": False,
        },
    }
    with httpx.Client(timeout=180.0) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    images = []
    for choice in data.get("output", {}).get("choices", []):
        content = choice.get("message", {}).get("content", [])
        for item in content:
            if "image" in item:
                images.append(item["image"])
    if not images:
        raise ValueError(f"图像生成未返回结果: {json.dumps(data, ensure_ascii=False)}")
    return images
