from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import tempfile
import os

from typst_renderer import TypstRenderer
from rendercv_renderer import RenderCVRenderer

class ThemeType(Enum):
    TYPST = "typst"
    RENDERCV = "rendercv"

class ThemeExporter:
    """Unified exporter supporting JSON Resume and Typst themes"""
    
    AVAILABLE_THEMES = {
        # Typst templates (working, high-quality themes)
        ThemeType.TYPST: {
            'modern-cv': 'Modern CV - Professional typography with elegant layout',
            'basic-resume': 'Basic Resume - Clean, ATS-friendly design'
        },
        # RenderCV themes (professional Typst-based templates)
        ThemeType.RENDERCV: {
            'classic': 'Classic - Traditional professional resume format',
            'engineeringresumes': 'Engineering Resumes - Optimized for technical roles', 
            'sb2nov': 'SB2Nov - Modern academic CV style',
            'moderncv': 'Modern CV - Contemporary professional design',
            'engineeringclassic': 'Engineering Classic - Clean technical resume format'
        }
    }
    
    def __init__(self):
        pass
    
    def get_available_themes(self) -> Dict[str, Dict[str, str]]:
        """Get all available themes organized by engine type"""
        return {
            'Typst': self.AVAILABLE_THEMES[ThemeType.TYPST],
            'RenderCV': self.AVAILABLE_THEMES[ThemeType.RENDERCV]
        }
    
    def get_theme_list(self) -> List[Tuple[str, str, str]]:
        """Get flat list of themes as (engine, theme_name, description)"""
        themes = []
        
        for engine_type, theme_dict in self.AVAILABLE_THEMES.items():
            engine_name = engine_type.value.replace('_', ' ').title()
            for theme_name, description in theme_dict.items():
                themes.append((engine_name, theme_name, description))
        
        return themes
    
    def export_resume(self, 
                      resume_data: Dict[str, Any],
                      theme_engine: str,
                      theme_name: str,
                      output_format: str = 'pdf') -> bytes:
        """
        Export resume using specified theme and engine
        
        Args:
            resume_data: Internal resume data structure
            theme_engine: 'json_resume' or 'typst'
            theme_name: Name of the theme
            output_format: 'pdf' or 'html' (html only for JSON Resume)
            
        Returns:
            File bytes (PDF or HTML)
        """
        
        engine_type = ThemeType(theme_engine.lower())
        

        if engine_type == ThemeType.TYPST:
            return self._export_typst(resume_data, theme_name, output_format)
        elif engine_type == ThemeType.RENDERCV:
            return self._export_rendercv(resume_data, theme_name, output_format)
        else:
            raise ValueError(f"Unsupported theme engine: {theme_engine}")
    
    def _export_typst(self, 
                      resume_data: Dict[str, Any],
                      theme_name: str,
                      output_format: str) -> bytes:
        """Export using Typst engine"""
        
        if output_format.lower() != 'pdf':
            raise ValueError("Typst only supports PDF output")
        
        # Render using Typst
        with TypstRenderer() as renderer:
            return renderer.render_resume(resume_data, theme_name)
    
    def _export_rendercv(self, 
                         resume_data: Dict[str, Any],
                         theme_name: str,
                         output_format: str) -> bytes:
        """Export using RenderCV engine"""
        
        if output_format.lower() != 'pdf':
            raise ValueError("RenderCV only supports PDF output")
        
        # Render using RenderCV
        with RenderCVRenderer() as renderer:
            return renderer.render_resume(resume_data, theme_name)
    
    def preview_theme(self, 
                      resume_data: Dict[str, Any],
                      theme_engine: str,
                      theme_name: str) -> str:
        """Generate HTML preview of theme (only works for JSON Resume themes)"""
        
        if theme_engine.lower() != 'json_resume':
            raise ValueError("Preview only available for JSON Resume themes")
        
        return self._export_json_resume(resume_data, theme_name, 'html').decode('utf-8')
    
    def validate_theme(self, theme_engine: str, theme_name: str) -> bool:
        """Validate if theme exists for given engine"""
        try:
            engine_type = ThemeType(theme_engine.lower())
            return theme_name in self.AVAILABLE_THEMES[engine_type]
        except ValueError:
            return False
    
    def get_theme_info(self, theme_engine: str, theme_name: str) -> Optional[str]:
        """Get description of a specific theme"""
        try:
            engine_type = ThemeType(theme_engine.lower())
            return self.AVAILABLE_THEMES[engine_type].get(theme_name)
        except ValueError:
            return None