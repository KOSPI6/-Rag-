from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph2.graph_2 import graph
from utils.log_utils import log
import json
import time

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class QuestionRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/monitor", response_class=HTMLResponse)
async def monitor():
    with open("templates/graph_monitor.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/chat")
async def chat(request: QuestionRequest):
    try:
        question = request.question

        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")

        log.info(f'收到用户问题: {question}')

        inputs = {'question': question}
        result = None

        for output in graph.stream(inputs):
            for key, value in output.items():
                log.info(f'Node "{key}" 执行完成')
                result = value

        generation = result.get('generation', '抱歉，无法生成回答')

        return {
            'answer': generation,
            'success': True
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f'处理请求时出错: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: QuestionRequest):
    """流式返回 Graph 执行过程"""
    question = request.question

    async def generate():
        try:
            if not question:
                yield f"data: {json.dumps({'type': 'error', 'error': '问题不能为空'})}\n\n"
                return

            log.info(f'收到用户问题: {question}')

            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'question': question})}\n\n"

            inputs = {'question': question}
            result = None

            for output in graph.stream(inputs):
                for key, value in output.items():
                    log.info(f'Node "{key}" 执行完成')

                    # 安全获取文档数量
                    documents = value.get('documents', [])
                    doc_count = len(documents) if isinstance(documents, list) else 0

                    # 发送节点执行事件
                    event_data = {
                        'type': 'node',
                        'node': key,
                        'data': {
                            'question': value.get('question', ''),
                            'documents_count': doc_count,
                            'generation': value.get('generation', ''),
                            'transform_count': value.get('transform_count', 0)
                        }
                    }
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                    result = value
                    time.sleep(0.1)  # 模拟延迟，便于观察

            generation = result.get('generation', '抱歉，无法生成回答')

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'end', 'answer': generation}, ensure_ascii=False)}\n\n"

        except Exception as e:
            log.error(f'处理请求时出错: {str(e)}')
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
