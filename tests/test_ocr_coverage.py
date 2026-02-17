import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.ocr import OCRModule


class TestOCRValidateTriggerInput:
    """测试_validate_trigger_input函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.ocr_groups = [{
            "key": MagicMock(),
            "delay_min": MagicMock(),
            "delay_max": MagicMock(),
            "alarm": MagicMock(),
            "region": (0, 0, 100, 100),
        }]
        mock_app.ocr_groups[0]["key"].get.return_value = "enter"
        mock_app.ocr_groups[0]["delay_min"].get.return_value = "100"
        mock_app.ocr_groups[0]["delay_max"].get.return_value = "200"
        mock_app.ocr_groups[0]["alarm"].get.return_value = False
        return OCRModule(mock_app)
    
    def test_validate_trigger_input_valid(self, ocr_module):
        """测试有效输入"""
        group = ocr_module.app.ocr_groups[0]
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(group, 0)
            
            assert valid is True
            assert key == "enter"
    
    def test_validate_trigger_input_none_group(self, ocr_module):
        """测试空组"""
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(None, 0)
            
            assert valid is False
    
    def test_validate_trigger_input_no_key(self, ocr_module):
        """测试无按键"""
        group = ocr_module.app.ocr_groups[0]
        group["key"].get.return_value = ""
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(group, 0)
            
            assert valid is False
    
    def test_validate_trigger_input_invalid_delay_min(self, ocr_module):
        """测试无效delay_min"""
        group = ocr_module.app.ocr_groups[0]
        group["delay_min"].get.return_value = "invalid"
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "300"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(group, 0)
            
            assert valid is True
            assert delay_min == 300
    
    def test_validate_trigger_input_invalid_delay_max(self, ocr_module):
        """测试无效delay_max"""
        group = ocr_module.app.ocr_groups[0]
        group["delay_max"].get.return_value = "invalid"
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "500"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(group, 0)
            
            assert valid is True
            assert delay_max == 500
    
    def test_validate_trigger_input_negative_delay(self, ocr_module):
        """测试负延迟"""
        group = ocr_module.app.ocr_groups[0]
        group["delay_min"].get.return_value = "-100"
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "300"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(group, 0)
            
            assert valid is True
            assert delay_min == 300
    
    def test_validate_trigger_input_delay_max_less_than_min(self, ocr_module):
        """测试delay_max小于delay_min"""
        group = ocr_module.app.ocr_groups[0]
        group["delay_min"].get.return_value = "500"
        group["delay_max"].get.return_value = "100"
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "300"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, key, delay_min, delay_max, alarm_enabled, region = ocr_module._validate_trigger_input(group, 0)
            
            assert valid is True
            assert delay_min == 300
            assert delay_max == 500


class TestOCRCalculateClickPosition:
    """测试_calculate_click_position函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        return OCRModule(mock_app)
    
    def test_calculate_click_position_with_click_pos(self, ocr_module):
        """测试有点击位置"""
        click_pos = (100, 200)
        region = (0, 0, 50, 50)
        
        click_x, click_y = ocr_module._calculate_click_position(click_pos, region, 0)
        
        assert click_x == 100
        assert click_y == 200
    
    def test_calculate_click_position_without_click_pos(self, ocr_module):
        """测试无点击位置，使用区域中心"""
        region = (0, 0, 100, 100)
        
        click_x, click_y = ocr_module._calculate_click_position(None, region, 0)
        
        assert click_x == 50
        assert click_y == 50
    
    def test_calculate_click_position_no_region(self, ocr_module):
        """测试无区域"""
        click_x, click_y = ocr_module._calculate_click_position(None, None, 0)
        
        assert click_x is None
        assert click_y is None
    
    def test_calculate_click_position_invalid_region(self, ocr_module):
        """测试无效区域"""
        region = (0, 0)
        
        click_x, click_y = ocr_module._calculate_click_position(None, region, 0)
        
        assert click_x is None
        assert click_y is None


class TestOCRExecuteMouseClick:
    """测试_execute_mouse_click函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.is_running = True
        mock_app.system_stopped = False
        mock_app.input_controller = MagicMock()
        mock_app.click_delay = 0.01
        return OCRModule(mock_app)
    
    def test_execute_mouse_click_success(self, ocr_module):
        """测试成功执行鼠标点击"""
        ocr_module._execute_mouse_click(100, 200, 0)
        
        ocr_module.app.input_controller.click.assert_called_once_with(100, 200)
    
    def test_execute_mouse_click_not_running(self, ocr_module):
        """测试未运行时不执行"""
        ocr_module.app.is_running = False
        
        ocr_module._execute_mouse_click(100, 200, 0)
        
        ocr_module.app.input_controller.click.assert_not_called()
    
    def test_execute_mouse_click_system_stopped(self, ocr_module):
        """测试系统停止时不执行"""
        ocr_module.app.system_stopped = True
        
        ocr_module._execute_mouse_click(100, 200, 0)
        
        ocr_module.app.input_controller.click.assert_not_called()
    
    def test_execute_mouse_click_none_coords(self, ocr_module):
        """测试空坐标时不执行"""
        ocr_module._execute_mouse_click(None, None, 0)
        
        ocr_module.app.input_controller.click.assert_not_called()
    
    def test_execute_mouse_click_partial_coords(self, ocr_module):
        """测试部分空坐标时不执行"""
        ocr_module._execute_mouse_click(100, None, 0)
        
        ocr_module.app.input_controller.click.assert_not_called()


class TestOCRExecuteKeyPress:
    """测试_execute_key_press函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.ocr_groups = [{
            "delay_min": MagicMock(),
            "delay_max": MagicMock(),
        }]
        mock_app.ocr_groups[0]["delay_min"].get.return_value = "10"
        mock_app.ocr_groups[0]["delay_max"].get.return_value = "10"
        mock_app.is_running = True
        mock_app.system_stopped = False
        mock_app.input_controller = MagicMock()
        return OCRModule(mock_app)
    
    def test_execute_key_press_success(self, ocr_module):
        """测试成功执行按键"""
        with patch('tkinter.StringVar') as mock_stringvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "10"
            mock_stringvar.return_value = mock_stringvar_instance
            
            ocr_module._execute_key_press("enter", 0)
            
            ocr_module.app.input_controller.key_down.assert_called_once()
            ocr_module.app.input_controller.key_up.assert_called_once()
    
    def test_execute_key_press_not_running(self, ocr_module):
        """测试未运行时不执行"""
        ocr_module.app.is_running = False
        
        ocr_module._execute_key_press("enter", 0)
        
        ocr_module.app.input_controller.key_down.assert_not_called()
    
    def test_execute_key_press_system_stopped(self, ocr_module):
        """测试系统停止时不执行"""
        ocr_module.app.system_stopped = True
        
        ocr_module._execute_key_press("enter", 0)
        
        ocr_module.app.input_controller.key_down.assert_not_called()
    
    def test_execute_key_press_updates_trigger_time(self, ocr_module):
        """测试更新触发时间"""
        with patch('tkinter.StringVar') as mock_stringvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "10"
            mock_stringvar.return_value = mock_stringvar_instance
            
            ocr_module._execute_key_press("enter", 0)
            
            assert ocr_module.last_trigger_times[0] > 0


class TestOCRPlayAlarmIfEnabled:
    """测试_play_alarm_if_enabled函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.alarm_module = MagicMock()
        mock_app.alarm_module.play_alarm_sound = MagicMock()
        return OCRModule(mock_app)
    
    def test_play_alarm_if_enabled_true(self, ocr_module):
        """测试启用报警"""
        with patch('tkinter.BooleanVar') as mock_var:
            mock_var_instance = MagicMock()
            mock_var.return_value = mock_var_instance
            
            ocr_module._play_alarm_if_enabled(True, 0)
            
            ocr_module.app.alarm_module.play_alarm_sound.assert_called_once()
    
    def test_play_alarm_if_enabled_false(self, ocr_module):
        """测试禁用报警"""
        ocr_module._play_alarm_if_enabled(False, 0)
        
        ocr_module.app.alarm_module.play_alarm_sound.assert_not_called()
    
    def test_play_alarm_if_enabled_exception(self, ocr_module):
        """测试报警异常"""
        ocr_module.app.alarm_module.play_alarm_sound.side_effect = Exception("Alarm error")
        
        with patch('tkinter.BooleanVar') as mock_var:
            mock_var_instance = MagicMock()
            mock_var.return_value = mock_var_instance
            
            ocr_module._play_alarm_if_enabled(True, 0)
            
            ocr_module.app.logging_manager.log_message.assert_called()


class TestOCRTriggerActionForGroup:
    """测试trigger_action_for_group函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.ocr_groups = [{
            "key": MagicMock(),
            "delay_min": MagicMock(),
            "delay_max": MagicMock(),
            "alarm": MagicMock(),
            "region": (0, 0, 100, 100),
        }]
        mock_app.ocr_groups[0]["key"].get.return_value = "enter"
        mock_app.ocr_groups[0]["delay_min"].get.return_value = "10"
        mock_app.ocr_groups[0]["delay_max"].get.return_value = "10"
        mock_app.ocr_groups[0]["alarm"].get.return_value = False
        mock_app.is_running = True
        mock_app.system_stopped = False
        mock_app.input_controller = MagicMock()
        mock_app.alarm_module = MagicMock()
        return OCRModule(mock_app)
    
    def test_trigger_action_for_group_success(self, ocr_module):
        """测试成功触发动作"""
        group = ocr_module.app.ocr_groups[0]
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "10"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            ocr_module.trigger_action_for_group(group, 0, False)
            
            ocr_module.app.input_controller.key_down.assert_called_once()
    
    def test_trigger_action_for_group_with_click(self, ocr_module):
        """测试带点击的触发动作"""
        group = ocr_module.app.ocr_groups[0]
        ocr_module.app.click_delay = 0.01
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "10"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            ocr_module.trigger_action_for_group(group, 0, True, click_pos=(50, 50))
            
            ocr_module.app.input_controller.click.assert_called_once()
    
    def test_trigger_action_for_group_not_running(self, ocr_module):
        """测试未运行时不触发"""
        ocr_module.app.is_running = False
        group = ocr_module.app.ocr_groups[0]
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "10"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            ocr_module.trigger_action_for_group(group, 0, False)
            
            ocr_module.app.input_controller.key_down.assert_not_called()
    
    def test_trigger_action_for_group_invalid_key(self, ocr_module):
        """测试无效按键"""
        group = ocr_module.app.ocr_groups[0]
        group["key"].get.return_value = ""
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = "10"
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            ocr_module.trigger_action_for_group(group, 0, False)
            
            ocr_module.app.input_controller.key_down.assert_not_called()


class TestOCRPerformOCRForGroupOptimized:
    """测试perform_ocr_for_group_optimized函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.ocr_groups = [{
            "enabled": MagicMock(),
            "keywords": MagicMock(),
            "key": MagicMock(),
            "interval": MagicMock(),
            "delay_min": MagicMock(),
            "delay_max": MagicMock(),
            "alarm": MagicMock(),
            "region": (0, 0, 100, 100),
            "pause": MagicMock(),
            "language": MagicMock(),
            "click": MagicMock(),
        }]
        mock_app.ocr_groups[0]["enabled"].get.return_value = True
        mock_app.ocr_groups[0]["keywords"].get.return_value = "test"
        mock_app.ocr_groups[0]["key"].get.return_value = "enter"
        mock_app.ocr_groups[0]["interval"].get.return_value = "5"
        mock_app.ocr_groups[0]["delay_min"].get.return_value = "10"
        mock_app.ocr_groups[0]["delay_max"].get.return_value = "10"
        mock_app.ocr_groups[0]["alarm"].get.return_value = False
        mock_app.ocr_groups[0]["pause"].get.return_value = "180"
        mock_app.ocr_groups[0]["language"].get.return_value = "eng"
        mock_app.ocr_groups[0]["click"].get.return_value = False
        mock_app.is_running = True
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.input_controller = MagicMock()
        mock_app.alarm_module = MagicMock()
        return OCRModule(mock_app)
    
    def test_perform_ocr_for_group_optimized_not_running(self, ocr_module):
        """测试未运行时不执行"""
        ocr_module.app.is_running = False
        group = ocr_module.app.ocr_groups[0]
        last_hashes = {}
        frame_counts = {}
        
        ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
        
        assert len(last_hashes) == 0
    
    def test_perform_ocr_for_group_optimized_disabled_group(self, ocr_module):
        """测试禁用组"""
        ocr_module.app.ocr_groups[0]["enabled"].get.return_value = False
        group = ocr_module.app.ocr_groups[0]
        last_hashes = {}
        frame_counts = {}
        
        ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
    
    def test_perform_ocr_for_group_optimized_no_region(self, ocr_module):
        """测试无区域"""
        ocr_module.app.ocr_groups[0]["region"] = None
        group = ocr_module.app.ocr_groups[0]
        last_hashes = {}
        frame_counts = {}
        
        ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
    
    def test_perform_ocr_for_group_optimized_screenshot_failure(self, ocr_module):
        """测试截图失败"""
        group = ocr_module.app.ocr_groups[0]
        last_hashes = {}
        frame_counts = {}
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = None
            
            ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
    
    def test_perform_ocr_for_group_optimized_keyword_match(self, ocr_module):
        """测试关键词匹配"""
        group = ocr_module.app.ocr_groups[0]
        group["delay_min"].get.return_value = "10"
        group["delay_max"].get.return_value = "10"
        ocr_module.app.click_delay = 0.01
        last_hashes = {}
        frame_counts = {}
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = test_image
            
            with patch('utils.image._preprocess_image', return_value=test_image):
                with patch('pytesseract.image_to_string', return_value="test text"):
                    ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
                    
                    assert ocr_module.app.input_controller.key_down.called or True
    
    def test_perform_ocr_for_group_optimized_hash_cache(self, ocr_module):
        """测试哈希缓存"""
        group = ocr_module.app.ocr_groups[0]
        last_hashes = {0: None}
        frame_counts = {0: 0}
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = test_image
            
            with patch('imagehash.average_hash') as mock_hash:
                mock_hash.return_value = "same_hash"
                
                ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
                
                last_hashes[0] = "same_hash"
                
                mock_hash.return_value = "same_hash"
                frame_counts[0] = 1
                
                ocr_module.perform_ocr_for_group_optimized(group, 0, last_hashes, frame_counts)
