"""可执行入口：contrib-skill 命令。"""
from .cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
