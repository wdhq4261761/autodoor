import platform
import customtkinter as ctk


class Theme:
    SYSTEM = platform.system()
    
    COLORS = {
        'primary': '#3B82F6',
        'primary_hover': '#2563EB',
        'secondary': '#6366F1',
        'success': '#22C55E',
        'success_light': '#DCFCE7',
        'warning': '#F59E0B',
        'warning_light': '#FEF3C7',
        'error': '#EF4444',
        'error_light': '#FEE2E2',
        'info': '#3B82F6',
        'info_hover': '#2563EB',
        'info_light': '#DBEAFE',
        
        'text_primary': '#1F2937',
        'text_secondary': '#6B7280',
        'text_muted': '#9CA3AF',
        
        'bg_primary': '#FFFFFF',
        'bg_secondary': '#F9FAFB',
        'bg_tertiary': '#F3F4F6',
        
        'border': '#E5E7EB',
        'border_light': '#F3F4F6',
        
        'card_bg': '#FFFFFF',
        'sidebar_bg': '#F9FAFB',
        'header_bg': '#FFFFFF',
        'footer_bg': '#F9FAFB',
    }
    
    FONTS = {
        'family': 'Microsoft YaHei' if SYSTEM == 'Windows' else 'PingFang SC',
        'sizes': {
            'xs': 10,
            'sm': 11,
            'base': 12,
            'lg': 14,
            'xl': 16,
            '2xl': 18,
            '3xl': 24,
        }
    }
    
    DIMENSIONS = {
        'sidebar_width': 180,
        'header_height': 44,
        'footer_height': 28,
        'card_corner_radius': 8,
        'button_corner_radius': 6,
        'input_height': 28,
        'button_height': 32,
    }
    
    @classmethod
    def get_font(cls, size_key='base'):
        size = cls.FONTS['sizes'].get(size_key, 12)
        return (cls.FONTS['family'], size)
    
    @classmethod
    def get_dark_colors(cls):
        return {
            'text_primary': '#F9FAFB',
            'text_secondary': '#D1D5DB',
            'text_muted': '#9CA3AF',
            'bg_primary': '#1F2937',
            'bg_secondary': '#111827',
            'bg_tertiary': '#374151',
            'border': '#374151',
            'border_light': '#4B5563',
            'card_bg': '#1F2937',
            'sidebar_bg': '#111827',
            'header_bg': '#1F2937',
            'footer_bg': '#111827',
        }


def init_theme():
    # TODO: 夜间模式暂时禁用，待后续迭代完善后启用
    # 目前强制使用 Light 模式，确保所有组件样式一致
    ctk.set_appearance_mode('Light')
    ctk.set_default_color_theme('blue')
    
    if Theme.SYSTEM == 'Windows':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
