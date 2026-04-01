import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.knowledge_base import knowledge_base
from services.param_advisor import get_scenarios, get_params, calculate_custom_params
from services.matlab_bridge import matlab_bridge
from services import qwen_client
from config import HOST, PORT, DASHSCOPE_API_KEY, MODEL_PRICING, IMAGE_GEN_PRICE

app = FastAPI(title="柔直仿真AI辅助知识系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Models ───


class ChatRequest(BaseModel):
    messages: list[dict]
    enable_search: bool = False


class ImageAnalysisRequest(BaseModel):
    image: str  # base64
    text: str = ""
    analysis_type: str = "general"


class CustomParamRequest(BaseModel):
    udc_kv: float
    capacity_mw: float


class ImageGenRequest(BaseModel):
    prompt: str
    n: int = 1


# ─── Routes ───


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/status")
async def status():
    return {
        "api_key_configured": bool(DASHSCOPE_API_KEY),
        "knowledge_topics": len(knowledge_base.get_all_topics()),
        "matlab": matlab_bridge.status(),
        "pricing": MODEL_PRICING,
        "image_gen_price": IMAGE_GEN_PRICE,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not DASHSCOPE_API_KEY:
        return JSONResponse({"error": "未配置 DASHSCOPE_API_KEY 环境变量"}, status_code=500)

    last_user_msg = ""
    for m in reversed(req.messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    knowledge_ctx = knowledge_base.get_context_for_query(last_user_msg)

    def generate():
        try:
            for chunk in qwen_client.chat_stream(req.messages, knowledge_ctx, req.enable_search):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/analyze-image")
async def analyze_image(req: ImageAnalysisRequest):
    if not DASHSCOPE_API_KEY:
        return JSONResponse({"error": "未配置 DASHSCOPE_API_KEY 环境变量"}, status_code=500)

    knowledge_ctx = knowledge_base.get_context_for_query(req.text or req.analysis_type)

    def generate():
        try:
            for chunk in qwen_client.analyze_image_stream(
                req.image, req.text, req.analysis_type, knowledge_ctx
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/knowledge/topics")
async def knowledge_topics():
    return knowledge_base.get_all_topics()


@app.get("/api/knowledge/search")
async def knowledge_search(q: str, top_k: int = 5):
    results = knowledge_base.search(q, top_k)
    return results


@app.get("/api/params/scenarios")
async def param_scenarios():
    return get_scenarios()


@app.get("/api/params/{scenario_id}")
async def param_detail(scenario_id: str):
    result = get_params(scenario_id)
    if not result:
        return JSONResponse({"error": "场景不存在"}, status_code=404)
    return result


@app.post("/api/params/custom")
async def param_custom(req: CustomParamRequest):
    return calculate_custom_params(req.udc_kv, req.capacity_mw)


@app.get("/api/matlab/status")
async def matlab_status():
    return matlab_bridge.status()


@app.post("/api/generate-image")
async def generate_image(req: ImageGenRequest):
    if not DASHSCOPE_API_KEY:
        return JSONResponse({"error": "未配置 DASHSCOPE_API_KEY 环境变量"}, status_code=500)
    try:
        urls = qwen_client.generate_image(req.prompt, req.n)
        return {"images": urls}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    knowledge_base.load()
    print(f"知识库已加载: {len(knowledge_base.chunks)} 个知识块")
    print(f"API Key: {'已配置' if DASHSCOPE_API_KEY else '未配置 (请设置 DASHSCOPE_API_KEY 环境变量)'}")
    print(f"启动服务: http://localhost:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
