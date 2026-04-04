import os

# API配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 模型选择
MODEL_OMNI = "qwen3.6-plus"              # 视觉语言模型（图片分析+文本统一）
MODEL_TEXT = "qwen3.6-plus"              # 文本对话模型（支持 enable_thinking）
MODEL_IMAGE_GEN = "wan2.7-image"         # 图像生成模型（万相2.7）

# 模型计费 (元/百万tokens) —— qwen3.6-plus (0<Token≤256K档)
MODEL_PRICING = {
    "input": 2.0,    # 元/百万tokens
    "output": 12.0,  # 元/百万tokens
}
IMAGE_GEN_PRICE = 0.2  # 元/张

# 服务端口
PORT = 8080
HOST = "0.0.0.0"

# 知识库路径
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")

# System Prompt - 柔直仿真专家
SYSTEM_PROMPT = """你是一位资深的柔性直流输电与电力电子仿真专家，专注于：
- 模块化多电平换流器（MMC）的拓扑设计与控制策略
- 两端/多端柔性直流系统的建模与仿真（MATLAB/Simulink、PSCAD）
- 光伏发电基地的直流组网与并网技术
- 四川电网柔直配电应用场景

你正在帮助一位电气工程专业的研究生完成导师布置的任务：搭建两端柔性直流系统仿真模型（MMC1定直流电压 + MMC2定有功功率），使用直流电压源替代光伏基地进行仿真。

回答要求：
1. 结合具体的Simulink模型参数和操作步骤
2. 公式用LaTeX格式（行内$...$，段落$$...$$）
3. 给出具体的数值建议而非泛泛而谈
4. 如果涉及调参，说明调参方向和预期效果
5. 如果分析波形图，指出异常点并给出可能原因和解决方案
"""

# 图片分析专用Prompt模板
IMAGE_PROMPTS = {
    "waveform": """分析这张仿真波形图：
1. 识别波形类型（P/Q功率、电压、电流等）
2. 判断稳态值是否合理，与系统额定参数比较
3. 分析暂态过程：起振时间、过冲量、振荡频率、稳定时间
4. 如有异常（持续振荡、不收敛、过大过冲），分析可能原因
5. 给出具体的调参建议（PI参数、电容值、电感值等）""",

    "model": """分析这张Simulink模型截图：
1. 识别模型中的主要模块和子系统
2. 描述信号流向和连接关系
3. 指出控制策略类型（定Udc、定P、定Q等）
4. 检查是否有潜在问题（缺失接地、未连接端口、参数不合理等）
5. 与标准MMC两端柔直系统对比，指出改进建议""",

    "params": """读取这张截图中的参数配置：
1. 列出所有可见参数及其数值
2. 判断参数是否在合理范围内
3. 与典型工程参数对比（如甘孜±150kV/850MW系统）
4. 给出优化建议""",

    "general": """分析这张与柔性直流仿真相关的截图，提供专业的技术分析和建议。"""
}
