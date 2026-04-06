import os
import sys
import tkinter as tk
import time
import threading
from tkinter import filedialog


def select_alarm_sound(app):
    """选择全局报警声音文件
    
    Args:
        app: 主应用实例
    """
    filetypes = [
        ("音频文件", "*.mp3 *.wav *.ogg *.flac"),
        ("所有文件", "*.*")
    ]
    
    filename = filedialog.askopenfilename(
        title="选择全局报警声音",
        filetypes=filetypes
    )

    if filename:
        app.alarm_sound_path.set(filename)
        app.logging_manager.log_message(f"已选择全局报警声音: {os.path.basename(filename)}")
        if hasattr(app, 'save_config') and callable(app.save_config):
            try:
                app.save_config()
            except Exception:
                pass


class AlarmModule:
    """报警模块"""
    def __init__(self, app):
        """
        初始化报警模块
        Args:
            app: 主应用实例
        """
        self.app = app
        # 检查pygame是否可用
        try:
            import pygame
            try:
                pygame.mixer.init()
                self.pygame_available = True
            except pygame.error:
                self.pygame_available = False
        except ImportError:
            self.pygame_available = False
    
    def get_default_alarm_sound_path(self):
        """
        获取默认的报警声音路径，使用项目自带的alarm.mp3

        支持Windows平台，同时支持打包后的环境

        Returns:
            str: 报警声音文件的路径
        """
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，获取项目根目录（modules的上一级目录）
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 构建跨平台的报警声音路径
        alarm_path = os.path.join(app_root, "voice", "alarm.mp3")

        # 确保路径格式正确
        alarm_path = os.path.normpath(alarm_path)

        return alarm_path
    
    def play_alarm_sound(self, alarm_var):
        """播放报警声音
        Args:
            alarm_var: 报警开关的BooleanVar变量
        """
        if not self.pygame_available:
            self.app.logging_manager.log_message("pygame库未安装，无法播放报警声音")
            return

        if not alarm_var.get():
            return

        sound_file = self.app.alarm_sound_path.get()
        if not sound_file or not os.path.exists(sound_file):
            self.app.logging_manager.log_message("未设置有效的全局报警声音文件")
            return

        try:
            import pygame
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(self.app.alarm_volume.get() / 100)  # 设置音量
            pygame.mixer.music.play()
            self.app.logging_manager.log_message("报警声音已播放")
        except Exception as e:
            self.app.logging_manager.log_message(f"播放报警声音失败: {str(e)}")

    def play_start_sound(self):
        """播放开始运行的音频"""
        if not self.pygame_available:
            self.app.logging_manager.log_message("pygame库未安装，无法播放开始运行音效")
            return

        # 直接使用固定的音频文件路径，不受报警声音设置的影响
        sound_file = self.get_default_alarm_sound_path()
        if not sound_file or not os.path.exists(sound_file):
            self.app.logging_manager.log_message("未找到默认音频文件，无法播放开始运行音效")
            return

        try:
            import pygame
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
            pygame.mixer.music.play()
        except Exception as e:
            self.app.logging_manager.log_message(f"播放开始运行音效失败: {str(e)}")

    def play_stop_sound(self):
        """播放停止运行的反向音频"""
        if not self.pygame_available:
            return

        try:
            import pygame
            # 获取程序运行目录
            if hasattr(sys, '_MEIPASS'):
                # 打包后的环境，使用_MEIPASS获取运行目录
                app_root = sys._MEIPASS
            else:
                # 开发环境，获取项目根目录（modules的上一级目录）
                app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # 构建跨平台的反向音频路径
            reversed_file = os.path.join(app_root, "voice", "temp_reversed.mp3")
            reversed_file = os.path.normpath(reversed_file)

            if os.path.exists(reversed_file):
                try:
                    pygame.mixer.music.load(reversed_file)
                    pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                    pygame.mixer.music.play()
                except pygame.error:
                    # 播放原始音频作为备选
                    sound_file = self.get_default_alarm_sound_path()
                    if sound_file and os.path.exists(sound_file):
                        try:
                            pygame.mixer.music.load(sound_file)
                            pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                            pygame.mixer.music.play()
                        except Exception:
                            pass
            else:
                # 如果反向音频文件不存在，播放原始音频
                sound_file = self.get_default_alarm_sound_path()
                if sound_file and os.path.exists(sound_file):
                    try:
                        pygame.mixer.music.load(sound_file)
                        pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                        pygame.mixer.music.play()
                    except Exception:
                        pass
        except Exception:
            pass
    
    def play_custom_alarm(self, sound_path=None, volume=None, repeat_count=1,
                         interval_ms=0, wait_complete=True):
        """
        播放自定义报警音
        
        Args:
            sound_path: 音频文件路径（None则使用全局默认）
            volume: 音量（0-100，None则使用全局音量）
            repeat_count: 重复次数（0=播放1次不重复，-1=无限循环，默认1次）
            interval_ms: 重复间隔（毫秒）
            wait_complete: 是否等待播放完成
        
        Returns:
            bool: 是否成功启动播放
        """
        if not self.pygame_available:
            if self.app and hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message("pygame库未安装，无法播放报警声音")
            return False
        
        actual_sound_path = sound_path
        if not actual_sound_path:
            actual_sound_path = self.app.alarm_sound_path.get() if hasattr(self.app, 'alarm_sound_path') else None
        
        if not actual_sound_path or not os.path.exists(actual_sound_path):
            actual_sound_path = self.get_default_alarm_sound_path()
        
        if not actual_sound_path or not os.path.exists(actual_sound_path):
            if self.app and hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message("未找到有效的音频文件")
            return False
        
        actual_volume = volume
        if actual_volume is None:
            actual_volume = self.app.alarm_volume.get() if hasattr(self.app, 'alarm_volume') else 70
        actual_volume = max(0, min(100, actual_volume)) / 100.0
        
        actual_repeat = max(1, repeat_count) if repeat_count != -1 else -1
        
        def _play_sound():
            try:
                import pygame
                play_count = 0
                while True:
                    if actual_repeat != -1 and play_count >= actual_repeat:
                        break
                    
                    if play_count > 0 and interval_ms > 0:
                        time.sleep(interval_ms / 1000.0)
                    
                    pygame.mixer.music.load(actual_sound_path)
                    pygame.mixer.music.set_volume(actual_volume)
                    pygame.mixer.music.play()
                    
                    play_count += 1
                    
                    if wait_complete or (actual_repeat == -1 or play_count < actual_repeat):
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.01)
                
                return True
            except Exception as e:
                if self.app and hasattr(self.app, 'logging_manager'):
                    self.app.logging_manager.log_message(f"播放报警音失败: {str(e)}")
                return False
        
        if wait_complete:
            return _play_sound()
        else:
            thread = threading.Thread(target=_play_sound, daemon=True)
            thread.start()
            return True
