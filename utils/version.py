import requests
import json
import os
import threading
import time
import tkinter as tk
import webbrowser


def open_bilibili():
    """打开Bilibili主页"""
    webbrowser.open("https://space.bilibili.com/263150759")


def open_tool_intro():
    """打开工具介绍页面"""
    webbrowser.open("https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink")


class VersionChecker:
    def __init__(self, app):
        self.app = app
        self.current_version = app.version
        self.check_interval = 24 * 60 * 60  # 24小时
        self.ignored_version = None
        # 从配置中加载已忽略的版本
        self._load_ignored_version()

    def _load_ignored_version(self):
        """从配置中加载已忽略的版本"""
        try:
            # 直接从配置文件中读取
            config_file_path = getattr(self.app, 'config_file_path', None)
            if config_file_path and os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'update' in config:
                        self.ignored_version = config.get('update', {}).get('ignored_version')
        except Exception as e:
            try:
                self.app.logging_manager.log_message(f"加载已忽略版本失败: {str(e)}")
            except Exception:
                print(f"加载已忽略版本失败: {str(e)}")

    def check_for_updates(self, manual=False):
        """检查版本更新"""
        try:
            # 使用GitHub API获取最新版本
            url = "https://api.github.com/repos/wdhq4261761/autodoor/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get('tag_name', '')  # tag_name直接是版本号，如"1.5.0"

            # 提取下载链接
            windows_download_url = None

            for asset in data.get('assets', []):
                asset_name = asset.get('name', '')
                if 'windows' in asset_name.lower():
                    windows_download_url = asset.get('browser_download_url')

            # 比较版本
            if self._is_newer_version(latest_version):
                # 发现新版本
                # 检查版本是否已被忽略
                # 注意：手动检查更新时不受历史忽略状态的影响，始终显示最新版本信息
                if not manual and self.ignored_version:
                    ignored_comparison = self._compare_versions(self.ignored_version, latest_version)
                    if ignored_comparison <= 0:
                        # 版本已被忽略或相同，不显示更新通知
                        return
                
                # 显示更新通知
                self._show_update_notification(data, latest_version, windows_download_url)
            else:
                # 当前已是最新版本或开发版本
                if manual:
                    # 手动检查时显示反馈
                    self.show_no_update_notification()

        except Exception as e:
            try:
                self.app.logging_manager.log_message(f"版本检查失败: {str(e)}")
            except Exception:
                print(f"版本检查失败: {str(e)}")

    def _is_newer_version(self, latest):
        """检查是否为新版本"""
        return self._compare_versions(self.current_version, latest) == 1

    def _compare_versions(self, current, latest):
        """比较两个版本号
        返回值：
        - 1: 当前版本旧，需要更新
        - 0: 当前版本是最新
        - -1: 当前版本新（开发版本）
        """
        try:
            current_parts = list(map(int, current.split('.')))
            latest_parts = list(map(int, latest.split('.')))
            
            for i in range(max(len(current_parts), len(latest_parts))):
                current_val = current_parts[i] if i < len(current_parts) else 0
                latest_val = latest_parts[i] if i < len(latest_parts) else 0

                if current_val < latest_val:
                    return 1
                elif current_val > latest_val:
                    return -1

            return 0
        except:
            return 0

    def _show_update_notification(self, data, latest_version, windows_download_url):
        """显示更新通知"""
        def show_notification():
            release_date = data.get('published_at', '')
            changelog = data.get('body', '')
            download_url = 'https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink'

            # 格式化发布日期
            if release_date:
                try:
                    from datetime import datetime
                    release_date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    release_date_str = release_date_obj.strftime('%Y-%m-%d')
                except:
                    release_date_str = release_date
            else:
                release_date_str = '未知'

            # 简化更新内容
            changelog_summary = changelog[:500] + '...' if len(changelog) > 500 else changelog

            # 创建通知窗口
            notification_window = tk.Toplevel(self.app.root)
            notification_window.title("发现新版本")
            window_width = 450
            window_height = 400
            notification_window.geometry(f"{window_width}x{window_height}")
            notification_window.minsize(window_width, window_height)
            notification_window.transient(self.app.root)
            notification_window.grab_set()

            self.app.root.update_idletasks()
            self.app.root.update()
            
            root_x = self.app.root.winfo_rootx()
            root_y = self.app.root.winfo_rooty()
            root_width = self.app.root.winfo_width()
            root_height = self.app.root.winfo_height()

            if root_width < 100 or root_height < 100:
                root_width = 1050
                root_height = 700
                root_x = (notification_window.winfo_screenwidth() - root_width) // 2
                root_y = (notification_window.winfo_screenheight() - root_height) // 2

            pos_x = root_x + (root_width // 2) - (window_width // 2)
            pos_y = root_y + (root_height // 2) - (window_height // 2)

            notification_window.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

            # 添加内容
            frame = tk.ttk.Frame(notification_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)

            tk.ttk.Label(frame, text=f"发现新版本: v{latest_version}", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            tk.ttk.Label(frame, text=f"发布日期: {release_date_str}").pack(pady=(0, 10))
            tk.ttk.Label(frame, text="更新内容:", font=('Arial', 10, 'bold')).pack(anchor='w')

            # 添加滚动条的文本框
            text_frame = tk.ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            changelog_text = tk.Text(text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
            scrollbar = tk.ttk.Scrollbar(text_frame, command=changelog_text.yview)
            changelog_text.config(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            changelog_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            changelog_text.config(state=tk.NORMAL)
            changelog_text.insert(tk.END, changelog_summary)
            changelog_text.config(state=tk.DISABLED)

            # 添加按钮
            button_frame = tk.ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            tk.ttk.Button(button_frame, text="查看更新", command=lambda: self.open_update_link(download_url)).pack(side=tk.LEFT, padx=(0, 10))
            tk.ttk.Button(button_frame, text="稍后提醒", command=notification_window.destroy).pack(side=tk.LEFT, padx=(0, 10))
            tk.ttk.Button(button_frame, text="忽略此版本", command=lambda: self.ignore_version(latest_version, notification_window)).pack(side=tk.LEFT)

        def schedule_notification(retry_count=0):
            if not (hasattr(self.app, 'root') and self.app.root):
                print("显示更新通知失败: root 窗口未初始化")
                return
            try:
                self.app.root.after(0, show_notification)
            except Exception as e:
                if retry_count < 5:
                    threading.Timer(0.5, lambda: schedule_notification(retry_count + 1)).start()
                else:
                    print(f"显示更新通知失败: {str(e)}")

        schedule_notification()

    def open_update_link(self, url):
        """打开更新链接"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            try:
                self.app.logging_manager.log_message(f"打开更新链接失败: {str(e)}")
            except Exception:
                print(f"打开更新链接失败: {str(e)}")

    def ignore_version(self, version, notification_window):
        """忽略指定版本"""
        try:
            # 直接更新配置文件
            config_file_path = getattr(self.app, 'config_file_path', None)
            if config_file_path:
                # 确保配置文件目录存在
                os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
                
                # 无论配置文件操作是否成功，都先设置 ignored_version 属性
                self.ignored_version = version
                
                # 读取现有配置
                if os.path.exists(config_file_path):
                    try:
                        with open(config_file_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    except json.JSONDecodeError:
                        # 配置文件格式错误，使用空配置
                        config = {}
                else:
                    config = {}
                
                # 更新被忽略的版本
                if 'update' not in config:
                    config['update'] = {}
                config['update']['ignored_version'] = version
                
                # 保存配置
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False, default=str)
                
                try:
                    self.app.logging_manager.log_message(f"已忽略版本: {version}")
                except Exception:
                    print(f"已忽略版本: {version}")
        except Exception as e:
            try:
                self.app.logging_manager.log_message(f"忽略版本失败: {str(e)}")
            except Exception:
                print(f"忽略版本失败: {str(e)}")
        finally:
            # 无论是否发生异常，都关闭通知窗口
            notification_window.destroy()

    def show_no_update_notification(self):
        """显示无更新通知"""
        def show_notification():
            # 创建通知窗口
            notification_window = tk.Toplevel(self.app.root)
            notification_window.title("检查更新")
            notification_window.geometry("300x150")
            notification_window.transient(self.app.root)
            notification_window.grab_set()
            
            self.app.root.update_idletasks()
            self.app.root.update()
            
            root_x = self.app.root.winfo_rootx()
            root_y = self.app.root.winfo_rooty()
            root_width = self.app.root.winfo_width()
            root_height = self.app.root.winfo_height()
            
            if root_width < 100 or root_height < 100:
                root_width = 1050
                root_height = 700
                root_x = (notification_window.winfo_screenwidth() - root_width) // 2
                root_y = (notification_window.winfo_screenheight() - root_height) // 2
            
            dialog_width = 300
            dialog_height = 150
            pos_x = root_x + (root_width // 2) - (dialog_width // 2)
            pos_y = root_y + (root_height // 2) - (dialog_height // 2)
            
            notification_window.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
            
            # 添加内容
            frame = tk.ttk.Frame(notification_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            tk.ttk.Label(frame, text="检查更新", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            tk.ttk.Label(frame, text="当前已是最新版本！", wraplength=260).pack(pady=(0, 15))
            
            # 添加按钮
            button_frame = tk.ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            tk.ttk.Button(button_frame, text="确定", command=notification_window.destroy).pack()

        def schedule_notification(retry_count=0):
            if not (hasattr(self.app, 'root') and self.app.root):
                print("显示无更新通知失败: root 窗口未初始化")
                return
            try:
                self.app.root.after(0, show_notification)
            except Exception as e:
                if retry_count < 5:
                    threading.Timer(0.5, lambda: schedule_notification(retry_count + 1)).start()
                else:
                    print(f"显示无更新通知失败: {str(e)}")

        schedule_notification()

    def start_auto_check(self):
        """启动一次性版本检查线程，检查完成后自动退出"""
        def check_once():
            time.sleep(2)
            self.check_for_updates()
        
        thread = threading.Thread(target=check_once, daemon=True)
        thread.start()
