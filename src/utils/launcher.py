"""启动器核心逻辑 - 基于 minecraft-launcher-lib"""
import minecraft_launcher_lib
import subprocess
import sys
from pathlib import Path

# 游戏目录
GAME_DIR = Path("./minecraft").absolute()

def get_version_list():
    """获取所有可用版本"""
    return minecraft_launcher_lib.utils.get_version_list()

def get_latest_version():
    """获取最新版本"""
    return minecraft_launcher_lib.utils.get_latest_version()

def is_version_installed(version):
    """检查版本是否已安装"""
    return minecraft_launcher_lib.utils.is_version_installed(version, str(GAME_DIR))

def install_version(version, callback=None):
    """安装指定版本"""
    def progress_callback(progress):
        if callback:
            callback(progress)
    
    minecraft_launcher_lib.install.install_minecraft_version(
        version, str(GAME_DIR), callback=progress_callback
    )

def get_installed_versions():
    """获取已安装的版本列表"""
    versions_dir = GAME_DIR / "versions"
    if not versions_dir.exists():
        return []
    
    installed = []
    for version_dir in versions_dir.iterdir():
        if version_dir.is_dir():
            version_id = version_dir.name
            game_jar = version_dir / f"{version_id}.jar"
            version_json = version_dir / f"{version_id}.json"
            if game_jar.exists() and version_json.exists():
                installed.append(version_id)
    return sorted(installed, reverse=True)

def launch_version(version, username="AetherPlayer", use_microsoft=False, login_data=None):
    """启动游戏"""
    options = {
        "username": username,
        "uuid": "",
        "token": ""
    }
    
    if use_microsoft and login_data:
        options["username"] = login_data.get("name", username)
        options["uuid"] = login_data.get("id", "")
        options["token"] = login_data.get("access_token", "")
    
    # 获取启动命令
    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
        version, str(GAME_DIR), options
    )
    
    # 启动游戏
    process = subprocess.Popen(
        minecraft_command,
        cwd=str(GAME_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    return process
