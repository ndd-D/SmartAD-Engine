# SmartAD-Engine

> 智能广告引擎 —— 基于 AI 的广告投放管理与优化平台

## 项目简介

SmartAD-Engine 是一个集广告管理、AI 智能优化、数据分析于一体的广告引擎平台，由三个核心服务组成：

| 模块 | 技术栈 | 描述 |
|------|--------|------|
| `smartad-server` | Java 17 + Spring Boot 3 + MyBatis-Plus | 后端 REST API 服务 |
| `smartad-admin` | Vue 3 + Vite + Element Plus | 管理后台前端 |
| `smartad-agent` | Python + FastAPI + LangChain | AI 智能代理服务 |
| `docs` | Markdown + SQL | 项目文档与数据库脚本 |

## 技术架构

```
┌──────────────────────────────────────────────────┐
│                  smartad-admin                    │
│              Vue 3 管理后台 (:80)                  │
└─────────────────────┬────────────────────────────┘
                      │ HTTP
┌─────────────────────▼────────────────────────────┐
│                 smartad-server                    │
│           Spring Boot REST API (:8081)            │
└───────────────┬─────────────────┬────────────────┘
                │ MySQL           │ HTTP
        ┌───────▼──────┐  ┌───────▼──────────────┐
        │    MySQL     │  │    smartad-agent      │
        │   数据库      │  │  FastAPI AI服务(:8001) │
        └──────────────┘  └──────────────────────┘
```

## 快速开始

### 环境要求

- Java 17+
- Maven 3.8+
- Node.js 18+
- Python 3.10+
- MySQL 8.0+

### 1. 数据库初始化

```sql
-- 执行 docs/init.sql 初始化数据库
mysql -u root -p < docs/init.sql
```

### 2. 启动后端服务 (smartad-server)

```bash
cd smartad-server

# 复制配置文件并填写真实配置
cp src/main/resources/application-example.yml src/main/resources/application.yml
# 编辑 application.yml，填写数据库密码、JWT密钥等

# 编译并运行
mvn clean package -DskipTests
java -jar target/smartad-server-*.jar
# 服务启动在 http://localhost:8081
```

### 3. 启动 AI 代理服务 (smartad-agent)

```bash
cd smartad-agent

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件并填写真实配置
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY 等

# 启动服务
python main.py
# 服务启动在 http://localhost:8001
```

### 4. 启动管理前端 (smartad-admin)

```bash
cd smartad-admin

# 安装依赖
npm install

# 开发模式启动
npm run dev
# 访问 http://localhost:5173

# 生产构建
npm run build
```

### 5. Docker Compose 一键启动（推荐）

```bash
# 根目录下复制环境变量文件
cp .env.example .env
# 填写 DEEPSEEK_API_KEY

docker-compose up -d
```

## 项目结构

```
SmartAD-Engine/
├── smartad-server/          # Java 后端服务
│   ├── src/
│   │   └── main/
│   │       ├── java/        # 业务代码
│   │       └── resources/
│   │           └── application-example.yml  # 配置模板
│   ├── pom.xml
│   └── Dockerfile
├── smartad-admin/           # Vue 管理前端
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── smartad-agent/           # Python AI 代理
│   ├── app/                 # FastAPI 应用
│   ├── chains/              # LangChain 链
│   ├── .env.example         # 环境变量模板
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                    # 项目文档
│   ├── database_design.md   # 数据库设计文档
│   └── init.sql             # 数据库初始化脚本
└── .env.example             # 根目录环境变量模板
```

## 配置说明

### 敏感配置处理

本项目所有敏感配置均通过环境变量注入，**不在代码中硬编码**：

| 配置项 | 文件 | 说明 |
|--------|------|------|
| 数据库密码 | `smartad-server/src/main/resources/application.yml` | 参考 `application-example.yml` |
| DeepSeek API Key | `smartad-agent/.env` | 参考 `.env.example` |
| JWT Secret | `smartad-server/src/main/resources/application.yml` | 参考 `application-example.yml` |

## API 文档

后端服务启动后，访问内置 Knife4j 文档：

```
http://localhost:8081/doc.html
```

## License

MIT License
