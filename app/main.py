"""
猫病诊断治疗系统 - FastAPI 后端主入口。

提供症状获取、疾病诊断等 RESTful API 接口，
并托管前端静态文件。
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pathlib

from app.engine import DiagnosisEngine

# 项目根目录
BASE_DIR = pathlib.Path(__file__).parent.parent

# 创建 FastAPI 应用
app = FastAPI(
    title="🐱 猫病诊断治疗系统",
    description="根据猫的症状体征智能诊断可能的疾病，并给出治疗方案",
    version="1.0.0",
)

# 初始化诊断引擎
engine = DiagnosisEngine()

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


class DiagnoseRequest(BaseModel):
    """诊断请求模型。"""
    symptoms: list[str]  # 症状ID列表
    breed_id: str | None = None  # 品种ID（可选）
    cat_age: str | None = None  # 猫的年龄段（可选）
    cat_weight: float | None = None  # 猫的体重kg（可选）


@app.get("/")
async def index():
    """返回前端主页面。"""
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.get("/api/symptoms")
async def get_symptoms():
    """获取所有可用症状（按分类）。"""
    return engine.get_all_symptoms()


@app.get("/api/breeds")
async def get_breeds():
    """获取所有支持的猫咪品种。"""
    return engine.get_breeds()


@app.post("/api/diagnose")
async def diagnose(request: DiagnoseRequest):
    """
    根据症状进行诊断。

    接收症状列表和品种，返回按匹配度排序的诊断结果，
    每个结果包含疾病信息、完整治疗方案及品种特定建议。
    """
    results = engine.diagnose(request.symptoms, breed_id=request.breed_id)

    # 将症状ID转换为中文名称
    symptom_names = {sid: engine.get_symptom_name(sid) for sid in request.symptoms}

    return {
        "input_symptoms": symptom_names,
        "results_count": len(results),
        "results": [r.to_dict() for r in results],
        "disclaimer": "⚠️ 本系统仅供参考，不能替代专业兽医诊断。如猫咪症状严重，请立即就医！",
    }
