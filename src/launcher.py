import requests
import json
import zipfile
import subprocess
import os
import sys
from pathlib import Path


# 1. 定义基本路径
GAME_DIR = Path("./minecraft")
VERSION = "1.8.9"
VERSION_DIR = GAME_DIR / "versions" / VERSION
LIBRARIES_DIR = GAME_DIR / "libraries"
NATIVES_DIR = VERSION_DIR / f"{VERSION}-natives"


# 2. 创建必要的文件夹
GAME_DIR.mkdir(exist_ok=True)
VERSION_DIR.mkdir(parents=True, exist_ok=True)
LIBRARIES_DIR.mkdir(parents=True, exist_ok=True)
NATIVES_DIR.mkdir(parents=True, exist_ok=True)


def download_json(url, file_path):
    """下载 JSON 文件"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()
        with open(file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
        print(f"JSON文件已保存至 {file_path}")
        return json_data
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_files(url, path):
    """下载 jar, assets  等文件到指定路径"""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if path.exists():
        print(f"  已存在: {path.name}")
        return True
    
    try:
        print(f"  下载中: {path.name}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  完成: {path.name}")
        return True
    except Exception as e:
        print(f"  下载失败: {path.name} - {e}")
        return False


def get_current_os():
    """获取当前操作系统（Mojang 的命名方式）"""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "osx"
    else:
        return "linux" 


def rule_matches(rule, current_os):
    """判断单条规则是否匹配当前系统"""
    if "os" not in rule:
        return True
    return rule["os"].get("name") == current_os


def is_library_allowed(library, current_os):
    """判断一个库是否允许在当前系统下载"""
    if "rules" not in library:
        return True
    
    allowed = False
    for rule in library["rules"]:
        if rule_matches(rule, current_os):
            if rule["action"] == "allow":
                allowed = True
            elif rule["action"] == "disallow":
                allowed = False
    
    return allowed

   
def build_classpath():
    """构建 classpath 字符串"""
    jar_files = []
    
    # 1. 添加所有 libraries jar
    for jar in LIBRARIES_DIR.rglob("*.jar"):
        jar_files.append(str(jar))
    
    # 2. 添加游戏本体 jar
    game_jar = VERSION_DIR / f"{VERSION}.jar"
    if game_jar.exists():
        jar_files.append(str(game_jar))
    
    # 3. 用系统分隔符连接
    separator = os.pathsep
    classpath = separator.join(jar_files)
    
    return classpath




# 主程序
if __name__ == "__main__":
    print("=== Aether Launcher ===")
    
    # 加载版本 JSON
    version_json_path = VERSION_DIR / f"{VERSION}.json"
    
    if not version_json_path.exists():
        print("正在下载版本信息...")
        version_url = "https://piston-meta.mojang.com/v1/packages/d546f1707a3f2b7d034eece5ea2e311eda875787/1.8.9.json"
        version_data = download_json(version_url, version_json_path)
    else:
        with open(version_json_path, "r") as f:
            version_data = json.load(f)
    
    if not version_data:
        print("无法加载版本信息")
        sys.exit(1)
    
    current_os = get_current_os()
    print(f"当前系统: {current_os}")
    print("-" * 50)
    
    # 4. 下载 game.jar
    print("\n正在下载游戏本体...")
    client_url = version_data["downloads"]["client"]["url"]
    client_path = VERSION_DIR / f"{VERSION}.jar"
    download_files(client_url, client_path)
    
    # 5. 下载所有 libraries
    print("\n正在下载 libraries...")
    for lib in version_data["libraries"]:
        name = lib.get("name", "unknown")
        
        if is_library_allowed(lib, current_os):
            # 处理普通 artifact
            if "artifact" in lib.get("downloads", {}):
                url = lib["downloads"]["artifact"]["url"]
                path = LIBRARIES_DIR / lib["downloads"]["artifact"]["path"]
                download_files(url, path)
            
            # 处理 natives（classifiers）
            if "classifiers" in lib.get("downloads", {}):
                classifiers = lib["downloads"]["classifiers"]
                # 查找匹配当前系统的 natives
                native_key = f"natives-{current_os}"
                if native_key in classifiers:
                    url = classifiers[native_key]["url"]
                    path = LIBRARIES_DIR / classifiers[native_key]["path"]
                    
                    # 下载 natives jar
                    if download_files(url, path):
                        # 解压到 NATIVES_DIR
                        print(f"  解压中: {path.name}")
                        with zipfile.ZipFile(path, 'r') as zip_ref:
                            zip_ref.extractall(NATIVES_DIR)
                        print(f"  解压完成到: {NATIVES_DIR}")
        else:
            print(f"跳过: {name}")
    
    # 6. 下载assets
    asset_index_url = version_data["assetIndex"]["url"]
    asset_index_path = VERSION_DIR / "asset_index.json"
    download_files(asset_index_url, asset_index_path)  # 用同一个函数

    # 读取索引
    with open(asset_index_path, "r") as f:
        asset_index = json.load(f)

    # 下载具体资源
    for key, value in asset_index["objects"].items():
        hash_val = value["hash"]
        sub_path = hash_val[:2]
        file_path = GAME_DIR / "assets" / "objects" / sub_path / hash_val
        url = f"https://resources.download.minecraft.net/{sub_path}/{hash_val}"
        download_files(url, file_path)

    print("下载完成")

    # 7. 构建classpath

    classpath = build_classpath()

    print(f"Classpath 长度: {len(classpath)} 字符")
    print(f"包含 {len(classpath.split(os.pathsep))} 个 jar 文件")


    # 8. 构建并启动

    # 1. 找到 Java 路径（先直接用 "java"）
    java_path = "java"  # Linux/Mac
    if sys.platform == "win32":
        java_path = "javaw.exe"  # Windows 用 javaw 不显示控制台

    # 2. 替换启动参数中的变量
    minecraft_args = version_data["minecraftArguments"]
    minecraft_args = minecraft_args.replace("${auth_player_name}", "AetherPlayer")
    minecraft_args = minecraft_args.replace("${version_name}", VERSION)
    minecraft_args = minecraft_args.replace("${game_directory}", str(GAME_DIR))
    minecraft_args = minecraft_args.replace("${assets_root}", str(GAME_DIR / "assets"))
    minecraft_args = minecraft_args.replace("${assets_index_name}", version_data["assetIndex"]["id"])
    minecraft_args = minecraft_args.replace("${auth_uuid}", "offline")
    minecraft_args = minecraft_args.replace("${auth_access_token}", "offline")
    minecraft_args = minecraft_args.replace("${user_properties}", "{}")
    minecraft_args = minecraft_args.replace("${user_type}", "legacy")

    # 3. 组装完整命令
    cmd = [
        java_path,
        f"-Djava.library.path={NATIVES_DIR}",
        "-cp", classpath,
        version_data["mainClass"]
    ] + minecraft_args.split()

    print("启动命令:")
    print(" ".join(cmd))

    # 4. 启动游戏
    print("\n正在启动 Minecraft...")
    try:
        # 使用 Popen 可以获取输出（方便调试）
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 实时打印游戏输出
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
    except FileNotFoundError:
        print("错误: 找不到 Java，请确保已安装 Java 8")
    except Exception as e:
        print(f"启动失败: {e}")
