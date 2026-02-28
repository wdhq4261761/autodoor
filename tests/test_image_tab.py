import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from PIL import Image


class TestImageTab:
    """图像检测标签页测试"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟应用实例"""
        app = Mock()
        app.content_area = Mock()
        app.pages = {}
        app.image_groups = []
        app.image_groups_frame = None
        app.logging_manager = Mock()
        app.config_manager = Mock()
        app.config_manager.defer_save_config = Mock()
        return app
    
    @pytest.fixture
    def mock_group(self):
        """创建模拟检测组"""
        class MockVar:
            def __init__(self, value=None):
                self._value = value
            
            def get(self):
                return self._value
            
            def set(self, value):
                self._value = value
        
        return {
            "frame": Mock(),
            "enabled": MockVar(False),
            "region_var": MockVar("未选择区域"),
            "region": None,
            "reference_image": None,
            "reference_hash": None,
            "image_path_var": MockVar("未选择图像"),
            "threshold": MockVar("5"),
            "interval": MockVar("5"),
            "pause": MockVar("180"),
            "key": MockVar("equal"),
            "delay_min": MockVar("300"),
            "delay_max": MockVar("500"),
            "alarm": MockVar(False),
            "click": MockVar(True),
            "title_label": Mock(),
            "image_preview": Mock()
        }
    
    def test_create_image_tab_structure(self, mock_app):
        """测试创建图像检测标签页的结构"""
        with patch('ui.image_tab.ctk.CTkFrame') as mock_frame, \
             patch('ui.image_tab.ctk.CTkScrollableFrame') as mock_scroll, \
             patch('ui.image_tab.AnimatedButton') as mock_btn, \
             patch('ui.image_tab.create_image_group') as mock_create_group:
            
            mock_frame_instance = Mock()
            mock_frame.return_value = mock_frame_instance
            mock_scroll_instance = Mock()
            mock_scroll.return_value = mock_scroll_instance
            
            from ui.image_tab import create_image_tab
            create_image_tab(mock_app)
            
            assert 'image' in mock_app.pages
            assert mock_create_group.call_count == 2
    
    def test_toggle_group_bg_enabled(self):
        """测试启用组背景色切换"""
        from ui.image_tab import toggle_group_bg
        
        mock_frame = Mock()
        toggle_group_bg(mock_frame, True)
        
        mock_frame.configure.assert_called_once()
    
    def test_toggle_group_bg_disabled(self):
        """测试禁用组背景色切换"""
        from ui.image_tab import toggle_group_bg
        
        mock_frame = Mock()
        toggle_group_bg(mock_frame, False)
        
        mock_frame.configure.assert_called_once()
    
    def test_renumber_image_groups(self, mock_app):
        """测试重新编号图像检测组"""
        from ui.image_tab import renumber_image_groups
        
        mock_label1 = Mock()
        mock_label2 = Mock()
        
        mock_app.image_groups = [
            {"title_label": mock_label1},
            {"title_label": mock_label2}
        ]
        
        renumber_image_groups(mock_app)
        
        mock_label1.configure.assert_called_with(text='检测组 1')
        mock_label2.configure.assert_called_with(text='检测组 2')
    
    def test_add_image_group_limit(self, mock_app):
        """测试添加检测组数量限制"""
        from ui.image_tab import add_image_group
        
        mock_app.image_groups = [Mock() for _ in range(15)]
        
        initial_count = len(mock_app.image_groups)
        add_image_group(mock_app)
        
        assert len(mock_app.image_groups) == initial_count
    
    def test_delete_image_group_with_confirm(self, mock_app, mock_group):
        """测试删除图像检测组（需确认）"""
        from ui.image_tab import delete_image_group
        
        mock_frame = Mock()
        mock_group["frame"] = mock_frame
        mock_app.image_groups = [mock_group]
        
        with patch('tkinter.messagebox.askyesno', return_value=False):
            delete_image_group(mock_app, mock_frame, confirm=True)
        
        assert len(mock_app.image_groups) == 1
        
        with patch('tkinter.messagebox.askyesno', return_value=True):
            delete_image_group(mock_app, mock_frame, confirm=True)
        
        assert len(mock_app.image_groups) == 0
    
    def test_delete_image_group_without_confirm(self, mock_app, mock_group):
        """测试删除图像检测组（无需确认）"""
        from ui.image_tab import delete_image_group
        
        mock_frame = Mock()
        mock_group["frame"] = mock_frame
        mock_app.image_groups = [mock_group]
        
        delete_image_group(mock_app, mock_frame, confirm=False)
        
        assert len(mock_app.image_groups) == 0
    
    def test_start_image_region_selection(self, mock_app):
        """测试开始选择图像检测区域"""
        from ui.image_tab import start_image_region_selection
        
        with patch('utils.region._start_selection') as mock_selection:
            start_image_region_selection(mock_app, 0)
            mock_selection.assert_called_once_with(mock_app, "image", 0)


class TestSelectReferenceImage:
    """选择参考图像测试"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟应用实例"""
        app = Mock()
        app.logging_manager = Mock()
        app.config_manager = Mock()
        app.config_manager.defer_save_config = Mock()
        return app
    
    @pytest.fixture
    def mock_group(self):
        """创建模拟检测组"""
        class MockVar:
            def __init__(self, value=None):
                self._value = value
            
            def get(self):
                return self._value
            
            def set(self, value):
                self._value = value
        
        return {
            "reference_image": None,
            "reference_hash": None,
            "image_path_var": MockVar("未选择图像"),
            "image_preview": Mock()
        }
    
    def test_select_reference_image_valid(self, mock_app, mock_group):
        """测试选择有效的参考图像"""
        from ui.image_tab import select_reference_image
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            image = Image.new('RGB', (100, 100), color='white')
            image.save(temp_path)
        
        try:
            mock_app.image_groups = [mock_group]
            
            with patch('tkinter.filedialog.askopenfilename', return_value=temp_path):
                with patch('ui.image_tab.update_image_preview'):
                    select_reference_image(mock_app, 0)
            
            assert mock_group["reference_image"] == temp_path
            assert mock_group["reference_hash"] is not None
            mock_app.logging_manager.log_message.assert_called()
        finally:
            os.unlink(temp_path)
    
    def test_select_reference_image_cancelled(self, mock_app, mock_group):
        """测试取消选择参考图像"""
        from ui.image_tab import select_reference_image
        
        mock_app.image_groups = [mock_group]
        
        with patch('tkinter.filedialog.askopenfilename', return_value=''):
            select_reference_image(mock_app, 0)
        
        assert mock_group["reference_image"] is None
    
    def test_select_reference_image_invalid(self, mock_app, mock_group):
        """测试选择无效的参考图像"""
        from ui.image_tab import select_reference_image
        
        mock_app.image_groups = [mock_group]
        
        with patch('tkinter.filedialog.askopenfilename', return_value='/nonexistent/path.png'):
            select_reference_image(mock_app, 0)
        
        mock_app.logging_manager.log_message.assert_called()


class TestUpdateImagePreview:
    """更新图像预览测试"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟应用实例"""
        app = Mock()
        app.logging_manager = Mock()
        return app
    
    def test_update_image_preview_valid(self, mock_app):
        """测试更新有效的图像预览"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            image = Image.new('RGB', (100, 100), color='white')
            image.save(temp_path)
        
        try:
            mock_preview = Mock()
            mock_group = {"image_preview": mock_preview}
            mock_app.image_groups = [mock_group]
            
            with patch('ui.image_tab.ImageTk.PhotoImage') as mock_photo:
                mock_photo.return_value = Mock()
                from ui.image_tab import update_image_preview
                update_image_preview(mock_app, 0, temp_path)
                
                mock_preview.configure.assert_called_once()
        finally:
            os.unlink(temp_path)
    
    def test_update_image_preview_invalid_index(self, mock_app):
        """测试无效索引的图像预览更新"""
        from ui.image_tab import update_image_preview
        
        mock_app.image_groups = []
        
        update_image_preview(mock_app, 0, "/some/path.png")
        
    def test_update_image_preview_no_preview(self, mock_app):
        """测试无预览组件时的更新"""
        from ui.image_tab import update_image_preview
        
        mock_group = {"image_preview": None}
        mock_app.image_groups = [mock_group]
        
        update_image_preview(mock_app, 0, "/some/path.png")
    
    def test_update_image_preview_nonexistent_file(self, mock_app):
        """测试文件不存在时的预览更新"""
        from ui.image_tab import update_image_preview
        
        mock_preview = Mock()
        mock_group = {"image_preview": mock_preview}
        mock_app.image_groups = [mock_group]
        
        update_image_preview(mock_app, 0, "/nonexistent/path.png")
        
        mock_preview.configure.assert_not_called()
