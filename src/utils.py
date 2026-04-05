import sys
import os
import json
import requests
from config import LIBRARIES_DIR, VERSION_DIR, VERSION


def get_current_os():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "osx"
    else:
        return "linux"


def rule_matches(rule, current_os):
    if "os" not in rule:
        return True
    return rule["os"].get("name") == current_os


def is_library_allowed(library, current_os):
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
    jar_files = []
    for jar in LIBRARIES_DIR.rglob("*.jar"):
        jar_files.append(str(jar))
    game_jar = VERSION_DIR / f"{VERSION}.jar"
    if game_jar.exists():
        jar_files.append(str(game_jar))
    return os.pathsep.join(jar_files)


def get_version_list():
    manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    print("正在获取版本列表...")
    response = requests.get(manifest_url)
    response.raise_for_status()
    manifest = response.json()
    versions = []
    for v in manifest["versions"]:
        versions.append({
            "id": v["id"],
            "type": v["type"],
            "url": v["url"]
        })
    return versions


def display_versions(versions, limit=20):
    print(f"\n可用版本（最新 {limit} 个）：")
    print("-" * 40)
    for i, v in enumerate(versions[:limit]):
        type_mark = "📦" if v["type"] == "release" else "🔧"
        print(f"{i+1:3}. {type_mark} {v['id']} ({v['type']})")
    print("-" * 40)


def select_version(versions):
    while True:
        try:
            choice = input("\n请输入版本号（如 1.8.9）或序号（1-20）: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(versions):
                    return versions[idx]["id"], versions[idx]["url"]
                else:
                    print(f"序号超出范围，请输入 1-{len(versions)}")
                    continue
            for v in versions:
                if v["id"] == choice:
                    return v["id"], v["url"]
            print(f"找不到版本 '{choice}'，请重新输入")
        except KeyboardInterrupt:
            print("\n已取消")
            sys.exit(0)


def download_version_json(version_id, version_url, version_dir):
    version_json_path = version_dir / f"{version_id}.json"
    if not version_json_path.exists():
        print(f"正在下载 {version_id} 版本信息...")
        response = requests.get(version_url)
        response.raise_for_status()
        version_data = response.json()
        with open(version_json_path, 'w') as f:
            json.dump(version_data, f, indent=4)
        print(f"版本信息已保存至 {version_json_path}")
    else:
        print(f"版本信息已存在: {version_json_path}")
        with open(version_json_path, "r") as f:
            version_data = json.load(f)
    return version_data
