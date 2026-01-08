import sys
import os
import json

# 添加dist/autodoor目录到Python路径
dist_path = os.path.join(os.path.dirname(__file__), 'dist', 'autodoor')
sys.path.insert(0, dist_path)

# 检查打包后的应用程序目录
print(f"检查打包后的应用程序目录: {dist_path}")

# 检查是否存在配置文件
config_path = os.path.join(dist_path, 'autodoor_config.json')
print(f"配置文件路径: {config_path}")
print(f"配置文件是否存在: {os.path.exists(config_path)}")

# 检查是否存在alarm.mp3文件
alarm_path = os.path.join(dist_path, 'voice', 'alarm.mp3')
print(f"报警声音路径: {alarm_path}")
print(f"报警声音是否存在: {os.path.exists(alarm_path)}")

# 列出dist/autodoor目录下的主要文件
print("\ndist/autodoor目录下的主要文件:")
for file in os.listdir(dist_path):
    file_path = os.path.join(dist_path, file)
    if os.path.isfile(file_path):
        print(f"  - {file}")
    elif os.path.isdir(file_path) and not file.startswith('_internal'):
        print(f"  - {file}/ (目录)")
