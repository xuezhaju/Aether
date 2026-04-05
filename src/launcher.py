import sys
import json
import subprocess
import zipfile
from pathlib import Path

from config import GAME_DIR
from downloader import download_file
from utils import (
    get_current_os, is_library_allowed,
    get_version_list, display_versions, select_version, download_version_json
)


def setup_version_paths(version_id):
    from config import GAME_DIR
    version_dir = GAME_DIR / "versions" / version_id
    libraries_dir = GAME_DIR / "libraries"
    natives_dir = version_dir / f"{version_id}-natives"
    assets_dir = GAME_DIR / "assets"
    version_dir.mkdir(parents=True, exist_ok=True)
    libraries_dir.mkdir(parents=True, exist_ok=True)
    natives_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return version_dir, libraries_dir, natives_dir, assets_dir


def download_game_jar(version_data, version_dir, version_id):
    print("\n正在下载游戏本体...")
    client_url = version_data["downloads"]["client"]["url"]
    client_path = version_dir / f"{version_id}.jar"
    download_file(client_url, client_path)


def download_all_libraries(version_data, current_os, libraries_dir, natives_dir):
    print("\n正在下载 libraries...")
    for lib in version_data["libraries"]:
        name = lib.get("name", "unknown")
        if is_library_allowed(lib, current_os):
            if "artifact" in lib.get("downloads", {}):
                url = lib["downloads"]["artifact"]["url"]
                path = libraries_dir / lib["downloads"]["artifact"]["path"]
                download_file(url, path)
            if "classifiers" in lib.get("downloads", {}):
                classifiers = lib["downloads"]["classifiers"]
                native_key = f"natives-{current_os}"
                if native_key in classifiers:
                    url = classifiers[native_key]["url"]
                    path = libraries_dir / classifiers[native_key]["path"]
                    if download_file(url, path):
                        print(f"  解压中: {path.name}")
                        with zipfile.ZipFile(path, 'r') as zip_ref:
                            zip_ref.extractall(natives_dir)
                        print(f"  解压完成到: {natives_dir}")
        else:
            print(f"跳过: {name}")


def download_all_assets(version_data, assets_dir):
    print("\n正在下载资源文件...")
    asset_index_id = version_data["assetIndex"]["id"]
    asset_index_url = version_data["assetIndex"]["url"]
    asset_index_path = assets_dir / "indexes" / f"{asset_index_id}.json"
    asset_index_path.parent.mkdir(parents=True, exist_ok=True)
    download_file(asset_index_url, asset_index_path)
    with open(asset_index_path, "r") as f:
        asset_index = json.load(f)
    assets_objects_dir = assets_dir / "objects"
    print(f"资源文件将保存到: {assets_objects_dir}")
    for key, value in asset_index["objects"].items():
        hash_val = value["hash"]
        sub_path = hash_val[:2]
        file_path = assets_objects_dir / sub_path / hash_val
        url = f"https://resources.download.minecraft.net/{sub_path}/{hash_val}"
        download_file(url, file_path)
    print("资源文件下载完成")


def build_launch_command(version_data, version_id, game_dir, version_dir, natives_dir, assets_dir, classpath):
    import sys as _sys
    import subprocess as _subprocess
    import shlex
    
    # 检测版本需要的 Java
    parts = version_id.split('.')
    if parts[0] == "1":
        major = int(parts[1])
    else:
        major = int(parts[0]) if parts[0].isdigit() else 0

    # 选择 Java 版本
    if version_id.startswith("26.") or major >= 25:
        # 最新快照需要 Java 26
        java_path = "/usr/lib/jvm/java-26-openjdk/bin/java"
        print(f"版本 {version_id} 需要 Java 26") 
    elif major >= 18 or version_id.startswith("1.18") or version_id.startswith("1.19") or version_id.startswith("1.20") or version_id.startswith("1.21"):
        java_paths = ["/usr/lib/jvm/java-17-openjdk/bin/java"]
        print(f"版本 {version_id} 需要 Java 17")
    else:
        java_paths = ["/usr/lib/jvm/java-8-openjdk/bin/java"]
        print(f"版本 {version_id} 需要 Java 8")    
    # 构建命令
    cmd = [java_path]
    
    # Java 17 不支持的参数列表
    unsupported_args = [
        "--sun-misc-unsafe-memory-access=allow",
        "--add-modules=jdk.incubator.vector",
        "-XX:+UseZGC",
        "-XX:+UseG1GC",
    ]
    
    # 添加 JVM 参数（过滤不支持的）
    if "arguments" in version_data and "jvm" in version_data["arguments"]:
        for arg in version_data["arguments"]["jvm"]:
            if isinstance(arg, str):
                # 跳过不支持的参数
                skip = False
                for unsupported in unsupported_args:
                    if unsupported in arg:
                        print(f"  跳过不支持的 JVM 参数: {arg}")
                        skip = True
                        break
                if skip:
                    continue
                # 替换变量
                arg = arg.replace("${natives_directory}", str(natives_dir))
                arg = arg.replace("${library_directory}", str(version_dir / "libraries"))
                arg = arg.replace("${classpath}", classpath)
                cmd.append(arg)
    
    # 添加基本参数
    cmd.append(f"-Djava.library.path={natives_dir}")
    cmd.extend(["-cp", classpath])
    cmd.append(version_data["mainClass"])
    
    # 添加游戏参数
    if "arguments" in version_data and "game" in version_data["arguments"]:
        for arg in version_data["arguments"]["game"]:
            if isinstance(arg, str):
                cmd.append(arg)
    else:
        minecraft_args = version_data.get("minecraftArguments", "")
        cmd.extend(shlex.split(minecraft_args))
    
    # 替换变量
    replacements = {
        "${auth_player_name}": "AetherPlayer",
        "${version_name}": version_id,
        "${game_directory}": str(game_dir),
        "${assets_root}": str(assets_dir),
        "${assets_index_name}": version_data["assetIndex"]["id"],
        "${auth_uuid}": "offline",
        "${auth_access_token}": "offline",
        "${user_properties}": "{}",
        "${user_type}": "legacy",
        "${resolution_width}": "854",
        "${resolution_height}": "480",
    }
    
    cmd_str = " ".join(cmd)
    for key, value in replacements.items():
        cmd_str = cmd_str.replace(key, value)
    
    cmd = shlex.split(cmd_str)
    
    # 打印最终命令（调试用）
    print(f"启动命令长度: {len(cmd)} 个参数")
    
    return cmd

def launch_game(cmd):
    print("\n正在启动 Minecraft...")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        for line in process.stdout:
            print(line, end='')
        process.wait()
    except FileNotFoundError:
        print("错误: 找不到 Java，请确保已安装 Java 8")
    except Exception as e:
        print(f"启动失败: {e}")


def download_version(version_id, version_url):
    """下载指定版本"""
    print(f"\n正在下载版本 {version_id}...")
    version_dir, libraries_dir, natives_dir, assets_dir = setup_version_paths(version_id)
    version_data = download_version_json(version_id, version_url, version_dir)
    current_os = get_current_os()
    
    download_game_jar(version_data, version_dir, version_id)
    download_all_libraries(version_data, current_os, libraries_dir, natives_dir)
    download_all_assets(version_data, assets_dir)
    
    print(f"\n✅ 版本 {version_id} 下载完成！")
    return version_data, version_dir, natives_dir, assets_dir


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
    return installed


def display_installed_versions(installed):
    """显示已安装的版本"""
    if not installed:
        print("暂无已安装的版本")
        return False
    
    print("\n已安装的版本：")
    print("-" * 40)
    for i, v in enumerate(installed):
        print(f"{i+1:3}. {v}")
    print("-" * 40)
    return True


def select_installed_version(installed):
    """选择要运行的已安装版本"""
    while True:
        try:
            choice = input("\n请选择要运行的版本（输入序号或版本号）: ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(installed):
                    return installed[idx]
                else:
                    print(f"序号超出范围，请输入 1-{len(installed)}")
                    continue
            
            # 直接匹配版本号
            for v in installed:
                if v == choice:
                    return v
            
            print(f"找不到版本 '{choice}'")
        except KeyboardInterrupt:
            print("\n已取消")
            return None


def main():
    print("=== Aether Launcher ===")
    
    while True:
        print("\n请选择操作：")
        print("1. 下载新版本")
        print("2. 运行已安装的版本")
        print("3. 退出")
        
        try:
            choice = input("\n请输入选项 (1/2/3): ").strip()
            
            if choice == "1":
                # 下载新版本
                versions = get_version_list()
                display_versions(versions, limit=20)
                version_id, version_url = select_version(versions)
                download_version(version_id, version_url)
                
            elif choice == "2":
                # 运行已安装的版本
                installed = get_installed_versions()
                if not display_installed_versions(installed):
                    print("请先下载版本（选择选项 1）")
                    continue
                
                version_id = select_installed_version(installed)
                if not version_id:
                    continue
                
                print(f"\n准备启动 {version_id}...")
                
                # 加载版本数据
                version_dir = GAME_DIR / "versions" / version_id
                version_json_path = version_dir / f"{version_id}.json"
                
                with open(version_json_path, "r") as f:
                    version_data = json.load(f)
                
                libraries_dir = GAME_DIR / "libraries"
                natives_dir = version_dir / f"{version_id}-natives"
                assets_dir = GAME_DIR / "assets"
                
                # 构建 classpath
                jar_files = []
                for jar in libraries_dir.rglob("*.jar"):
                    jar_files.append(str(jar))
                game_jar = version_dir / f"{version_id}.jar"
                if game_jar.exists():
                    jar_files.append(str(game_jar))
                classpath = ":".join(jar_files)
                
                print(f"Classpath 包含 {len(jar_files)} 个 jar 文件")
                
                # 启动游戏
                cmd = build_launch_command(version_data, version_id, GAME_DIR, version_dir, natives_dir, assets_dir, classpath)
                launch_game(cmd)
                
            elif choice == "3":
                print("再见！")
                break
            else:
                print("无效选项，请输入 1、2 或 3")
                
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    main()
