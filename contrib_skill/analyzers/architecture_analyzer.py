"""ArchitectureAnalyzer：基于目录结构与技术栈推断架构风格。证据不足时明确说明。"""
from __future__ import annotations

from ..models import (
    ArchitectureEvidence,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    TechStackEvidence,
)
from .repo_scanner import RepoStructure

_LAYER_HINTS = {
    "controller": "Controller 层（接口/路由）",
    "api": "API 层",
    "service": "Service 层（业务逻辑）",
    "repository": "Repository 层（数据访问）",
    "mapper": "Mapper 层（数据访问）",
    "dao": "DAO 层（数据访问）",
    "model": "Model 层（数据模型）",
    "entity": "Entity 层（实体）",
    "domain": "Domain 层（领域模型）",
    "dto": "DTO（数据传输对象）",
    "view": "View 层",
    "component": "前端组件层",
    "router": "路由层",
    "middleware": "中间件层",
    "util": "工具层",
    "utils": "工具层",
}


def analyze_architecture(
    structure: RepoStructure, tech: TechStackEvidence
) -> ArchitectureEvidence:
    ev = ArchitectureEvidence()
    all_paths = structure.module_paths + structure.key_dirs
    path_text = " ".join(p.lower() for p in all_paths)

    # 分层识别
    layers_found: list[str] = []
    for hint, desc in _LAYER_HINTS.items():
        if hint in path_text and desc not in layers_found:
            layers_found.append(desc)
    ev.layer_analysis = layers_found

    # 架构风格判断（按证据强度排序）
    styles: list[str] = []
    has_frontend_dir = any(
        d in path_text for d in ("frontend", "client", "web/")
    ) or "web" in structure.top_dirs
    has_backend_dir = any(d in path_text for d in ("backend", "server"))
    multi_service = (
        len([f for f in structure.dependency_files if "/" in f.replace("\\", "/")]) >= 2
        and len(structure.top_dirs) >= 3
    )

    if "AI/LLM" in tech.possible_architecture_style:
        styles.append("AI Agent / LLM 应用架构")
    if multi_service and any("docker-compose" in f.lower() for f in structure.docker_ci_files):
        styles.append("多服务/微服务倾向（多个子目录含独立依赖文件 + docker-compose）")
    if has_frontend_dir and has_backend_dir:
        styles.append("前后端分离")
    elif "前后端分离" in tech.possible_architecture_style:
        styles.append("前后端分离（依赖层面推断）")
    if {"Controller 层（接口/路由）", "Service 层（业务逻辑）"} & set(layers_found):
        if any("数据访问" in l for l in layers_found):
            styles.append("经典分层架构（Controller-Service-DAO/Repository）")
        else:
            styles.append("MVC / Model-Service-Controller 倾向")
    if "Domain 层（领域模型）" in layers_found:
        styles.append("存在 DDD 倾向（出现 domain 目录，需结合代码确认）")
    if not styles:
        if structure.dependency_files:
            styles.append("单体应用（未发现服务拆分迹象）")
        else:
            styles.append("无法从代码中确定完整架构")

    ev.architecture_style = "；".join(styles)

    # 模块地图：取顶层/二级目录
    for mod in structure.module_paths[:30]:
        ev.module_map.setdefault(mod.split("/")[0], []).append(mod)

    # 依赖观察
    if tech.frameworks:
        ev.dependency_observations.append(
            f"主要框架：{', '.join(tech.frameworks)}（来自 {', '.join(tech.evidence_files[:3])}）"
        )
    if tech.databases:
        ev.dependency_observations.append(f"数据存储：{', '.join(tech.databases)}")
    if tech.middlewares:
        ev.dependency_observations.append(f"中间件：{', '.join(tech.middlewares)}")
    if not ev.dependency_observations:
        ev.dependency_observations.append("未能从依赖文件中识别出明确的框架与中间件")

    # 优势与风险（基于可见证据的保守判断）
    if layers_found:
        ev.architecture_strengths.append("目录体现出分层意识，职责划分有迹可循")
    if structure.test_dirs:
        ev.architecture_strengths.append(f"存在测试目录（{', '.join(structure.test_dirs[:3])}）")
    if tech.deployment:
        ev.architecture_strengths.append(f"具备部署配置：{', '.join(tech.deployment)}")
    if not structure.test_dirs:
        ev.architecture_risks.append("未发现测试目录，回归保障能力存疑")
    if not structure.readme_path:
        ev.architecture_risks.append("缺少 README，项目背景与使用方式无文档支撑")
    if not structure.docker_ci_files:
        ev.architecture_risks.append("未发现部署/CI 配置，交付方式无法从仓库确认")

    # 置信度
    if layers_found and tech.frameworks:
        ev.confidence = CONFIDENCE_HIGH if len(layers_found) >= 3 else CONFIDENCE_MEDIUM
    elif tech.frameworks or layers_found:
        ev.confidence = CONFIDENCE_MEDIUM
    else:
        ev.confidence = CONFIDENCE_LOW
        ev.architecture_style = "无法从代码中确定完整架构"
    return ev
