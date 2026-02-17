import pytest
from unittest.mock import MagicMock, patch
from modules.alarm import AlarmModule


class TestAlarmPlayStopSound:
    """测试play_stop_sound函数"""
    
    @pytest.fixture
    def alarm_module(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return AlarmModule(mock_app)
    
    def test_play_stop_sound_no_pygame(self, alarm_module):
        """测试无pygame时不播放"""
        alarm_module.pygame_available = False
        
        alarm_module.play_stop_sound()
    
    def test_play_stop_sound_reversed_file_exists(self, alarm_module):
        """测试反向音频文件存在"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        def exists_side_effect(path):
            return "alarm_reversed.mp3" in path or "alarm.mp3" in path
        
        with patch('os.path.exists', side_effect=exists_side_effect):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
                
                mock_pygame.mixer.music.load.assert_called()
                mock_pygame.mixer.music.play.assert_called()
    
    def test_play_stop_sound_reversed_file_not_exists(self, alarm_module):
        """测试反向音频文件不存在，使用原始音频"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        def exists_side_effect(path):
            return "alarm.mp3" in path and "alarm_reversed.mp3" not in path
        
        with patch('os.path.exists', side_effect=exists_side_effect):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
                
                mock_pygame.mixer.music.load.assert_called()
                mock_pygame.mixer.music.set_volume.assert_called_with(0.7)
    
    def test_play_stop_sound_both_files_not_exists(self, alarm_module):
        """测试两个音频文件都不存在"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        with patch('os.path.exists', return_value=False):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
                
                mock_pygame.mixer.music.load.assert_not_called()
    
    def test_play_stop_sound_pygame_error_reversed(self, alarm_module):
        """测试pygame错误时回退"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        mock_pygame.mixer.music.load.side_effect = [mock_pygame.error, None]
        mock_pygame.error = Exception
        
        def exists_side_effect(path):
            return True
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
    
    def test_play_stop_sound_exception_handling(self, alarm_module):
        """测试异常处理"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        mock_pygame.mixer.music.load.side_effect = Exception("Load error")
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
    
    def test_play_stop_sound_packaged_env(self, alarm_module):
        """测试打包环境"""
        import sys
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
    
    def test_play_stop_sound_sets_volume(self, alarm_module):
        """测试设置音量"""
        alarm_module.pygame_available = True
        
        mock_pygame = MagicMock()
        
        with patch('os.path.exists', return_value=True):
            with patch.dict('sys.modules', {'pygame': mock_pygame}):
                alarm_module.play_stop_sound()
                
                mock_pygame.mixer.music.set_volume.assert_called_with(0.7)
