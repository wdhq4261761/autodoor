import json
import os
import datetime
import tkinter as tk
from ui.utils import update_group_style

class ConfigManager:
    """统一配置管理器类"""
    
    def __init__(self, app):
        """初始化配置管理器
        Args:
            app: AutoDoorOCR实例
        """
        self.app = app
        self.config_file_path = app.config_file_path
    
    def read_config(self):
        """读取配置文件
        Returns:
            dict or None: 如果成功读取则返回配置字典，否则返回None
        """
        if not os.path.exists(self.config_file_path):
            return None
        
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"开始加载配置: {self.config_file_path}")
            else:
                print(f"开始加载配置: {self.config_file_path}")
            return config
        except json.JSONDecodeError as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置文件格式错误: {self.config_file_path}，错误详情: {str(e)}")
            else:
                print(f"配置文件格式错误: {self.config_file_path}，错误详情: {str(e)}")
        except PermissionError:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"没有权限读取配置文件: {self.config_file_path}")
            else:
                print(f"没有权限读取配置文件: {self.config_file_path}")
        except IOError as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置文件IO错误: {str(e)}")
            else:
                print(f"配置文件IO错误: {str(e)}")
        except Exception as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置加载错误: {str(e)}")
            else:
                print(f"配置加载错误: {str(e)}")
        return None
    
    def save_config(self, config):
        """保存配置到文件
        Args:
            config: 配置字典
        Returns:
            bool: 如果保存成功则返回True，否则返回False
        """
        try:
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)

            # 写入配置文件，使用更紧凑的格式
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)

            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message("配置已保存")
            else:
                print("配置已保存")
            return True
        except PermissionError:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"没有权限写入配置文件: {self.config_file_path}")
            else:
                print(f"没有权限写入配置文件: {self.config_file_path}")
            return False
        except IOError as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置文件IO错误: {str(e)}")
            else:
                print(f"配置文件IO错误: {str(e)}")
            return False
        except Exception as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置保存错误: {str(e)}")
            else:
                print(f"配置保存错误: {str(e)}")
            return False
    
    def get_config_value(self, config, key_path, default=None):
        """获取配置值，支持嵌套路径
        Args:
            config: 配置字典
            key_path: 键路径，如 'tesseract.path' 或 ['tesseract', 'path']
            default: 默认值
        
        Returns:
            配置值
        """
        if isinstance(key_path, str):
            key_path = key_path.split('.')

        value = config
        for key in key_path:
            if isinstance(value, dict) and key in value:
                value = value[key]
                # 如果值为None，返回默认值
                if value is None:
                    return default
            else:
                return default
        return value
    
    def get_full_config(self):
        """获取完整的配置数据结构
        Returns:
            dict: 完整的配置字典
        """
        # 获取各部分配置
        timed_groups_config = self._get_timed_config()
        number_regions_config = self._get_number_config()

        # 完整的配置数据结构，确保所有配置项都被保存
        config = {
            'version': self.app.version,  # 使用应用版本号
            'last_save_time': datetime.datetime.now().isoformat(),
            # 基本OCR配置
            'ocr': self._get_ocr_config(),
            # Tesseract配置
            'tesseract': self._get_tesseract_config(),
            # 定时功能配置
            'timed_key_press': {
                'groups': timed_groups_config
            },
            # 数字识别配置
            'number_recognition': {
                'regions': number_regions_config
            },
            # 图像检测配置
            'image_detection': self._get_image_detection_config(),
            # 快捷键配置 - 新增
            'shortcuts': self._get_shortcuts_config(),
            # 报警功能配置
            'alarm': self._get_alarm_config(),
            # 首页功能状态勾选框配置
            'home_checkboxes': self._get_home_checkboxes_config(),
            # 脚本和颜色识别配置
            'script': self._get_script_config()
        }
        return config
    
    def load_tesseract_config(self, config):
        """加载Tesseract配置"""
        tesseract_path = self.get_config_value(config, 'tesseract.path')
        if not tesseract_path:
            # 兼容旧格式
            tesseract_path = config.get('tesseract_path')

        if tesseract_path and tesseract_path.strip():
            temp_path = tesseract_path.strip()
            # 检查路径是否存在
            if os.path.exists(temp_path):
                self.app.tesseract_path = temp_path
                if hasattr(self.app, 'logging_manager'):
                    self.app.logging_manager.log_message(f"从配置文件加载Tesseract路径: {self.app.tesseract_path}")
            else:
                if hasattr(self.app, 'logging_manager'):
                    self.app.logging_manager.log_message(f"配置文件中的Tesseract路径不存在: {temp_path}")
    
    def load_ocr_config(self, config):
        """加载OCR配置"""
        ocr_config = self.get_config_value(config, 'ocr', {})
        groups = self.get_config_value(ocr_config, 'groups', [])

        if isinstance(groups, list):
            for group in self.app.ocr_groups:
                group['frame'].destroy()
            self.app.ocr_groups.clear()

            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    self.app.ocr.create_group(i)
                    if i < len(self.app.ocr_groups):
                        for key, value in group_config.items():
                            if key in self.app.ocr_groups[i]:
                                if key == 'enabled':
                                    self.app.ocr_groups[i][key].set(value)
                                    group_frame = self.app.ocr_groups[i]['frame']
                                    update_group_style(group_frame, value)
                                elif key == 'region' and value is not None:
                                    try:
                                        region = tuple(value)
                                        self.app.ocr_groups[i][key] = region
                                        self.app.ocr_groups[i]['region_var'].set(f"{region[0]},{region[1]} - {region[2]},{region[3]}")
                                    except (TypeError, ValueError):
                                        if hasattr(self.app, 'logging_manager'):
                                            self.app.logging_manager.log_message(f"配置文件中的OCR区域格式错误: {value}")
                                else:
                                    if hasattr(self.app.ocr_groups[i][key], 'set'):
                                        self.app.ocr_groups[i][key].set(value)

            if len(self.app.ocr_groups) == 0:
                self.app.ocr.create_group(0)
    
    def load_timed_config(self, config):
        """加载定时功能配置"""
        timed_config = config.get('timed_key_press', {})
        groups = self.get_config_value(timed_config, 'groups', [])

        if isinstance(groups, list):
            for group in self.app.timed_groups:
                group['frame'].destroy()
            self.app.timed_groups.clear()

            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    self.app.timed.create_group(i)
                    if i < len(self.app.timed_groups):
                        for key, value in group_config.items():
                            if key in self.app.timed_groups[i]:
                                if key == 'enabled':
                                    self.app.timed_groups[i][key].set(value)
                                    group_frame = self.app.timed_groups[i]['frame']
                                    update_group_style(group_frame, value)
                                elif hasattr(self.app.timed_groups[i][key], 'set'):
                                    self.app.timed_groups[i][key].set(value)
                        
                        pos_x = group_config.get('position_x', 0)
                        pos_y = group_config.get('position_y', 0)
                        if pos_x != 0 or pos_y != 0:
                            self.app.timed_groups[i]['position_var'].set(f"{pos_x},{pos_y}")

            if len(self.app.timed_groups) == 0:
                self.app.timed.create_group(0)
    
    def load_number_config(self, config):
        """加载数字识别配置"""
        number_config = config.get('number_recognition', {})
        regions = self.get_config_value(number_config, 'regions', [])

        if isinstance(regions, list):
            for region in self.app.number_regions:
                region['frame'].destroy()
            self.app.number_regions.clear()

            for i, region_config in enumerate(regions):
                if isinstance(region_config, dict):
                    self.app.number.create_region(i)
                    if i < len(self.app.number_regions):
                        for key, value in region_config.items():
                            if key in self.app.number_regions[i]:
                                if key == 'enabled':
                                    self.app.number_regions[i][key].set(value)
                                    group_frame = self.app.number_regions[i]['frame']
                                    update_group_style(group_frame, value)
                                elif key == 'region' and value is not None:
                                    try:
                                        region = tuple(value)
                                        self.app.number_regions[i][key] = region
                                        self.app.number_regions[i]['region_var'].set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
                                    except (TypeError, ValueError):
                                        if hasattr(self.app, 'logging_manager'):
                                            self.app.logging_manager.log_message(f"配置文件中的数字识别区域格式错误: {value}")
                                elif hasattr(self.app.number_regions[i][key], 'set'):
                                    self.app.number_regions[i][key].set(value)

            if len(self.app.number_regions) == 0:
                self.app.number.create_region(0)
    
    def load_image_detection_config(self, config):
        """加载图像检测配置"""
        image_config = config.get('image_detection', {})
        groups = self.get_config_value(image_config, 'groups', [])
        
        if isinstance(groups, list):
            for group in self.app.image_groups:
                group['frame'].destroy()
            self.app.image_groups.clear()
            
            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    self.app.image.create_group(i)
                    if i < len(self.app.image_groups):
                        for key, value in group_config.items():
                            if key in self.app.image_groups[i]:
                                if key == 'enabled':
                                    self.app.image_groups[i][key].set(value)
                                    group_frame = self.app.image_groups[i]['frame']
                                    update_group_style(group_frame, value)
                                elif key == 'region' and value is not None:
                                    try:
                                        region = tuple(value)
                                        self.app.image_groups[i][key] = region
                                        self.app.image_groups[i]['region_var'].set(f"{region[0]},{region[1]} - {region[2]},{region[3]}")
                                    except (TypeError, ValueError):
                                        if hasattr(self.app, 'logging_manager'):
                                            self.app.logging_manager.log_message(f"配置文件中的图像检测区域格式错误: {value}")
                                elif key == 'reference_image' and value is not None:
                                    self._load_reference_image(i, value)
                                else:
                                    if hasattr(self.app.image_groups[i][key], 'set'):
                                        self.app.image_groups[i][key].set(value)
            
            if len(self.app.image_groups) == 0:
                self.app.image.create_group(0)
    
    def _load_reference_image(self, group_index, image_path):
        """加载参考图像（模板）"""
        import os
        
        try:
            import cv2
            CV2_AVAILABLE = True
        except ImportError:
            CV2_AVAILABLE = False
        
        if not CV2_AVAILABLE:
            self.app.logging_manager.log_message("[图像检测] 错误: OpenCV未安装，无法加载参考图像")
            return
        
        if os.path.exists(image_path):
            try:
                template = cv2.imread(image_path, cv2.IMREAD_COLOR)
                if template is None:
                    self.app.logging_manager.log_message(f"[图像检测] 无法读取图像文件: {image_path}")
                    return
                
                h, w = template.shape[:2]
                
                self.app.image_groups[group_index]["template_image"] = template
                self.app.image_groups[group_index]["reference_image"] = image_path
                self.app.image_groups[group_index]["image_path_var"].set(os.path.basename(image_path))
                
                self.app.logging_manager.log_message(f"[图像检测] 检测组{group_index + 1}已加载模板: {image_path}")
                self.app.logging_manager.log_message(f"[图像检测] 模板尺寸: {w}x{h}")
                
                from ui.image_tab import update_image_preview
                update_image_preview(self.app, group_index, image_path)
            except Exception as e:
                self.app.logging_manager.log_message(f"[图像检测] 加载参考图像失败: {str(e)}")
    
    def load_alarm_config(self, config):
        """
        加载报警配置
        Args:
            config: 配置字典
        """
        alarm_config = self.get_config_value(config, 'alarm', {})

        # 加载全局报警声音
        if 'sound' in alarm_config:
            self.app.alarm_sound_path.set(alarm_config['sound'])

        # 加载报警音量
        if 'volume' in alarm_config:
            self.app.alarm_volume.set(alarm_config['volume'])
            self.app.alarm_volume_str.set(str(alarm_config['volume']))

        # 加载各模块报警开关状态
        for module in ["ocr", "timed", "number"]:
            module_config = alarm_config.get(module, {})
            if 'enabled' in module_config:
                self.app.alarm_enabled[module].set(module_config['enabled'])
    
    def load_shortcuts_config(self, config):
        """加载快捷键配置"""
        shortcuts_config = self.get_config_value(config, 'shortcuts', {})
        if hasattr(self.app, 'start_shortcut_var') and 'start' in shortcuts_config:
            self.app.start_shortcut_var.set(shortcuts_config['start'])
        if hasattr(self.app, 'stop_shortcut_var') and 'stop' in shortcuts_config:
            self.app.stop_shortcut_var.set(shortcuts_config['stop'])
    
    def load_home_checkboxes_config(self, config):
        """加载首页勾选框配置"""
        if 'home_checkboxes' in config and hasattr(self.app, 'module_check_vars'):
            home_checkboxes = config['home_checkboxes']
            if home_checkboxes:
                for module in ['ocr', 'timed', 'number', 'image', 'script']:
                    if module in home_checkboxes:
                        self.app.module_check_vars[module].set(home_checkboxes[module])
    
    def load_script_config(self, config):
        """加载脚本和颜色识别配置"""
        script_config = self.get_config_value(config, 'script', {})

        # 加载脚本内容
        if 'script_content' in script_config and hasattr(self.app, 'script_text'):
            script_content = script_config['script_content']
            self.app.script_text.delete(1.0, 'end')
            self.app.script_text.insert(1.0, script_content)

        # 加载颜色识别命令内容
        if 'color_commands' in script_config and hasattr(self.app, 'color_commands'):
            color_commands_content = script_config['color_commands']
            self.app.color_commands.delete(1.0, 'end')
            self.app.color_commands.insert(1.0, color_commands_content)

        # 加载颜色识别区域
        if 'color_recognition_region' in script_config and script_config['color_recognition_region']:
            color_recognition_region = script_config['color_recognition_region']
            if hasattr(self.app, 'region_var'):
                try:
                    x1, y1, x2, y2 = color_recognition_region
                    self.app.region_var.set(f"({x1}, {y1}) - ({x2}, {y2})")
                    # 同时更新实际使用的属性
                    self.app.color_recognition_region = color_recognition_region
                except (TypeError, ValueError):
                    if hasattr(self.app, 'logging_manager'):
                        self.app.logging_manager.log_message(f"配置文件中的颜色识别区域格式错误: {color_recognition_region}")

        # 加载目标颜色
        if 'target_color' in script_config and script_config['target_color']:
            target_color = script_config['target_color']
            if hasattr(self.app, 'color_var'):
                try:
                    r, g, b = target_color
                    self.app.color_var.set(f"RGB({r}, {g}, {b})")
                    if hasattr(self.app, 'color_display'):
                        self.app.color_display.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
                    # 同时更新实际使用的属性
                    self.app.target_color = target_color
                except (TypeError, ValueError):
                    if hasattr(self.app, 'logging_manager'):
                        self.app.logging_manager.log_message(f"配置文件中的目标颜色格式错误: {target_color}")

        # 加载颜色容差
        if 'color_tolerance' in script_config and hasattr(self.app, 'tolerance_var'):
            color_tolerance = script_config['color_tolerance']
            try:
                self.app.tolerance_var.set(str(int(color_tolerance)))
            except (ValueError, TypeError):
                self.app.tolerance_var.set("10")

        # 加载检查间隔
        if 'color_interval' in script_config and hasattr(self.app, 'interval_var'):
            color_interval = script_config['color_interval']
            try:
                self.app.interval_var.set(str(int(color_interval)))
            except (ValueError, TypeError):
                self.app.interval_var.set("5")

        # 加载颜色识别启用状态
        if 'color_recognition_enabled' in script_config and hasattr(self.app, 'color_enabled'):
            color_recognition_enabled = script_config['color_recognition_enabled']
            self.app.color_enabled.set(bool(color_recognition_enabled))
        
        # 加载脚本运行的延迟设置
        if 'delay_var' in script_config and hasattr(self.app, 'delay_var'):
            try:
                self.app.delay_var.set(str(int(script_config['delay_var'])))
            except (ValueError, TypeError):
                self.app.delay_var.set('250')
        
        if 'combo_key_delay' in script_config and hasattr(self.app, 'combo_key_delay'):
            try:
                self.app.combo_key_delay.set(str(int(script_config['combo_key_delay'])))
            except (ValueError, TypeError):
                self.app.combo_key_delay.set('2500')
        
        if 'combo_after_delay' in script_config and hasattr(self.app, 'combo_after_delay'):
            try:
                self.app.combo_after_delay.set(str(int(script_config['combo_after_delay'])))
            except (ValueError, TypeError):
                self.app.combo_after_delay.set('300')
    
    def defer_save_config(self):
        """
        延迟保存配置，避免频繁保存
        """
        if not hasattr(self.app, 'root') or not self.app.root:
            return
        
        if not hasattr(self.app, '_save_config_timer'):
            self.app._save_config_timer = None
        
        if self.app._save_config_timer:
            try:
                self.app.root.after_cancel(self.app._save_config_timer)
            except Exception:
                pass
        
        try:
            self.app._save_config_timer = self.app.root.after(1000, self.app.save_config)
        except Exception:
            pass
    
    def _get_timed_config(self):
        """获取定时功能配置"""
        timed_groups_config = []
        for group in self.app.timed_groups:
            timed_groups_config.append({
                'enabled': group['enabled'].get(),
                'interval': group['interval'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'alarm': group['alarm'].get(),
                'click_enabled': group['click_enabled'].get(),
                'position_x': group['position_x'].get(),
                'position_y': group['position_y'].get(),
                'position': group['position_var'].get()
            })
        return timed_groups_config
    
    def _get_number_config(self):
        """获取数字识别配置"""
        number_regions_config = []
        for region_config in self.app.number_regions:
            number_regions_config.append({
                'enabled': region_config['enabled'].get(),
                'region': list(region_config['region']) if region_config['region'] else None,
                'threshold': region_config['threshold'].get(),
                'key': region_config['key'].get(),
                'delay_min': region_config['delay_min'].get(),
                'delay_max': region_config['delay_max'].get(),
                'alarm': region_config['alarm'].get()
            })
        return number_regions_config
    
    def _get_ocr_config(self):
        """获取OCR配置"""
        ocr_groups_config = []
        for group in self.app.ocr_groups:
            ocr_groups_config.append({
                'enabled': group['enabled'].get(),
                'region': list(group['region']) if group['region'] else None,
                'interval': group['interval'].get(),
                'pause': group['pause'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'alarm': group['alarm'].get(),
                'keywords': group['keywords'].get(),
                'language': group['language'].get(),
                'click': group['click'].get()
            })
        return {
            'groups': ocr_groups_config
        }
    
    def _get_image_detection_config(self):
        """获取图像检测配置"""
        image_groups_config = []
        for group in self.app.image_groups:
            image_groups_config.append({
                'enabled': group['enabled'].get(),
                'region': list(group['region']) if group['region'] else None,
                'reference_image': group.get('reference_image'),
                'threshold': group['threshold'].get(),
                'interval': group['interval'].get(),
                'pause': group['pause'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'alarm': group['alarm'].get(),
                'click': group['click'].get()
            })
        return {
            'groups': image_groups_config
        }
    
    def _get_tesseract_config(self):
        """获取Tesseract配置"""
        return {
            'path': self.app.tesseract_path
        }
    
    def _get_shortcuts_config(self):
        """获取快捷键配置"""
        return {
            'start': self.app.start_shortcut_var.get(),
            'stop': self.app.stop_shortcut_var.get()
        }
    
    def _get_alarm_config(self):
        """
        获取报警功能配置
        Returns:
            dict: 报警功能配置字典
        """
        return {
            'sound': self.app.alarm_sound_path.get(),
            'volume': self.app.alarm_volume.get(),
            'ocr': {
                'enabled': self.app.alarm_enabled['ocr'].get()
            },
            'timed': {
                'enabled': self.app.alarm_enabled['timed'].get()
            },
            'number': {
                'enabled': self.app.alarm_enabled['number'].get()
            }
        }
    
    def _get_home_checkboxes_config(self):
        """获取首页勾选框配置"""
        return {
            'ocr': self.app.module_check_vars['ocr'].get(),
            'timed': self.app.module_check_vars['timed'].get(),
            'number': self.app.module_check_vars['number'].get(),
            'image': self.app.module_check_vars.get('image', tk.BooleanVar(value=False)).get(),
            'script': self.app.module_check_vars.get('script', tk.BooleanVar(value=False)).get()
        }
    
    def _get_script_config(self):
        """获取脚本和颜色识别配置"""
        # 获取脚本内容
        script_content = ''
        if hasattr(self.app, 'script_text'):
            script_content = self.app.script_text.get(1.0, 'end')
        
        # 获取颜色识别命令内容
        color_commands_content = ''
        if hasattr(self.app, 'color_commands'):
            color_commands_content = self.app.color_commands.get(1.0, 'end')
        
        # 获取颜色识别区域
        color_recognition_region = None
        if hasattr(self.app, 'color_recognition_region'):
            color_recognition_region = self.app.color_recognition_region
        
        # 获取目标颜色
        target_color = None
        if hasattr(self.app, 'target_color'):
            target_color = self.app.target_color
        
        # 获取颜色容差
        color_tolerance = 10
        if hasattr(self.app, 'tolerance_var'):
            try:
                val = self.app.tolerance_var.get()
                color_tolerance = int(val) if val else 10
            except (ValueError, TypeError):
                color_tolerance = 10
        
        # 获取检查间隔
        color_interval = 5
        if hasattr(self.app, 'interval_var'):
            try:
                val = self.app.interval_var.get()
                color_interval = int(val) if val else 5
            except (ValueError, TypeError):
                color_interval = 5
        
        # 获取颜色识别启用状态
        color_recognition_enabled = False
        if hasattr(self.app, 'color_enabled'):
            color_recognition_enabled = self.app.color_enabled.get()
        
        # 获取脚本运行的延迟设置
        delay_var = '250'
        if hasattr(self.app, 'delay_var'):
            try:
                delay_var = str(int(self.app.delay_var.get()))
            except (ValueError, TypeError):
                delay_var = '250'
        
        combo_key_delay = '2500'
        if hasattr(self.app, 'combo_key_delay'):
            try:
                combo_key_delay = str(int(self.app.combo_key_delay.get()))
            except (ValueError, TypeError):
                combo_key_delay = '2500'
        
        combo_after_delay = '300'
        if hasattr(self.app, 'combo_after_delay'):
            try:
                combo_after_delay = str(int(self.app.combo_after_delay.get()))
            except (ValueError, TypeError):
                combo_after_delay = '300'
        
        return {
            'script_content': script_content,
            'color_commands': color_commands_content,
            'color_recognition_region': color_recognition_region,
            'target_color': target_color,
            'color_tolerance': color_tolerance,
            'color_interval': color_interval,
            'color_recognition_enabled': color_recognition_enabled,
            'delay_var': delay_var,
            'combo_key_delay': combo_key_delay,
            'combo_after_delay': combo_after_delay
        }
    
    def load_config(self):
        """
        加载配置
        增强错误处理，能够处理文件不存在、格式错误或路径配置缺失等异常情况
        确保加载所有前端设置，包括新增功能的相关配置
        支持新旧配置格式的兼容处理
        
        Returns:
            bool: 如果配置加载成功则返回True，否则返回False
        """
        config_loaded = False
        config_version = '1.0.0'
        config = None

        config = self.read_config()

        if config:
            config_loaded, config_version = self._process_config(config)

        if config_loaded and config:
            self._update_config_version(config, config_version)

        self._update_tesseract_path_var()

        return config_loaded
    
    def _process_config(self, config):
        """
        处理配置数据
        Args:
            config: 配置字典
        
        Returns:
            tuple: (config_loaded, config_version)
        """
        try:
            config_version = self.get_config_value(config, 'version', '1.0.0')
            self.app.logging_manager.log_message(f"配置版本: {config_version}")

            self.load_tesseract_config(config)
            self.load_ocr_config(config)
            self._load_click_config(config)
            self.load_timed_config(config)
            self.load_number_config(config)
            self.load_image_detection_config(config)
            self.load_alarm_config(config)
            self.load_shortcuts_config(config)
            self.load_home_checkboxes_config(config)
            self.load_script_config(config)

            self.app.logging_manager.log_message("配置加载成功")
            return True, config_version
        except Exception as e:
            self.app.logging_manager.log_message(f"处理配置时发生错误: {str(e)}")
            return False, '1.0.0'
    
    def _load_click_config(self, config):
        """加载点击模式和坐标配置（保持兼容性）"""
        pass
    
    def _update_config_version(self, config, config_version):
        """
        更新配置文件版本号
        Args:
            config: 配置字典
            config_version: 当前配置版本
        """
        if config_version != self.app.version:
            self.app.logging_manager.log_message(f"配置版本更新: {config_version} → {self.app.version}")
            config['version'] = self.app.version
            config['last_save_time'] = datetime.datetime.now().isoformat()
            try:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.app.logging_manager.log_message(f"更新配置版本失败: {str(e)}")
    
    def _update_tesseract_path_var(self):
        """更新界面中的Tesseract路径变量"""
        if hasattr(self.app, 'tesseract_path_var'):
            self.app.tesseract_path_var.set(self.app.tesseract_path)
    
    def setup_config_listeners(self):
        """为配置变量添加监听器，自动保存配置"""
        def immediate_save(*args):
            self.defer_save_config()

        def setup_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", immediate_save)
            if hasattr(group.get("key"), "trace_add"):
                group["key"].trace_add("write", immediate_save)
            group["delay_min"].trace_add("write", immediate_save)
            group["delay_max"].trace_add("write", immediate_save)
            group["alarm"].trace_add("write", immediate_save)
            group["click_enabled"].trace_add("write", immediate_save)

        for group in self.app.timed_groups:
            setup_group_listeners(group)

        self.app._setup_group_listeners = setup_group_listeners

        def setup_region_listeners(region_config):
            region_config["enabled"].trace_add("write", immediate_save)
            region_config["threshold"].trace_add("write", immediate_save)
            if hasattr(region_config.get("key"), "trace_add"):
                region_config["key"].trace_add("write", immediate_save)
            region_config["delay_min"].trace_add("write", immediate_save)
            region_config["delay_max"].trace_add("write", immediate_save)
            region_config["alarm"].trace_add("write", immediate_save)

        for region_config in self.app.number_regions:
            setup_region_listeners(region_config)

        self.app._setup_region_listeners = setup_region_listeners

        def setup_ocr_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", immediate_save)
            group["pause"].trace_add("write", immediate_save)
            if hasattr(group.get("key"), "trace_add"):
                group["key"].trace_add("write", immediate_save)
            group["delay_min"].trace_add("write", immediate_save)
            group["delay_max"].trace_add("write", immediate_save)
            group["alarm"].trace_add("write", immediate_save)
            group["keywords"].trace_add("write", immediate_save)
            group["language"].trace_add("write", immediate_save)
            group["click"].trace_add("write", immediate_save)

        for group in self.app.ocr_groups:
            setup_ocr_group_listeners(group)

        self.app._setup_ocr_group_listeners = setup_ocr_group_listeners

        def setup_image_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["threshold"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", immediate_save)
            group["pause"].trace_add("write", immediate_save)
            if hasattr(group.get("key"), "trace_add"):
                group["key"].trace_add("write", immediate_save)
            group["delay_min"].trace_add("write", immediate_save)
            group["delay_max"].trace_add("write", immediate_save)
            group["alarm"].trace_add("write", immediate_save)
            group["click"].trace_add("write", immediate_save)

        for group in self.app.image_groups:
            setup_image_group_listeners(group)

        self.app._setup_image_group_listeners = setup_image_group_listeners

        if hasattr(self.app, 'module_check_vars'):
            for module, var in self.app.module_check_vars.items():
                var.trace_add("write", immediate_save)

        if hasattr(self.app, 'start_shortcut_var'):
            self.app.start_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.app.setup_shortcuts()))
        if hasattr(self.app, 'stop_shortcut_var'):
            self.app.stop_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.app.setup_shortcuts()))

        if hasattr(self.app, 'script_text'):
            def on_script_change(event):
                if self.app.script_text.edit_modified():
                    immediate_save()
                    self.app.script_text.edit_modified(False)
            self.app.script_text.bind("<<Modified>>", on_script_change)
            self.app.script_text.edit_modified(False)

        if hasattr(self.app, 'color_commands'):
            def on_color_commands_change(event):
                if self.app.color_commands.edit_modified():
                    immediate_save()
                    self.app.color_commands.edit_modified(False)
            self.app.color_commands.bind("<<Modified>>", on_color_commands_change)
            self.app.color_commands.edit_modified(False)

        if hasattr(self.app, 'color_enabled'):
            self.app.color_enabled.trace_add("write", immediate_save)

        if hasattr(self.app, 'tolerance_var'):
            self.app.tolerance_var.trace_add("write", immediate_save)

        if hasattr(self.app, 'interval_var'):
            self.app.interval_var.trace_add("write", immediate_save)
        
        if hasattr(self.app, 'delay_var'):
            self.app.delay_var.trace_add("write", immediate_save)
        
        if hasattr(self.app, 'combo_key_delay'):
            self.app.combo_key_delay.trace_add("write", immediate_save)
        
        if hasattr(self.app, 'combo_after_delay'):
            self.app.combo_after_delay.trace_add("write", immediate_save)

    def clear_ocr_groups(self):
        """清空所有OCR组"""
        for group in self.app.ocr_groups:
            group['frame'].destroy()
        self.app.ocr_groups.clear()

    def load_group_config(self, group, group_config):
        """加载单个OCR组的配置
        Args:
            group: OCR组配置字典
            group_config: 从配置文件读取的组配置
        """
        from ui.utils import update_group_style

        def set_key_value(val):
            if hasattr(group['key'], 'set'):
                group['key'].set(val)
            elif hasattr(group['key'], 'configure'):
                group['key'].configure(state='normal')
                group['key'].delete(0, 'end')
                group['key'].insert(0, val)
                group['key'].configure(state='disabled')

        def safe_set_int(var, val, default=0):
            try:
                var.set(str(int(val)))
            except (ValueError, TypeError):
                var.set(str(default))

        config_mappings = {
            'enabled': lambda val: self.load_enabled_config(group, val),
            'region': lambda val: self.load_region_config(group, val),
            'interval': lambda val: safe_set_int(group['interval'], val, 5),
            'pause': lambda val: safe_set_int(group['pause'], val, 180),
            'key': set_key_value,
            'delay_min': lambda val: safe_set_int(group['delay_min'], val, 300),
            'delay_max': lambda val: safe_set_int(group['delay_max'], val, 500),
            'alarm': lambda val: group['alarm'].set(bool(val)),
            'keywords': lambda val: group['keywords'].set(str(val) if val else ''),
            'language': lambda val: group['language'].set(str(val) if val else 'eng'),
            'click': lambda val: group['click'].set(bool(val))
        }

        for key, setter in config_mappings.items():
            if key in group_config:
                setter(group_config[key])

    def load_enabled_config(self, group, enabled):
        """加载启用状态配置
        Args:
            group: OCR组配置字典
            enabled: 是否启用
        """
        from ui.utils import update_group_style

        group['enabled'].set(enabled)
        group_frame = group['frame']
        update_group_style(group_frame, enabled)

    def load_region_config(self, group, region):
        """加载区域配置
        Args:
            group: OCR组配置字典
            region: 区域坐标
        """
        if region is not None:
            try:
                region_tuple = tuple(region)
                group['region'] = region_tuple
                group['region_var'].set(f"{region_tuple[0]},{region_tuple[1]},{region_tuple[2]},{region_tuple[3]}")
            except (TypeError, ValueError):
                self.app.logging_manager.log_message(f"配置文件中的OCR区域格式错误: {region}")