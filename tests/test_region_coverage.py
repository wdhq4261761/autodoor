import pytest
from unittest.mock import MagicMock, patch
from utils import region


class TestRegionStartSelection:
    """测试区域选择启动"""
    
    def test_start_selection_normal(self, mock_app):
        """测试普通区域选择"""
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = False
        mock_app.root = MagicMock()
        mock_app.min_x = 0
        mock_app.min_y = 0
        
        with patch('screeninfo.get_monitors') as mock_monitors:
            mock_monitor = MagicMock()
            mock_monitor.x = 0
            mock_monitor.y = 0
            mock_monitor.width = 1920
            mock_monitor.height = 1080
            mock_monitors.return_value = [mock_monitor]
            
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_window = MagicMock()
                mock_toplevel.return_value = mock_window
                
                with patch('tkinter.Canvas') as mock_canvas:
                    mock_canvas_instance = MagicMock()
                    mock_canvas.return_value = mock_canvas_instance
                    
                    region._start_selection(mock_app, "normal", 0)
                    
                    assert mock_app.is_selecting is True
    
    def test_start_selection_number(self, mock_app):
        """测试数字区域选择"""
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = False
        mock_app.root = MagicMock()
        mock_app.current_number_region_index = None
        
        with patch('screeninfo.get_monitors') as mock_monitors:
            mock_monitor = MagicMock()
            mock_monitor.x = 0
            mock_monitor.y = 0
            mock_monitor.width = 1920
            mock_monitor.height = 1080
            mock_monitors.return_value = [mock_monitor]
            
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_window = MagicMock()
                mock_toplevel.return_value = mock_window
                
                with patch('tkinter.Canvas') as mock_canvas:
                    mock_canvas_instance = MagicMock()
                    mock_canvas.return_value = mock_canvas_instance
                    
                    region._start_selection(mock_app, "number", 0)
                    
                    assert mock_app.current_number_region_index == 0
    
    def test_start_selection_ocr(self, mock_app):
        """测试OCR区域选择"""
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = False
        mock_app.root = MagicMock()
        mock_app.current_ocr_region_index = None
        
        with patch('screeninfo.get_monitors') as mock_monitors:
            mock_monitor = MagicMock()
            mock_monitor.x = 0
            mock_monitor.y = 0
            mock_monitor.width = 1920
            mock_monitor.height = 1080
            mock_monitors.return_value = [mock_monitor]
            
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_window = MagicMock()
                mock_toplevel.return_value = mock_window
                
                with patch('tkinter.Canvas') as mock_canvas:
                    mock_canvas_instance = MagicMock()
                    mock_canvas.return_value = mock_canvas_instance
                    
                    region._start_selection(mock_app, "ocr", 0)
                    
                    assert mock_app.current_ocr_region_index == 0


class TestRegionMouseDown:
    """测试鼠标按下事件"""
    
    def test_on_mouse_down_saves_coordinates(self, mock_app):
        """测试保存坐标"""
        mock_app.min_x = 0
        mock_app.min_y = 0
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        region.on_mouse_down(mock_app, event)
        
        assert mock_app.start_x_abs == 100
        assert mock_app.start_y_abs == 200
        assert mock_app.start_x_rel == 100
        assert mock_app.start_y_rel == 200


class TestRegionMouseDrag:
    """测试鼠标拖动事件"""
    
    def test_on_mouse_drag_draws_rectangle(self, mock_app):
        """测试绘制矩形"""
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.start_x_rel = 50
        mock_app.start_y_rel = 50
        mock_app.canvas = MagicMock()
        mock_app.rect = None
        
        event = MagicMock()
        event.x_root = 200
        event.y_root = 300
        
        region.on_mouse_drag(mock_app, event)
        
        mock_app.canvas.create_rectangle.assert_called_once()
    
    def test_on_mouse_drag_deletes_old_rect(self, mock_app):
        """测试删除旧矩形"""
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.start_x_rel = 50
        mock_app.start_y_rel = 50
        mock_app.canvas = MagicMock()
        mock_app.rect = "old_rect"
        
        event = MagicMock()
        event.x_root = 200
        event.y_root = 300
        
        region.on_mouse_drag(mock_app, event)
        
        mock_app.canvas.delete.assert_called_with("old_rect")


class TestRegionSaveSelection:
    """测试保存区域选择"""
    
    def test_save_selection_valid_region(self, mock_app):
        """测试有效区域"""
        result = region._save_selection(mock_app, 0, 0, 100, 100)
        
        assert result == (0, 0, 100, 100)
    
    def test_save_selection_swapped_coords(self, mock_app):
        """测试交换坐标"""
        result = region._save_selection(mock_app, 100, 100, 0, 0)
        
        assert result == (0, 0, 100, 100)
    
    def test_save_selection_too_small(self, mock_app):
        """测试区域太小"""
        with patch('tkinter.messagebox.showwarning'):
            result = region._save_selection(mock_app, 0, 0, 5, 5)
            
            assert result is None


class TestRegionCancelSelection:
    """测试取消区域选择"""
    
    def test_cancel_selection_resets_state(self, mock_app):
        """测试重置状态"""
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.logging_manager = MagicMock()
        
        region.cancel_selection(mock_app)
        
        assert mock_app.is_selecting is False
        mock_app.select_window.destroy.assert_called_once()
    
    def test_cancel_selection_window_not_exists(self, mock_app):
        """测试窗口不存在"""
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = False
        mock_app.logging_manager = MagicMock()
        
        region.cancel_selection(mock_app)
        
        assert mock_app.is_selecting is False


class TestRegionMouseUp:
    """测试鼠标释放事件"""
    
    def test_on_mouse_up_ocr_selection(self, mock_app, create_mock_ocr_group):
        """测试OCR区域选择释放"""
        mock_app.selection_type = 'ocr'
        mock_app.current_ocr_region_index = 0
        mock_app.ocr_groups = [create_mock_ocr_group()]
        mock_app.ocr_groups[0]['region_var'] = MagicMock()
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.config_manager = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        assert mock_app.ocr_groups[0]['region'] == (0, 0, 100, 100)
    
    def test_on_mouse_up_color_selection(self, mock_app):
        """测试颜色区域选择释放"""
        mock_app.selection_type = 'color'
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.color_recognition_region = None
        mock_app.color_recognition_manager = MagicMock()
        mock_app.color_recognition_manager.color_recognition = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        assert mock_app.color_recognition_region == (0, 0, 100, 100)
    
    def test_on_mouse_up_color_selection_no_manager(self, mock_app):
        """测试颜色区域选择释放 - 无manager"""
        mock_app.selection_type = 'color'
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.color_recognition_region = None
        
        with patch('modules.color.ColorRecognitionManager') as mock_manager_class:
            mock_manager_instance = MagicMock()
            mock_manager_instance.color_recognition = None
            mock_manager_class.return_value = mock_manager_instance
            
            with patch('modules.color.ColorRecognition') as mock_recognition_class:
                mock_recognition = MagicMock()
                mock_recognition_class.return_value = mock_recognition
                
                event = MagicMock()
                event.x_root = 100
                event.y_root = 100
                
                region.on_mouse_up(mock_app, event)
                
                assert mock_app.color_recognition_region == (0, 0, 100, 100)
    
    def test_on_mouse_up_other_selection_type(self, mock_app):
        """测试其他选择类型"""
        mock_app.selection_type = 'other'
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.region_var = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        mock_app.region_var.set.assert_called_once_with("0,0,100,100")
    
    def test_on_mouse_up_no_selection_type(self, mock_app):
        """测试无选择类型"""
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.region_var = MagicMock()
        
        if hasattr(mock_app, 'selection_type'):
            delattr(mock_app, 'selection_type')
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        mock_app.region_var.set.assert_called_once_with("0,0,100,100")
    
    def test_on_mouse_up_ocr_invalid_index(self, mock_app, create_mock_ocr_group):
        """测试OCR区域选择释放 - 无效索引"""
        mock_app.selection_type = 'ocr'
        mock_app.current_ocr_region_index = 99
        mock_app.ocr_groups = [create_mock_ocr_group()]
        original_region = mock_app.ocr_groups[0]['region']
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        assert mock_app.ocr_groups[0]['region'] == original_region
    
    def test_on_mouse_up_color_with_region_var(self, mock_app):
        """测试颜色区域选择释放 - 有region_var"""
        mock_app.selection_type = 'color'
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.color_recognition_region = None
        mock_app.color_recognition_manager = MagicMock()
        mock_app.color_recognition_manager.color_recognition = MagicMock()
        mock_app.region_var = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        mock_app.region_var.set.assert_called_once_with("0,0,100,100")
    
    def test_on_mouse_up_with_config_manager(self, mock_app):
        """测试有配置管理器"""
        mock_app.selection_type = 'other'
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.min_x = 0
        mock_app.min_y = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        mock_app.region_var = MagicMock()
        mock_app.config_manager = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 100
        
        region.on_mouse_up(mock_app, event)
        
        mock_app.config_manager.defer_save_config.assert_called_once()


class TestNumberRegionMouseUp:
    """测试数字区域鼠标释放"""
    
    def test_on_number_region_mouse_up(self, mock_app, create_mock_number_region):
        """测试数字区域选择释放"""
        mock_app.current_number_region_index = 0
        mock_app.number_regions = [create_mock_number_region()]
        mock_app.number_regions[0]['region_var'] = MagicMock()
        mock_app.start_x_abs = 0
        mock_app.start_y_abs = 0
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = True
        mock_app.select_window = MagicMock()
        mock_app.select_window.winfo_exists.return_value = True
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 50
        
        region.on_number_region_mouse_up(mock_app, event)
        
        assert mock_app.number_regions[0]['region'] == (0, 0, 100, 50)
