from pathlib import Path

GAME_DIR = Path("./minecraft")
VERSION = "1.8.9"  # 默认版本，实际会被选择的版本覆盖
VERSION_DIR = GAME_DIR / "versions" / VERSION
LIBRARIES_DIR = GAME_DIR / "libraries"
NATIVES_DIR = VERSION_DIR / f"{VERSION}-natives"
ASSETS_DIR = GAME_DIR / "assets"

# 创建目录
GAME_DIR.mkdir(exist_ok=True)
