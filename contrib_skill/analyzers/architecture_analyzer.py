"""ArchitectureAnalyzer：基于目录结构与技术栈推断架构风格。证据不足时明确说明。"""
from __future__ import annotations

from ..models import (
    ArchitectureEvidence,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    TechStackEvidence,
    Commit,
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
    structure: RepoStructure,
    tech: TechStackEvidence,
    commits: list[Commit] | None = None,
) -> ArchitectureEvidence:
    ev = ArchitectureEvidence()
    all_paths = structure.module_paths + structure.key_dirs
    path_text = " ".join(p.lower() for p in all_paths)
    historical_paths = [
        path.replace("\\", "/").lower()
        for commit in (commits or [])
        for path in commit.changed_files
    ]
    pattern_paths = [p.replace("\\", "/").lower() for p in all_paths] + historical_paths

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
    layer_set = set(layers_found)
    has_controller = "Controller 层（接口/路由）" in layer_set
    has_service = "Service 层（业务逻辑）" in layer_set
    has_model = any(name in layer_set for name in ("Model 层（数据模型）", "Entity 层（实体）"))
    if has_controller and has_service:
        if any("数据访问" in l for l in layers_found):
            styles.append("经典分层架构（Controller-Service-DAO/Repository）")
        elif has_model:
            styles.append("MVC / Model-Service-Controller 架构")
        else:
            styles.append("Controller-Service 分层架构")
    elif has_controller and has_model:
        styles.append("MVC 架构")
    ev.design_patterns, ev.pattern_evidence = _detect_design_patterns(pattern_paths)
    if "DDD 领域驱动设计" in ev.design_patterns:
        styles.append("DDD 分层架构（领域模型与配套分层证据）")
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


def _detect_design_patterns(paths: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    corpus = " ".join(paths)
    patterns: list[str] = []
    evidence: dict[str, list[str]] = {}

    def add(name: str, hints: tuple[str, ...]) -> None:
        hits = [path for path in paths if any(hint in path for hint in hints)]
        if hits:
            patterns.append(name)
            evidence[name] = list(dict.fromkeys(hits))[:5]

    if "controller" in corpus and "service" in corpus:
        add("分层架构", ("controller", "service"))
    if "controller" in corpus and any(word in corpus for word in ("/model/", "/entity/", "model/", "entity/")):
        add("MVC 架构", ("controller", "/model/", "/entity/", "model/", "entity/"))
    has_domain = any(part in corpus for part in ("/domain/", "domain/", "/domain"))
    has_ddd_companion = any(
        part in corpus for part in ("repository", "entity", "aggregate", "application", "infrastructure")
    )
    if has_domain and has_ddd_companion:
        add("DDD 领域驱动设计", ("domain", "repository", "entity", "aggregate", "application", "infrastructure"))

    rules = (
        ("Repository 模式", ("repository",)),
        ("DAO 模式", ("/dao/",)),
        ("Data Mapper 模式", ("mapper",)),
        ("策略模式", ("strategy", "策略")),
        ("工厂模式", ("factory", "工厂")),
        ("适配器模式", ("adapter", "适配器")),
        ("观察者模式", ("observer", "listener", "观察者")),
        ("责任链模式", ("handler_chain", "chain_of_responsibility", "责任链")),
        ("命令模式", ("command", "命令模式")),
        ("模板方法模式", ("template_method", "template-method", "模板方法")),
    )
    for name, hints in rules:
        add(name, hints)
    return list(dict.fromkeys(patterns)), evidence
