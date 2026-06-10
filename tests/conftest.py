import os
import subprocess
from pathlib import Path

import pytest


def _git(repo: Path, *args: str, author=None, date=None):
    env = os.environ.copy()
    env.setdefault("GIT_CONFIG_GLOBAL", "/dev/null")
    if author:
        name, email = author
        env.update({
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        })
    if date:
        env.update({"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, env=env,
    )


def _commit(repo: Path, message: str, files: dict[str, str], author, date):
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message, author=author, date=date)


ALICE = ("Alice Zhang", "alice@example.com")
BOB = ("Bob Li", "bob@example.com")


@pytest.fixture(scope="session")
def sample_repo(tmp_path_factory) -> Path:
    repo = tmp_path_factory.mktemp("sample_repo")
    _git(repo, "init", "-b", "main")

    _commit(
        repo,
        "init project scaffold",
        {
            "package.json": (
                '{"name": "order-shop", "dependencies": '
                '{"express": "^4.18.0", "mysql2": "^3.0.0", "redis": "^4.0.0"},'
                '"devDependencies": {"jest": "^29.0.0"}}'
            ),
            "README.md": "# order-shop\n\n一个简单的电商订单与支付后端服务。\n",
            ".gitignore": "node_modules/\n",
        },
        ALICE,
        "2025-01-05T10:00:00+08:00",
    )
    _commit(
        repo,
        "feat: 新增订单创建接口",
        {
            "src/service/order_service.js": "function createOrder() { return 'order'; }\n",
            "src/controller/order_controller.js": "function orderApi() {}\n",
        },
        ALICE,
        "2025-01-20T14:30:00+08:00",
    )
    _commit(
        repo,
        "feat: 实现订单状态流转",
        {
            "src/service/order_service.js":
                "function createOrder() { return 'order'; }\n"
                "function transitionState() {}\n",
        },
        ALICE,
        "2025-02-10T11:00:00+08:00",
    )
    _commit(
        repo,
        "fix: 修复支付回调空指针",
        {
            "src/service/payment_service.js": "function callback(data) { return data || {}; }\n",
        },
        BOB,
        "2025-02-15T23:30:00+08:00",
    )
    _commit(
        repo,
        "docs: update readme",
        {
            "README.md": "# order-shop\n\n一个简单的电商订单与支付后端服务。\n\n## 使用方式\n",
        },
        ALICE,
        "2025-03-01T09:00:00+08:00",
    )
    return repo
