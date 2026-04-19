
#  朔方智域 · 多模态异构认知计算与全域知识检索校园智能引擎系统

> 你的校园生活学习智能助手 | 查课表 · 找教室 · 问学习 · 帮生活 · 识图片 · 纯本地运行

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-本地部署-000000?style=flat-square&logo=ollama&logoColor=white)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 项目名称
朔方智域 · 多模态异构认知计算与全域知识检索校园智能引擎系统

##  核心功能

| 功能模块 | 说明 |
|---------|------|
|  智能对话 | 基于本地大模型，支持多模型切换 |
|  多模态识别 | 上传图片，AI分析内容 |
|  智能检索 | 向量检索 + 知识库，快速查找信息 |
|  课程查询 | 查今日课程、空教室、食堂、活动 |
|  考试倒计时 | 管理考试时间，生成复习计划 |
|  每日一句 | 励志语录，每日更新 |
|  知识库管理 | 自定义知识库，持久化存储 |
 一句话总结

朔方智域 = 大模型的聪明头脑 + 校园专属的实时数据 + 随时更新的灵活性 = 真正懂你的校园助手。

# 文件结构

本项目采用模块化分层架构，代码结构清晰，职责划分明确，便于维护与扩展。

## `modules/` 主模块目录

### `database/` 数据层
负责知识库存储、文档处理与向量检索，是系统知识能力的基础。
- `document_chunker.py`：实现文档智能切片与预处理
- `knowledge_base.py`：提供知识库的增删改查功能
- `vector_store.py`：实现向量数据库构建与语义检索

### `models/` 模型层
统一管理AI模型服务、对话记忆与网络状态检测。
- `conversation_memory.py`：管理多轮对话上下文记忆
- `network_detector.py`：实时检测网络状态，支持模型自动切换
- `smart_model.py`：封装DeepSeek云端模型与Ollama本地模型调用逻辑

### `services/` 业务层
实现校园场景核心业务功能，响应各类服务请求。
- `activity_service.py`：校园活动信息查询服务
- `canteen_service.py`：食堂信息与推荐服务
- `classroom_service.py`：空教室查询与管理服务
- `course_service.py`：课程信息查询服务
- `exam_service.py`：考试管理、倒计时与复习计划生成服务

### `utils/` 工具层
提供通用工具函数，支撑全系统功能运行。
- `helpers.py`：日期、时间、格式转换等通用辅助方法
- `intent.py`：用户意图识别与分类，实现精准服务匹配

### `vision/` 视觉层
实现多模态图片解析与内容理解。
- `ollama_vision.py`：基于本地Ollama模型的图片分析
- `siliconflow_vision.py`：云端视觉模型接口调用
# 环境要求
系统运行需满足：Python 3.10及以上版本，设备内存不低于4GB。可选配置包括本地模型部署工具Ollama，以及用于云端模型调用的DeepSeek API Key，用户可根据使用需求选择部署方式。

# 安装步骤
首先确认Python版本与内存达标，并备好Ollama安装包与DeepSeek API Key。进入项目根目录，在终端执行`pip install -r requirements.txt`安装依赖，推荐使用虚拟环境避免冲突。如需本地模型，安装并启动Ollama后，通过`ollama pull moondream`和`ollama pull qwen:7b`拉取模型。云端模型需在系统侧边栏“API配置”中填写密钥并保存。最后执行`streamlit run app.py`，系统将自动在浏览器启动。

# 安装使用流程
系统启动后，若浏览器未自动打开，可手动访问`http://localhost:8501`。进入界面后先在“服务状态”检查网络、云端及本地模型是否正常可用。
核心功能方面，“智能对话”可解答课表、空教室等校园问题，支持多轮交互，上传图片即可实现通知、试题等内容的多模态解析。“考试管理”支持添加科目与时间，自动生成倒计时和个性化复习计划。“知识检索”可快速查询规章制度、备考重点等信息，支持文档下载与相关内容推荐。
网络中断时，系统自动切换至Ollama本地模型，保障基础对话与本地知识库检索功能可用，网络恢复后自动切回云端，实现离线在线无缝衔接。
#!/bin/bash
## 启动 Ollama 服务
ollama serve &

## 等待 Ollama 服务就绪
sleep 5

## 验证模型是否可用（无需重新下载）
ollama list

## 启动 Streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0