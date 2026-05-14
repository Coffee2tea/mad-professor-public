# 网络版改造分析（从 PyQt6 桌面版到 Web 版）

## 1. 当前项目形态结论
本项目目前是**典型本地桌面应用**：
- UI：`PyQt6` 组件渲染（`AI_professor_UI.py` + `ui/`）
- 业务编排：`AI_manager.py` + `data_manager.py`
- 文档处理与 RAG：`pipeline.py`、`processor/`、`rag_retriever.py`
- 语音：`voice_input.py` + `TTS_manager.py`

这意味着“改为网络版”时，建议遵循“**先服务化、再前后端分离**”路线，尽量复用已有 AI 与处理逻辑，避免重写算法核心。

---

## 2. 可复用与需重构模块

### 2.1 可高复用（优先保留）
- `pipeline.py` 与 `processor/*`：教材解析/转换链路。
- `rag_retriever.py`：检索逻辑。
- `AI_professor_chat.py`、`AI_manager.py` 中与模型调用和提示词路由相关的纯业务部分。
- `prompt/*`：角色设定和教学策略资产。

### 2.2 需重构/替换
- `AI_professor_UI.py`、`ui/*`：完全是桌面组件，需替换为 Web 前端。
- `threads.py` 中若包含 Qt 线程/信号机制，需要改为后端任务队列或 async。
- `voice_input.py`：桌面音频采集方式需改为浏览器 WebRTC/MediaRecorder。
- 本地文件路径依赖（`paths.py`）需引入“按用户隔离”的存储策略。

---

## 3. 推荐网络版目标架构

## 3.1 后端（Python）
推荐 `FastAPI`：
- REST API：教材上传、课程列表、聊天、历史记录。
- WebSocket：流式回复 + TTS 播放进度/分片。
- Background Worker：长耗时任务（PDF 解析、向量构建）异步执行。

建议分层：
- `api/`：路由层
- `services/`：对话、RAG、TTS、文档处理服务
- `repositories/`：数据与文件索引
- `workers/`：异步任务执行

## 3.2 前端
推荐 `Next.js`（或 Vue3）：
- 页面模块：课程库、阅读器、聊天、设置。
- 组件映射当前桌面结构：
  - Sidebar -> 课程目录组件
  - MarkdownView -> 浏览器 Markdown/KaTeX 渲染
  - ChatWidget -> Web 聊天组件
- 音频输入输出：
  - 输入：浏览器麦克风权限 + WebRTC
  - 输出：后端返回音频流 URL 或分片二进制

## 3.3 存储与部署
- 数据库：PostgreSQL（用户、教材元信息、对话历史）
- 对象存储：S3/MinIO（上传教材、处理中间产物）
- 向量库：FAISS（单机）或 Milvus/pgvector（多用户）
- 部署：
  - 单机 MVP：Docker Compose（web + api + worker + db + minio）
  - 生产：K8s 或云托管

---

## 4. 分阶段改造路线（最低风险）

### Phase 0：服务抽离（1~2 周）
目标：不改功能，只把非 UI 逻辑从 Qt 项目中抽为可调用服务。
- 把 `AI_manager.py` 里纯业务逻辑抽到 `services/chat_service.py`
- 把 `pipeline.py` 能力包成可由 API 调用的函数
- 统一错误码与日志

### Phase 1：最小可用 Web API（1~2 周）
- 新建 `FastAPI` 项目骨架
- 实现接口：
  - `POST /api/books/upload`
  - `POST /api/books/{id}/process`
  - `GET /api/books`
  - `POST /api/chat`
  - `WS /api/chat/stream`
- 保持现有桌面版可并行运行（降低切换风险）

### Phase 2：Web 前端 MVP（2~3 周）
- 完成登录（可选先匿名）
- 课程列表 + 文档阅读 + 聊天主流程
- 接入流式回答与公式渲染

### Phase 3：语音与多用户能力（2~4 周）
- 语音输入（浏览器）
- TTS 播放
- 用户数据隔离与权限
- 处理任务队列（Celery/RQ）

### Phase 4：生产化（持续）
- 监控：Prometheus + Grafana
- 限流/鉴权：JWT + API Gateway
- 成本优化：缓存、向量分层、冷存储

---

## 5. 关键技术风险与规避

1. **长耗时 PDF 处理阻塞请求**
   - 规避：任务队列 + 状态轮询/推送。
2. **多用户数据串线**
   - 规避：所有资源按 `tenant_id/user_id` 分区。
3. **语音链路浏览器兼容问题**
   - 规避：先做文本主链路，再灰度语音。
4. **向量库容量增长**
   - 规避：教材级索引分片 + 热门缓存。
5. **模型与 TTS API 成本不可控**
   - 规避：会话限额、文本截断、缓存 TTS 结果。

---

## 6. 建议的“第一步落地任务”

1. 在当前仓库新增 `backend/` 目录，初始化 FastAPI。
2. 把 `pipeline.py` 封装成无 UI 依赖的 service 方法。
3. 打通“上传教材 -> 后台处理 -> 聊天检索”单链路 API。
4. 用最简单网页（或 Postman）验证端到端。

> 只要这 4 步跑通，项目就已完成从“桌面内嵌业务”到“可网络访问服务”的关键跨越。

---

## 7. 粗略工期评估（单个熟悉 Python 的全栈）
- MVP（文本上传 + 阅读 + 聊天）：**4~7 周**
- 含语音、鉴权、部署与监控：**8~12 周**

团队并行（前端/后端/算法各 1 人）可缩短约 30%~40%。


---

## 8. 关于“为什么不直接继续上云”的说明

可以，而且**建议从 Day 1 就云优先**。前一版方案强调“先服务化”是为了降低一次性重写风险，不是排斥云。

### 8.1 为什么先服务化再云化
- 当前代码深度耦合桌面 UI 与本地线程模型，先拆服务能减少云上排障复杂度。
- 文档处理和向量构建是长任务，如果不先做任务队列，直接上云也会遇到超时和扩缩容困难。
- 先把 API 边界固定，再上云做网关、鉴权、监控，会更稳。

### 8.2 云上可并行推进（推荐）
可按“**服务化与云化并行**”执行，不需要等本地全部完成：
1. 后端容器化：`api` 与 `worker` 分离镜像。
2. 托管数据库：PostgreSQL（RDS/Aiven/Supabase 等）。
3. 对象存储：S3/OSS/MinIO（云盘或托管）。
4. 队列与缓存：Redis（托管优先）。
5. 部署：
   - MVP：单机云主机 + Docker Compose。
   - 生产：K8s / ECS / Cloud Run（按团队熟悉度选）。

### 8.3 最小云上落地形态（两周内）
- 第 1 周：完成 FastAPI + 上传/处理/聊天 API，容器化并部署到测试环境。
- 第 2 周：接入对象存储、托管 PostgreSQL、Redis 队列，打通端到端。

> 结论：不是“不继续上云”，而是“先把桌面耦合点拆开，同时尽早云上部署”，这样风险和速度最平衡。
