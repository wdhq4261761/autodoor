import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_app():
    """创建模拟应用实例"""
    app = MagicMock()
    app.version = "2.1.0"
    app.is_running = False
    app.is_paused = False
    app.is_selecting = False
    app.system_stopped = False
    app.tesseract_path = ""
    app.tesseract_available = True
    
    app.logging_manager = MagicMock()
    app.logging_manager.log_message = MagicMock()
    
    app.config_manager = MagicMock()
    app.config_manager.get_config = MagicMock(return_value={})
    app.config_manager.save_config = MagicMock()
    
    app.input_controller = MagicMock()
    app.input_controller.key_press = MagicMock()
    app.input_controller.key_down = MagicMock()
    app.input_controller.key_up = MagicMock()
    app.input_controller.mouse_click = MagicMock()
    app.input_controller.mouse_move = MagicMock()
    
    app.alarm_module = MagicMock()
    app.alarm_module.play_alarm_sound = MagicMock()
    
    app.ocr_groups = []
    app.timed_groups = []
    app.number_regions = []
    
    app.status_labels = defaultdict(lambda: MagicMock())
    
    app.PRIORITIES = {
        "number": 5,
        "timed": 4,
        "ocr": 3,
        "color": 2,
        "script": 1
    }
    
    return app


@pytest.fixture
def mock_tk_var():
    """创建模拟Tkinter变量"""
    class MockVar:
        def __init__(self, value=None):
            self._value = value
        
        def get(self):
            return self._value
        
        def set(self, value):
            self._value = value
    
    return MockVar


@pytest.fixture
def create_mock_ocr_group(mock_tk_var):
    """创建模拟OCR组"""
    def _create(enabled=True, keywords="test", key="enter", interval="1", 
                delay_min="100", delay_max="200", alarm=False, region=(0, 0, 100, 100),
                pause="180", language="eng", click=False):
        return {
            "enabled": mock_tk_var(enabled),
            "keywords": mock_tk_var(keywords),
            "key": mock_tk_var(key),
            "interval": mock_tk_var(interval),
            "delay_min": mock_tk_var(delay_min),
            "delay_max": mock_tk_var(delay_max),
            "alarm": mock_tk_var(alarm),
            "region": region,
            "pause": mock_tk_var(pause),
            "language": mock_tk_var(language),
            "click": mock_tk_var(click),
        }
    return _create


@pytest.fixture
def create_mock_timed_group(mock_tk_var):
    """创建模拟定时组"""
    def _create(enabled=True, key="space", interval="5", 
                delay_min="100", delay_max="200", alarm=False, coords=None):
        return {
            "enabled": mock_tk_var(enabled),
            "key": mock_tk_var(key),
            "interval": mock_tk_var(interval),
            "delay_min": mock_tk_var(delay_min),
            "delay_max": mock_tk_var(delay_max),
            "alarm": mock_tk_var(alarm),
            "coords": coords or (100, 100),
            "click_enabled": mock_tk_var(False),
            "position_x": mock_tk_var(0),
            "position_y": mock_tk_var(0),
            "position_var": mock_tk_var("0,0"),
        }
    return _create


@pytest.fixture
def create_mock_number_region(mock_tk_var):
    """创建模拟数字识别区域"""
    def _create(enabled=True, threshold="500", key="f5", 
                region=(0, 0, 100, 30), delay_min="100", delay_max="200"):
        return {
            "enabled": mock_tk_var(enabled),
            "threshold": mock_tk_var(threshold),
            "key": mock_tk_var(key),
            "region": region,
            "delay_min": mock_tk_var(delay_min),
            "delay_max": mock_tk_var(delay_max),
        }
    return _create
