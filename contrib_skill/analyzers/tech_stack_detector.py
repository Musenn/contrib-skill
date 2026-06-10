"""TechStackDetector：基于依赖文件与项目文件识别技术栈。结论附证据文件。"""
from __future__ import annotations

from pathlib import Path

from ..models import TechStackEvidence
from ..utils.file_utils import safe_read_text
from .repo_scanner import RepoStructure

# (类别, 展示名, 关键词列表)。关键词在依赖文件内容中匹配（不区分大小写）。
_CONTENT_RULES: list[tuple[str, str, list[str]]] = [
    ("frameworks", "Spring Boot", ["spring-boot"]),
    ("frameworks", "Spring Security", ["spring-security", "spring-boot-starter-security"]),
    ("frameworks", "MyBatis-Plus", ["mybatis-plus"]),
    ("frameworks", "MyBatis", ["mybatis"]),
    ("frameworks", "JPA", ["spring-data-jpa", "hibernate"]),
    ("frameworks", "React", ["\"react\""]),
    ("frameworks", "Vue", ["\"vue\""]),
    ("frameworks", "Angular", ["@angular/core"]),
    ("frameworks", "Next.js", ["\"next\""]),
    ("frameworks", "Nuxt", ["\"nuxt\""]),
    ("frameworks", "Express", ["\"express\""]),
    ("frameworks", "NestJS", ["@nestjs/core"]),
    ("frameworks", "TypeScript", ["\"typescript\""]),
    ("frameworks", "FastAPI", ["fastapi"]),
    ("frameworks", "Flask", ["flask"]),
    ("frameworks", "Django", ["django"]),
    ("frameworks", "PyTorch", ["torch"]),
    ("frameworks", "TensorFlow", ["tensorflow"]),
    ("frameworks", "Transformers", ["transformers"]),
    ("frameworks", "LangChain", ["langchain"]),
    ("frameworks", "LlamaIndex", ["llama-index", "llama_index"]),
    ("frameworks", "Gin", ["github.com/gin-gonic/gin"]),
    ("frameworks", "Echo", ["github.com/labstack/echo"]),
    ("frameworks", "Gorm", ["gorm.io/gorm"]),
    ("databases", "MySQL", ["mysql"]),
    ("databases", "PostgreSQL", ["postgres", "psycopg"]),
    ("databases", "MongoDB", ["mongodb", "mongoose", "pymongo"]),
    ("databases", "SQLite", ["sqlite"]),
    ("middlewares", "Redis", ["redis"]),
    ("middlewares", "Elasticsearch", ["elasticsearch"]),
    ("middlewares", "Kafka", ["kafka"]),
    ("middlewares", "RabbitMQ", ["rabbitmq", "amqp", "pika"]),
    ("middlewares", "RocketMQ", ["rocketmq"]),
    ("test_tools", "JUnit", ["junit"]),
    ("test_tools", "pytest", ["pytest"]),
    ("test_tools", "Jest", ["\"jest\""]),
    ("test_tools", "Vitest", ["vitest"]),
    ("build_tools", "Vite", ["\"vite\""]),
    ("build_tools", "Webpack", ["webpack"]),
]

# 依赖文件名 -> 构建工具
_BUILD_TOOL_BY_FILE = {
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle",
    "package.json": "npm/yarn/pnpm",
    "pyproject.toml": "pip/poetry/uv",
    "requirements.txt": "pip",
    "setup.py": "pip",
    "go.mod": "Go Modules",
    "Cargo.toml": "Cargo",
}

# 部署相关文件路径关键词 -> 部署方式
_DEPLOY_RULES: list[tuple[str, str]] = [
    ("docker-compose", "Docker Compose"),
    ("dockerfile", "Docker"),
    ("k8s", "Kubernetes"),
    ("kubernetes", "Kubernetes"),
    ("nginx", "Nginx"),
    (".github/workflows", "GitHub Actions"),
    (".gitlab-ci", "GitLab CI"),
]


def detect_tech_stack(repo_path: Path | str, structure: RepoStructure) -> TechStackEvidence:
    root = Path(repo_path).resolve()
    ev = TechStackEvidence(languages=dict(structure.language_file_counts))

    found: dict[str, list[str]] = {
        "frameworks": [], "databases": [], "middlewares": [],
        "build_tools": [], "test_tools": [],
    }

    for dep_file in structure.dependency_files:
        fname = Path(dep_file).name
        content = safe_read_text(root / dep_file).lower()
        if not content:
            continue
        ev.evidence_files.append(dep_file)
        tool = _BUILD_TOOL_BY_FILE.get(fname)
        if tool and tool not in found["build_tools"]:
            found["build_tools"].append(tool)
        for category, name, keywords in _CONTENT_RULES:
            if name in found[category]:
                continue
            if any(kw.lower() in content for kw in keywords):
                found[category].append(name)

    ev.frameworks = found["frameworks"]
    ev.databases = found["databases"]
    ev.middlewares = found["middlewares"]
    ev.build_tools = found["build_tools"]
    ev.test_tools = found["test_tools"]

    deploy: list[str] = []
    for f in structure.docker_ci_files + structure.config_files:
        low = f.lower()
        for hint, name in _DEPLOY_RULES:
            if hint in low and name not in deploy:
                deploy.append(name)
                if f not in ev.evidence_files:
                    ev.evidence_files.append(f)
    ev.deployment = deploy

    ev.possible_architecture_style = _guess_style(ev, structure)
    return ev


def _guess_style(ev: TechStackEvidence, structure: RepoStructure) -> str:
    has_frontend = any(
        f in ev.frameworks for f in ("React", "Vue", "Angular", "Next.js", "Nuxt")
    )
    has_backend = any(
        f in ev.frameworks
        for f in ("Spring Boot", "FastAPI", "Flask", "Django", "Express", "NestJS", "Gin", "Echo")
    )
    has_ai = any(
        f in ev.frameworks
        for f in ("PyTorch", "TensorFlow", "Transformers", "LangChain", "LlamaIndex")
    )
    if has_ai:
        return "AI/LLM 应用或模型工程（推断）"
    if has_frontend and has_backend:
        return "前后端分离（推断）"
    if has_frontend:
        return "前端应用（推断）"
    if has_backend:
        return "后端服务（推断）"
    if structure.dependency_files:
        return "单体应用（推断，证据有限）"
    return "无法从依赖文件确定"
