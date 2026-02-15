import uvicorn
import os
import sys

# 将当前目录添加到 sys.path，确保可以导入 app 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 从环境变量读取端口（Render 等云平台会动态分配端口）
    port = int(os.environ.get("PORT", 8000))
    print("🐱 正在启动猫咪健康诊断系统...")
    print(f"访问地址: http://0.0.0.0:{port}")
    # 生产模式：绑定 0.0.0.0 允许外部访问，关闭热重载
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
