import os
import sys
import subprocess
import pytesseract
from tkinter import messagebox
from PIL import Image


class TesseractManager:
    """
    Tesseract管理类，负责管理Tesseract OCR引擎的配置和验证
    """
    
    def __init__(self, app):
        """
        初始化Tesseract管理器
        Args:
            app: 应用程序实例
        """
        self.app = app
    
    def get_default_tesseract_path(self):
        """
        获取默认的Tesseract路径，使用项目自带的tesseract
        Returns:
            str: Tesseract可执行文件的路径，如果未找到则返回空字符串
        """
        if hasattr(sys, '_MEIPASS'):
            app_root = sys._MEIPASS
        else:
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        possible_paths = self.app.platform_adapter.get_tesseract_paths(app_root)
        
        tesseract_path = ""
        for path in possible_paths:
            if os.path.exists(path):
                tesseract_path = path
                break

        if tesseract_path:
            possible_tessdata_paths = [
                os.path.join(os.path.dirname(tesseract_path), "tessdata"),
                os.path.join(app_root, "tessdata"),
                os.path.join(app_root, "tesseract", "tessdata"),
            ]
            
            for tessdata_path in possible_tessdata_paths:
                if os.path.exists(tessdata_path):
                    os.environ["TESSDATA_PREFIX"] = tessdata_path
                    break

        return tesseract_path
    
    def _validate_tesseract_path(self):
        """
        验证Tesseract路径有效性

        Returns:
            bool: 如果路径有效则返回True，否则返回False
        """
        if not self.app.tesseract_path:
            self.app.logging_manager.log_message("Tesseract路径未配置")
            return False

        if not os.path.exists(self.app.tesseract_path):
            self.app.logging_manager.log_message(f"Tesseract路径不存在: {self.app.tesseract_path}")
            return False

        if not os.path.isfile(self.app.tesseract_path):
            self.app.logging_manager.log_message(f"Tesseract路径不是文件: {self.app.tesseract_path}")
            return False

        return True
    
    def _check_tesseract_permissions(self):
        """
        检查Tesseract执行权限
        Returns:
            bool: 如果权限正确则返回True，否则返回False
        """
        if not self.app.platform_adapter.is_valid_tesseract_path(self.app.tesseract_path):
            self.app.logging_manager.log_message(f"Tesseract路径不是有效可执行文件: {self.app.tesseract_path}")
            return False
        return True

    def _check_tesseract_version(self):
        """
        检查Tesseract版本兼容性
        Returns:
            bool: 如果版本兼容则返回True，否则返回False
        """
        try:
            version_result = subprocess.run(
                [self.app.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            version_output = version_result.stdout.strip()
            if "tesseract" in version_output.lower():
                version_parts = version_output.split()
                if len(version_parts) >= 2:
                    version_str = version_parts[1]
                    try:
                        cleaned_version = version_str.lstrip('v')
                        major_version = int(cleaned_version.split('.')[0])
                        if major_version < 4:
                            self.app.logging_manager.log_message(f"Tesseract版本太旧 ({version_str})，建议使用4.x或更高版本")
                            return False
                    except (ValueError, IndexError):
                        pass
            return True
        except Exception as e:
            self.app.logging_manager.log_message(f"版本检查失败: {str(e)}")
            return False

    def _get_test_file_path(self):
        """
        获取测试文件路径
        Returns:
            str: 测试文件路径
        """
        return self.app.platform_adapter.get_test_file_path()

    def _cleanup_test_files(self, test_file_path):
        """
        清理测试文件
        Args:
            test_file_path: 测试文件路径
        """
        if os.path.exists(test_file_path):
            try:
                os.remove(test_file_path)
            except Exception as e:
                self.app.logging_manager.log_message(f"清理测试文件失败: {str(e)}")

    def _test_tesseract_functionality(self):
        """
        测试Tesseract基本功能
        Returns:
            bool: 如果功能测试通过则返回True，否则返回False
        """
        try:
            pytesseract.pytesseract.tesseract_cmd = self.app.tesseract_path

            test_file_path = self._get_test_file_path()
            test_image = Image.new('RGB', (100, 30), color='white')
            test_image.save(test_file_path)

            test_result = pytesseract.image_to_string(test_file_path, lang='eng', timeout=5)

            self._cleanup_test_files(test_file_path)
            return True
        except Exception as e:
            test_file_path = self._get_test_file_path()
            self._cleanup_test_files(test_file_path)
            self.app.logging_manager.log_message(f"功能测试失败: {str(e)}")
            return False

    def check_tesseract_availability(self):
        """
        检查Tesseract OCR是否可用

        包括：
        1. 路径有效性验证
        2. 版本兼容性检查
        3. 基础功能测试

        Returns:
            bool: 如果Tesseract OCR可用则返回True，否则返回False
        """
        if not self.app.tesseract_path:
            self.app.tesseract_path = self.get_default_tesseract_path()
            if not self.app.tesseract_path:
                self.app.logging_manager.log_message("Tesseract OCR未配置")
                return False
            else:
                if hasattr(self.app, 'config_manager') and self.app.config_manager:
                    self.app.config_manager.defer_save_config()

        try:
            if not self._validate_tesseract_path():
                return False

            if not self._check_tesseract_permissions():
                return False

            if not self._check_tesseract_version():
                return False

            if not self._test_tesseract_functionality():
                return False

            # 全局设置 pytesseract 路径，避免每次识别都重新初始化
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self.app.tesseract_path

            if hasattr(self.app, 'tesseract_path_var'):
                self.app.tesseract_path_var.set(self.app.tesseract_path)

            self.app.logging_manager.log_message(f"Tesseract OCR引擎就绪: {self.app.tesseract_path}")
            return True

        except subprocess.TimeoutExpired:
            self.app.logging_manager.log_message(f"Tesseract命令执行超时: {self.app.tesseract_path}")
            return False
        except subprocess.CalledProcessError as e:
            self.app.logging_manager.log_message(f"Tesseract命令执行失败: {e}")
            return False
        except FileNotFoundError:
            self.app.logging_manager.log_message(f"Tesseract可执行文件未找到: {self.app.tesseract_path}")
            return False
        except pytesseract.TesseractError as e:
            self.app.logging_manager.log_message(f"Tesseract OCR测试失败: {e}")
            return False
        except PermissionError as e:
            self.app.logging_manager.log_message(f"Tesseract权限错误: {str(e)}")
            return False
        except Exception as e:
            self.app.logging_manager.log_message(f"Tesseract检测发生未知错误: {str(e)}")
            return False

    def set_tesseract_path(self):
        """设置Tesseract OCR路径"""
        new_path = self.app.tesseract_path_var.get().strip()

        if not new_path:
            messagebox.showwarning("警告", "请输入有效的Tesseract路径！")
            return

        if not os.path.exists(new_path):
            messagebox.showwarning("警告", "指定的路径不存在！")
            return

        if not new_path.endswith("tesseract.exe"):
            messagebox.showwarning("警告", "请指定tesseract.exe可执行文件！")
            return

        try:
            # 测试新路径是否可用
            subprocess.run(
                [new_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )

            # 更新路径和配置
            self.app.tesseract_path = new_path
            pytesseract.pytesseract.tesseract_cmd = new_path
            self.app.tesseract_available = True

            self.app.logging_manager.log_message(f"已设置Tesseract路径: {new_path}")
            self.app.status_var.set("就绪")
            messagebox.showinfo("成功", "Tesseract路径设置成功！")

            if hasattr(self.app, 'config_manager') and self.app.config_manager:
                self.app.config_manager.defer_save_config()

        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showwarning("警告", "无法使用指定的Tesseract路径！")
            return
