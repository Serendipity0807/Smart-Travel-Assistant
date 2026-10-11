# 阶段9 测试与部署 — 操作指南

> 写给学习者：本阶段 7 个任务，**任务 0~5 在本地 Windows 完成**，**任务 6 需要一台服务器**。
> 按顺序做，每步都有验证命令，验证不过不要进下一步。

## 任务清单

| # | 任务 | 位置 | 目的 |
|---|------|------|------|
| 0 | git 初始化 + 首次提交 | 项目根 | 部署前提，也是阶段1~8 代码的第一份存档 |
| 1 | Element Plus 按需引入 | 前端 | 首屏 chunk 从 1MB 降到 ~500KB |
| 2 | 生产构建配置 | 前端 | `.env.production`：同源部署 + 高德 key |
| 3 | CORS 收紧白名单 | 后端 | 不再 `*` 全放开，配置化白名单 |
| 4 | requirements 合并进 pyproject | 后端 | 依赖版本可复现（pin 实际版本） |
| 5 | 后端补 API 层测试 | 后端 | 路由/参数校验/容错降级，外部依赖全 mock |
| 6 | Docker + Nginx 部署 | 服务器 | 前端 nginx 静态服务 + `/api` 反代后端 |

---

## 任务 0：git 初始化 + 首次提交

项目至今没有 git 仓库（阶段1~8 代码全未提交），部署也需要 git 来同步代码。

```bash
# 在项目根目录 Smart-Travel-Assistant/ 下
git init
```

**先写 `.gitignore`（根目录新建）**，密钥和依赖绝不能进仓库：

```gitignore
# Python
backend/venv/
__pycache__/
*.pyc
backend/.env
backend/.env.*
backend/logs/

# Node
frontend/node_modules/
frontend/dist/
```

```bash
git add .
git commit -m "阶段1-8: 智能行程规划/地图/预算/编辑/导出 完成"
```

**验证**：`git log --oneline` 有一条提交；`git status` 干净。

> 易错点：如果 `git add .` 前没写好 .gitignore，`backend/.env` 会被加进去。万一发生：
> `git rm --cached backend/.env` 再补 .gitignore 重新提交。密钥一旦推上远程仓库必须去换 key。

---

## 任务 1：Element Plus 按需引入（前端）

现状：[main.ts](frontend/src/main.ts) 全量引入 Element Plus，导致 `index` chunk 1.08MB（gzip 361KB）。
方案：官方推荐的 unplugin 自动导入，**模板里用到的组件自动按需打包**。

### 1.1 安装插件

```bash
cd frontend
npm install -D unplugin-vue-components unplugin-auto-import
```

### 1.2 改 [vite.config.ts](frontend/vite.config.ts)

```ts
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入: 模板里的组件(如 el-button)由插件自动解析并只打包用到的
    AutoImport({ resolvers: [ElementPlusResolver()] }),
    Components({ resolvers: [ElementPlusResolver()] }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
  },
})
```

### 1.3 改 [main.ts](frontend/src/main.ts)

```ts
// 应用入口: 挂载 App(=后端 main.py 的角色)
// Element Plus 按需引入(阶段9): 组件由 vite 插件自动导入, 这里不再全量注册
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { createApp } from 'vue'

// 基础样式(reset + CSS 变量 --el-color-*)
import 'element-plus/theme-chalk/base.css'
// ElMessage/ElMessageBox 在 script 里手动 import(PlanView.vue), 插件管不到, 样式需手动引入
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'

import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(router).mount('#app')
```

**删除的三行**：`import ElementPlus from 'element-plus'`、`import 'element-plus/dist/index.css'`、`createApp(App).use(ElementPlus, { locale: zhCn }).use(router)...` 里的 `.use(ElementPlus, ...)`。

### 1.4 中文 locale 改由 ConfigProvider 提供（改 [App.vue](frontend/src/App.vue)）

原来 `app.use(ElementPlus, { locale: zhCn })` 的全局配置没有了，改用组件包裹：

```vue
<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>
```

（以你现有的 App.vue 为准，把 `<router-view />` 包进去即可，script 加 zhCn import。）

### 1.5 tsconfig 包含插件生成的声明文件

首次 `npm run dev` 或 `npm run build` 后，**项目根目录会生成 `components.d.ts` 和 `auto-imports.d.ts`**。
打开 [tsconfig.app.json](frontend/tsconfig.app.json)，把这两个文件加进 `include`（否则 vue-tsc 不认识模板里自动导入的组件名）：

```json
"include": ["src/**/*.ts", "src/**/*.vue", "components.d.ts", "auto-imports.d.ts"]
```

### 1.6 验证

```bash
npm run build
```

看产物体积：`index-*.js` 应从 1.08MB 降到 ~500KB 左右（按需引入后 Element Plus 组件会拆到各自的异步 chunk 里）。
再看一眼页面：日期选择器、对话框、消息提示都正常，日期控件是中文（ConfigProvider 生效）。

> 易错点：
> - `ElMessage.error()` 弹窗没有样式 → 检查 1.3 的 message/message-box 样式 import 是否漏了
> - 组件显示但样式奇怪（变量丢失）→ 检查 `element-plus/theme-chalk/base.css` 是否引入
> - 日期选择器变英文 → App.vue 的 ConfigProvider 没生效

---

## 任务 2：生产构建配置（前端）

现在 `VITE_API_BASE_URL=http://localhost:8000` 只存在于 `.env.development`。生产部署走 **nginx 同源反代**（前端页面和 `/api` 同域名），所以生产构建时 baseURL 应留空。

**新建 [.env.production](frontend/.env.production)**（key 从 .env.development 复制过来）：

```bash
# 生产: 同源部署(nginx 把 /api 反代到后端), baseURL 留空 = 相对路径
VITE_API_BASE_URL=

# 高德 Web端(JS API) key + 安全密钥(与 .env.development 相同)
VITE_AMAP_JS_KEY=你的key
VITE_AMAP_SECURITY_CODE=你的安全码
```

**验证**：

```bash
npm run build
grep -r "localhost:8000" dist/   # 应无任何输出
```

> 说明：`import.meta.env.VITE_API_BASE_URL` 在**构建时**就固化进产物了，所以本地 dev 读 .env.development、生产 build 读 .env.production，两者互不影响。
> 高德 JS key 本来就暴露在前端（靠域名白名单防护，不是秘密），放 .env.production 没问题。

---

## 任务 3：CORS 收紧（后端）

现状：[main.py](backend/app/main.py) 里 `allow_origins=["*"]` 全放开。收紧为**配置化白名单**。

### 3.1 [config.py](backend/app/config.py) 加一个字段

照现有字段的样子加：

```python
# CORS 白名单: 逗号分隔的允许来源列表(阶段9: 从 * 收紧)
# 部署走 nginx 同源反代后本不需要跨域, 白名单是给直连场景的兜底
cors_origins: str = "http://localhost:5173"
```

### 3.2 [main.py](backend/app/main.py) 改 CORS 中间件

```python
# CORS: 只放行白名单来源(阶段9收紧, 不再使用 *)
_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

（原来的 `allow_origins=["*"]` 版替换掉；注释也更新。）

### 3.3 同步 .env / .env.example

如果项目里有 `backend/.env.example`，加上一行：

```bash
# CORS 白名单, 多个来源用英文逗号分隔; 部署时改成实际域名, 如 http://trip.example.com
CORS_ORIGINS=http://localhost:5173
```

**验证**（起后端后）：

```bash
# 白名单内的来源有 CORS 头
curl -s -H "Origin: http://localhost:5173" -D - http://localhost:8000/api/health -o /dev/null | grep -i access-control
# 应看到 access-control-allow-origin: http://localhost:5173

# 白名单外的来源没有
curl -s -H "Origin: http://evil.com" -D - http://localhost:8000/api/health -o /dev/null | grep -i access-control
# 应无任何 access-control 头
```

> 部署时（任务6）：服务器上 `backend/.env` 里把 `CORS_ORIGINS` 改成你的实际域名（如 `http://trip.example.com`），有多个就逗号分隔。

---

## 任务 4：requirements 合并进 pyproject（后端）

目标：依赖清单只维护一处，并且 **pin 住本地验证过的实际版本**（服务器构建时才不会装到不兼容的新版）。

### 4.1 拿到本地实际版本

```bash
cd backend
venv/Scripts/pip.exe freeze | grep -E "^(fastapi|uvicorn|pydantic|pydantic-settings|httpx|langchain|langchain-openai|langgraph|loguru|mcp|fastmcp|openai)=="
```

会输出类似：

```
fastapi==0.1xx.x
langchain==1.4.4
...
```

### 4.2 改 [pyproject.toml](backend/pyproject.toml)

在 `[project]` 里加 `dependencies`（版本号填 4.1 拿到的实际值）：

```toml
[project]
name = "smart-travel-assistant-backend"
version = "0.1.0"
description = "智能旅游助手后端(FastAPI + LangChain/LangGraph)"
requires-python = ">=3.10"
dependencies = [
    # Web 框架
    "fastapi==0.1xx.x",
    "uvicorn[standard]==0.xx.x",
    # 数据验证与配置
    "pydantic==2.x.x",
    "pydantic-settings==2.x.x",
    # HTTP 客户端(调用高德/Unsplash REST API)
    "httpx==0.xx.x",
    # 智能体框架(LangChain 1.x + LangGraph 1.x)
    "langchain==1.4.4",
    "langchain-openai==1.7.0",
    "langgraph==1.2.14",
    "openai==3.28.0",
    # 日志(企业统一日志)
    "loguru==0.7.x",
    # MCP 协议(scripts/ 验证脚本还在用; langchain 内置适配器也依赖它)
    "mcp==1.x.x",
    "fastmcp==4.1.0",
]
```

### 4.3 验证 + 删掉 requirements.txt

```bash
venv/Scripts/pip.exe install -e .          # 用新清单重装一次, 现有环境应几乎无变化
venv/Scripts/python.exe -m pytest          # 13+ 测试仍全绿
venv/Scripts/ruff.exe check .              # 无新告警
rm requirements.txt                        # 依赖清单合并完成, 删旧文件
```

（`rm` 用 Git Bash；也可以直接在 VSCode 里删。）

> 易错点：`pip install -e .` 之后如果 pytest/ruff 还在，说明 dev 依赖没动，正常。若报缺少 `setuptools` 之类，`pip install setuptools` 即可（Python 3.13 环境偶发）。

---

## 任务 5：后端补 API 层测试

现在测试只有 `test_budget_service.py`（8个）和 `test_spot_service.py`（5个），都是服务层。补**路由层**测试：参数校验、响应包装格式、外部依赖 mock。

**新建 [tests/test_api.py](backend/tests/test_api.py)**：

```python
"""API 层测试: 路由/参数校验/容错降级

原则: 外部依赖(高德/LLM)全部 mock, 测试不访问真实网络
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # 三个密钥状态只能是 bool, 且不泄露密钥本身
    assert isinstance(body["llm_configured"], bool)
    assert isinstance(body["amap_configured"], bool)
    assert isinstance(body["unsplash_configured"], bool)


def test_search_spots_requires_keyword():
    """缺 keyword 参数 → FastAPI 校验直接 422"""
    resp = client.get("/api/trip/spots/search")
    assert resp.status_code == 422


def test_search_spots_ok(monkeypatch):
    """mock 掉高德客户端: 验证响应包装格式与 POI 转换正确"""
    from app.services import spot_service

    def fake_search(keyword, city="", offset=10):
        return [
            {
                "name": "测试景点",
                "location": "120.100000,30.200000",
                "address": ["测试路1号"],
                "type": "风景名胜;国家级景点",
            }
        ]

    # 注意看 spot_service.py 里 amap 客户端是怎么 import 的, monkeypatch 的路径要对应:
    #   from app.services.amap_client import search_pois  → patch spot_service.search_pois
    #   from app.services import amap_client             → patch amap_client.search_pois
    monkeypatch.setattr(spot_service, "search_pois", fake_search)

    resp = client.get("/api/trip/spots/search", params={"keyword": "测试", "city": "杭州"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    spots = body["data"]
    assert len(spots) == 1
    assert spots[0]["name"] == "测试景点"
    assert spots[0]["lng"] == 120.1
    assert spots[0]["lat"] == 30.2
    assert spots[0]["address"] == "测试路1号"


def test_search_spots_amap_failure_degrades(monkeypatch):
    """高德异常时降级返回空列表: 企业容错原则, 外部依赖失败不级联成 500"""
    from app.services import spot_service

    def fake_search(keyword, city="", offset=10):
        return []  # amap_client 内部已把异常降级为 [], 这里模拟降级结果

    monkeypatch.setattr(spot_service, "search_pois", fake_search)
    resp = client.get("/api/trip/spots/search", params={"keyword": "测试"})
    assert resp.status_code == 200
    assert resp.json() == {"code": 0, "message": "success", "data": []}
```

**验证**：

```bash
venv/Scripts/python.exe -m pytest -v     # 全部测试(13+新增)通过
venv/Scripts/ruff.exe check .
```

> 关键点：先打开 [spot_service.py](backend/app/services/spot_service.py) 确认它 import amap_client 的**具体写法**，按注释里的对应关系 patch，否则 mock 不生效、测试会打真实网络。

---

## 任务 6：Docker + Nginx 部署（服务器）

架构：

```
浏览器 ──> 服务器 80 端口 ──> nginx(frontend 容器)
                              ├── /           → 前端静态页面(dist)
                              └── /api/*      → 反代 → backend 容器(8000, 不对外暴露)
```

### 6.1 先推到远程仓库（推荐 Gitee，国内快）

```bash
git remote add origin https://gitee.com/你的用户名/smart-travel-assistant.git
git push -u origin master
```

### 6.2 新增 6 个部署文件

**backend/Dockerfile**：

```dockerfile
FROM python:3.13-slim

# 国内构建加速: 清华 PyPI 镜像
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**backend/.dockerignore**（密钥绝不进镜像，容器运行时通过 env_file 注入）：

```
venv/
__pycache__/
*.pyc
.env
.env.*
logs/
tests/
scripts/
```

**frontend/Dockerfile**（多阶段：node 构建 → nginx 运行）：

```dockerfile
# 构建阶段: node 打生产包(读 .env.production)
FROM node:20-alpine AS build
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 运行阶段: nginx 静态服务 + API 反代
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**frontend/.dockerignore**：

```
node_modules/
dist/
```

**frontend/nginx.conf**：

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA 路由: 刷新 /plan 之类的路径不 404, 全部回落 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到后端容器(compose 内网用服务名 backend 寻址)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 180s;  # 行程规划全流程约 1-2 分钟, 默认 60s 会超时!
    }
}
```

**docker-compose.yml**（项目根目录）：

```yaml
services:
  backend:
    build: ./backend
    env_file: ./backend/.env   # 服务器上的 .env 注入容器环境变量
    restart: unless-stopped
    # 不映射端口: 只允许 frontend 经 compose 内网访问, 不直接暴露公网

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### 6.3 服务器操作（Linux）

**① 安装 Docker**（国内用 daocloud 脚本或先配镜像加速）：

```bash
curl -fsSL https://get.docker.com | bash
# 镜像加速(任选一个国内源), 写入 /etc/docker/daemon.json 后重启 docker:
#   https://mirror.ccs.tencentyun.com
#   https://docker.m.daocloud.io
```

**② 拉代码 + 写密钥**：

```bash
git clone https://gitee.com/你的用户名/smart-travel-assistant.git
cd smart-travel-assistant
vim backend/.env     # 内容与本地 backend/.env 相同, 另加:
                     # CORS_ORIGINS=http://你的域名   (不用 nginx 反代直连时才有意义, 兜底)
```

**③ 构建启动**：

```bash
docker compose up -d --build
docker compose ps          # 两个服务都是 Up
docker compose logs -f backend   # 有报错看这里
```

**④ 验证**：

```bash
curl http://localhost/api/health        # 服务器本机, 应返回 {"status":"ok",...}
```

浏览器访问 `http://服务器IP/`：首页能开、三个密钥状态全绿、能规划行程、地图能显示。

### 6.4 收尾两件事

1. **高德控制台加白名单**：Web端(JS API) key 的「域名白名单」加上你的域名（如 `http://trip.example.com`，用 IP 就加 IP），否则地图报 `USERKEY_PLAT_NOMATCH`。
2. **安全组/防火墙**：只开 80 端口即可，**8000 不要开**（backend 容器没映射端口，外部本来就访问不到）。

---

## 阶段9 完成验收清单

- [ ] `git log` 有首次提交，后续改动有意义的提交
- [ ] 前端 build 后 index chunk 明显变小；页面功能、中文 locale 正常
- [ ] `grep -r localhost:8000 dist/` 无输出（生产构建同源）
- [ ] CORS：白名单内带 CORS 头、白名单外没有
- [ ] requirements.txt 已删，`pip install -e .` 可用，pyproject dependencies 为 pin 版本
- [ ] `pytest -v` 全绿（含新增 API 测试，外部依赖全 mock）
- [ ] 服务器 `curl http://localhost/api/health` 正常，浏览器完整走通：规划 → 地图 → 编辑 → 导出
- [ ] 高德域名白名单已加，生产环境地图正常
- [ ] 服务器上看过 `docker compose logs backend`，无异常堆栈

## 下一阶段预告（阶段10）

自写高德 MCP server：把「精确交通路线预算核算」补上——目前交通费是 50 元/人/天估算（前后端各一处常量），阶段10 用 `maps_direction_transit_integrated` 按真实路线（地铁/公交/打车价格）核算，替换估算值。
