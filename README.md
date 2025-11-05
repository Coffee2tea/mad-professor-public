# Bonjour! 法语小伙伴

一个基于 PyQt6 的桌面应用，帮助 8-12 岁学生跟随动画老师“阳光老师 Amélie”学习法语。应用保留了原项目的文档处理与 RAG 检索能力，同时重新设计了儿童友好的界面、课堂提示词以及卡通语音体验。

## 功能亮点
- **课本秒变知识库**：导入 PDF 或 Markdown 课本后，自动拆分章节、构建向量索引，并支持中法双语切换。
- **动画老师陪练**：聊天窗口的人设、决策 Prompt 和 TTS 全面调整为阳光老师 Amélie，回答方式温柔、互动化。
- **卡通语音播报**：集成 MiniMax TTS，默认使用适合儿童的卡通音色，并根据情绪调整语速与音调。
- **语音问答**：延续语音识别与实时播放链路，孩子可以直接对着麦克风发问或跟读。
- **暖色系教室 UI**：窗口、侧边栏、Markdown 阅读区与聊天区全面换肤，突出课程、奖励和小游戏提示。

## 架构概览
- **界面层**：`AI_professor_UI.py` 负责主窗口布局；`ui/` 目录包含课本视图、聊天组件、侧边栏与上传面板。
- **数据层**：`data_manager.py` 管理课本索引、内容加载、处理队列与信号分发。
- **AI 管理层**：`AI_manager.py` 协调对话、RAG 检索、语音识别与 TTS 播报。
- **文本处理管线**：`pipeline.py` 复用原论文处理流程，可将教材转换为结构化 JSON、翻译稿和向量库。
- **提示词与角色**：`prompt/` 目录新增课堂角色、决策路由和教学提示词三套文件。

## 环境准备
### 依赖
- Python 3.10+
- PyQt6、PyQt6-WebEngine
- magic-pdf、RealtimeSTT、pyaudio 等（详见 `requirements.txt`）
- 推荐 GPU ≥6GB（可选，用于更快完成批量嵌入）

### 安装步骤
1. 创建环境并安装依赖：
   ```bash
   conda create -n french-buddy python=3.10.16
   conda activate french-buddy
   pip install -U magic-pdf[full]==1.3.3 -i https://mirrors.aliyun.com/pypi/simple
   pip install -r requirements.txt
   ```
2. 根据显卡安装匹配的 PyTorch 与 CUDA（示例）
   ```bash
   pip install --force-reinstall torch torchvision torchaudio "numpy<=2.1.1" --index-url https://download.pytorch.org/whl/cu124
   ```
3. 安装 FAISS GPU（可选）
   ```bash
   conda install -c conda-forge faiss-gpu
   ```
4. 下载 MinerU 所需模型（首次运行时也可自动下载）
   ```bash
   python download_models.py
   ```
5. 配置 LLM 与 TTS API，在 `config.py` 中填写：
   ```python
   API_BASE_URL = "YOUR_API_URL"
   API_KEY = "YOUR_API_KEY"
   TTS_GROUP_ID = "YOUR_MINIMAX_GROUP_ID"
   TTS_API_KEY = "YOUR_MINIMAX_API_KEY"
   TTS_VOICE_ID = "YOUR_MINIMAX_FRENCH_CARTOON_VOICE"
   ```
   `TTS_VOICE_ID` 建议使用事先在 MiniMax 平台克隆好的卡通音色。

## 运行
```bash
python main.py
```
启动后将看到橙色暖调的“Bonjour! 法语小伙伴”界面，左侧为课本列表与导入面板，中间为课本文档，右侧是阳光老师 Amélie 的聊天窗口。

## 使用指南
1. **导入课本**：点击侧边栏底部“导入课本”按钮，选择 PDF/Markdown 文件并等待处理完成。
2. **选择课程**：从左侧列表挑选想要学习的课本章节，中央阅读区会展示中/法双语内容，可通过右上角按钮切换语言。
3. **课堂互动**：在聊天区输入问题、小游戏指令或语音发问，Amélie 会结合课本内容进行讲解、带读或布置练习。
4. **语音练习**：聊天框下方可切换麦克风设备并开启实时语音识别，适合跟读发音与听力练习。

## 定制指南
- **更换角色设定**：编辑 `prompt/ai_character_prompt_french_tutor.txt` 与 `prompt/ai_explain_prompt_french_tutor.txt`。
- **调整教学策略**：`prompt/ai_router_prompt_french_tutor.txt` 决定课堂情绪与检索策略，可按需要扩展新功能标签。
- **切换音色**：修改 `config.py` 中 `TTS_VOICE_ID`，并在 `TTS_manager.py` 的 `build_tts_stream_body` 调整语速、音高。
- **教材预处理**：若教材结构特殊，可扩展 `processor/` 下各处理器或在 `pipeline.py` 中自定义拆分逻辑。

## 目录结构
```
mad-professor-public/
├── AI_professor_UI.py      # 主界面（现已是法语学习主题）
├── AI_professor_chat.py    # Amélie 的对话逻辑与策略
├── AI_manager.py           # 对话、RAG、语音与TTS协调器
├── data_manager.py         # 课本索引、内容与处理队列
├── TTS_manager.py          # MiniMax 流式 TTS
├── voice_input.py          # 语音识别入口
├── pipeline.py             # 课本处理管线
├── prompt/                 # 课堂人设、决策与讲解提示词
└── ui/                     # 聊天、侧边栏、Markdown 视图等组件
```

## 致谢
项目仍然依赖下列优秀的开源与云服务：
- [MinerU](https://github.com/opendatalab/MinerU)
- [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT)
- [DeepSeek API](https://api-docs.deepseek.com)
- [MiniMax 语音克隆](https://platform.minimaxi.com/document/Voice%20Cloning?key=66719032a427f0c8a570165b)

欢迎在此基础上继续打造更多课堂玩法，让更多孩子快乐学外语！
