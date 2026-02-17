import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from modules.alarm import AlarmModule, select_alarm_sound


class TestAlarmModuleInit:
    """AlarmModule初始化测试"""
    
    def test_init_with_pygame(self, mock_app):
        """测试pygame可用时的初始化"""
        mock_app.logging_manager = MagicMock()
        
        with patch.dict('sys.modules', {'pygame': MagicMock()}):
            with patch('pygame.mixer.init'):
                alarm_module = AlarmModule(mock_app)
                
                assert alarm_module.app is not None
    
    def test_init_without_pygame(self, mock_app):
        """测试pygame不可用时的初始化"""
        mock_app.logging_manager = MagicMock()
        
        with patch.dict('sys.modules', {'pygame': None}):
            with patch('builtins.__import__', side_effect=ImportError("No pygame")):
                alarm_module = AlarmModule(mock_app)
                
                assert alarm_module.pygame_available is False


class TestAlarmModuleDefaultSound:
    """默认报警声音测试"""
    
    @pytest.fixture
    def alarm_module(self, mock_app):
        return AlarmModule(mock_app)
    
    def test_get_default_alarm_sound_path_development(self, alarm_module):
        """测试开发环境默认声音路径"""
        path = alarm_module.get_default_alarm_sound_path()
        
        assert "voice" in path
        assert "alarm.mp3" in path
    
    def test_get_default_alarm_sound_path_packaged(self, alarm_module):
        """测试打包环境默认声音路径"""
        original_meipass = getattr(sys, '_MEIPASS', None)
        sys._MEIPASS = "/fake/app"
        
        try:
            path = alarm_module.get_default_alarm_sound_path()
            
            assert "voice" in path
            assert "alarm.mp3" in path
        finally:
            if original_meipass:
                sys._MEIPASS = original_meipass
            else:
                delattr(sys, '_MEIPASS')


class TestAlarmModulePlaySound:
    """播放声音测试"""
    
    @pytest.fixture
    def alarm_module(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.alarm_sound_path = MagicMock()
        mock_app.alarm_volume = MagicMock()
        mock_app.alarm_volume.get.return_value = 50
        return AlarmModule(mock_app)
    
    def test_play_alarm_sound_disabled(self, alarm_module):
        """测试报警禁用时不播放"""
        alarm_var = MagicMock()
        alarm_var.get.return_value = False
        
        alarm_module.play_alarm_sound(alarm_var)
        
        alarm_module.app.logging_manager.log_message.assert_not_called()
    
    def test_play_alarm_sound_no_pygame(self, alarm_module):
        """测试无pygame时不播放"""
        alarm_module.pygame_available = False
        alarm_var = MagicMock()
        alarm_var.get.return_value = True
        
        alarm_module.play_alarm_sound(alarm_var)
        
        alarm_module.app.logging_manager.log_message.assert_called()
    
    def test_play_alarm_sound_no_file(self, alarm_module):
        """测试无声音文件时不播放"""
        alarm_module.pygame_available = True
        alarm_module.app.alarm_sound_path.get.return_value = ""
        alarm_var = MagicMock()
        alarm_var.get.return_value = True
        
        alarm_module.play_alarm_sound(alarm_var)
        
        alarm_module.app.logging_manager.log_message.assert_called()
    
    def test_play_alarm_sound_file_not_exists(self, alarm_module):
        """测试声音文件不存在时不播放"""
        alarm_module.pygame_available = True
        alarm_module.app.alarm_sound_path.get.return_value = "/nonexistent/file.mp3"
        alarm_var = MagicMock()
        alarm_var.get.return_value = True
        
        with patch('os.path.exists', return_value=False):
            alarm_module.play_alarm_sound(alarm_var)
            
            alarm_module.app.logging_manager.log_message.assert_called()
    
    def test_play_alarm_sound_success(self, alarm_module):
        """测试成功播放报警声音"""
        alarm_module.pygame_available = True
        alarm_module.app.alarm_sound_path.get.return_value = "/path/to/sound.mp3"
        alarm_var = MagicMock()
        alarm_var.get.return_value = True
        
        mock_pygame = MagicMock()
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_alarm_sound(alarm_var)
                
                mock_pygame.mixer.music.load.assert_called_once()
                mock_pygame.mixer.music.play.assert_called_once()
    
    def test_play_alarm_sound_with_volume(self, alarm_module):
        """测试带音量播放"""
        alarm_module.pygame_available = True
        alarm_module.app.alarm_sound_path.get.return_value = "/path/to/sound.mp3"
        alarm_module.app.alarm_volume.get.return_value = 80
        alarm_var = MagicMock()
        alarm_var.get.return_value = True
        
        mock_pygame = MagicMock()
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_alarm_sound(alarm_var)
                
                mock_pygame.mixer.music.set_volume.assert_called_with(0.8)
    
    def test_play_alarm_sound_exception(self, alarm_module):
        """测试播放异常处理"""
        alarm_module.pygame_available = True
        alarm_module.app.alarm_sound_path.get.return_value = "/path/to/sound.mp3"
        alarm_var = MagicMock()
        alarm_var.get.return_value = True
        
        mock_pygame = MagicMock()
        mock_pygame.mixer.music.load.side_effect = Exception("Load error")
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_alarm_sound(alarm_var)
                
                alarm_module.app.logging_manager.log_message.assert_called()


class TestAlarmModuleStartSound:
    """开始声音测试"""
    
    @pytest.fixture
    def alarm_module(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return AlarmModule(mock_app)
    
    def test_play_start_sound_no_pygame(self, alarm_module):
        """测试无pygame时不播放开始声音"""
        alarm_module.pygame_available = False
        
        alarm_module.play_start_sound()
        
        alarm_module.app.logging_manager.log_message.assert_called()
    
    def test_play_start_sound_file_not_exists(self, alarm_module):
        """测试开始声音文件不存在"""
        alarm_module.pygame_available = True
        
        with patch('os.path.exists', return_value=False):
            alarm_module.play_start_sound()
            
            alarm_module.app.logging_manager.log_message.assert_called()
    
    def test_play_start_sound_success(self, alarm_module):
        """测试成功播放开始声音"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_start_sound()
                
                mock_pygame.mixer.music.load.assert_called_once()
                mock_pygame.mixer.music.set_volume.assert_called_with(0.7)
                mock_pygame.mixer.music.play.assert_called_once()
    
    def test_play_start_sound_exception(self, alarm_module):
        """测试播放开始声音异常"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        mock_pygame.mixer.music.load.side_effect = Exception("Load error")
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_start_sound()
                
                alarm_module.app.logging_manager.log_message.assert_called()


class TestAlarmModuleStopSound:
    """停止声音测试"""
    
    @pytest.fixture
    def alarm_module(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return AlarmModule(mock_app)
    
    def test_play_stop_sound_no_pygame(self, alarm_module):
        """测试无pygame时不播放停止声音"""
        alarm_module.pygame_available = False
        
        alarm_module.play_stop_sound()
    
    def test_play_stop_sound_reversed_exists(self, alarm_module):
        """测试反向音频文件存在"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
                
                mock_pygame.mixer.music.load.assert_called()
                mock_pygame.mixer.music.play.assert_called()
    
    def test_play_stop_sound_reversed_not_exists(self, alarm_module):
        """测试反向音频文件不存在，使用原始音频"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        def exists_side_effect(path):
            return "alarm.mp3" in path
        
        with patch('os.path.exists', side_effect=exists_side_effect):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
                
                mock_pygame.mixer.music.load.assert_called()
    
    def test_play_stop_sound_packaged_env(self, alarm_module):
        """测试打包环境停止声音"""
        alarm_module.pygame_available = True
        original_meipass = getattr(sys, '_MEIPASS', None)
        sys._MEIPASS = "/fake/app"
        
        mock_pygame = MagicMock()
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch.dict('sys.modules', {'pygame': mock_pygame}):
                    alarm_module.play_stop_sound()
                    
                    mock_pygame.mixer.music.load.assert_called()
        finally:
            if original_meipass:
                sys._MEIPASS = original_meipass
            else:
                delattr(sys, '_MEIPASS')
    
    def test_play_stop_sound_pygame_error(self, alarm_module):
        """测试pygame错误时回退"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        mock_pygame.mixer.music.load.side_effect = [mock_pygame.error, None]
        mock_pygame.error = Exception
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()


class TestSelectAlarmSound:
    """选择报警声音测试"""
    
    def test_select_alarm_sound_cancelled(self, mock_app):
        """测试取消选择"""
        mock_app.alarm_sound_path = MagicMock()
        mock_app.logging_manager = MagicMock()
        
        with patch('tkinter.filedialog.askopenfilename', return_value=""):
            select_alarm_sound(mock_app)
            
            mock_app.alarm_sound_path.set.assert_not_called()
    
    def test_select_alarm_sound_selected(self, mock_app):
        """测试选择声音文件"""
        mock_app.alarm_sound_path = MagicMock()
        mock_app.logging_manager = MagicMock()
        mock_app.save_config = MagicMock()
        
        with patch('tkinter.filedialog.askopenfilename', return_value="/path/to/sound.mp3"):
            select_alarm_sound(mock_app)
            
            mock_app.alarm_sound_path.set.assert_called_once_with("/path/to/sound.mp3")
            mock_app.save_config.assert_called_once()
    
    def test_select_alarm_sound_save_config_exception(self, mock_app):
        """测试保存配置异常"""
        mock_app.alarm_sound_path = MagicMock()
        mock_app.logging_manager = MagicMock()
        mock_app.save_config = MagicMock(side_effect=Exception("Save error"))
        
        with patch('tkinter.filedialog.askopenfilename', return_value="/path/to/sound.mp3"):
            select_alarm_sound(mock_app)
            
            mock_app.alarm_sound_path.set.assert_called_once()
