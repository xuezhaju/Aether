import requests
import json
import sys
import zipfile
from config import GAME_DIR, VERSION, VERSION_DIR, LIBRARIES_DIR, NATIVES_DIR, ASSETS_DIR
from utils import get_current_os, is_library_allowed


def download_json(url, file_path):
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


def download_file(url, path):
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


def load_version_data():
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
    return version_data
