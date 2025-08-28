from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import tempfile
import os

from json_resume_transformer import JSONResumeTransformer
from json_resume_renderer import JSONResumeRenderer
from exporter import PDFExporter

class ThemeType(Enum):
    JSON_RESUME = "json_resume"
    REPORTLAB = "reportlab"
    TYPST = "typst"  # For future implementation

class ThemeExporter:
    """Unified exporter supporting multiple resume theme engines"""
    
    AVAILABLE_THEMES = {
        # Current ReportLab implementation (working)
        ThemeType.REPORTLAB: {
            'professional': 'Professional - Clean corporate style with elegant typography',
            'modern': 'Modern - Contemporary design (coming soon)',
            'minimal': 'Minimal - Clean and simple layout (coming soon)'
        },
        # JSON Resume themes (experimental - may have dependency issues)
        ThemeType.JSON_RESUME: {
            'professional': 'JSON Resume Professional - External theme (experimental)',
            'elegant': 'JSON Resume Elegant - External theme (experimental)'
        }
    }
    
    def __init__(self):
        self.json_transformer = JSONResumeTransformer()
        self.reportlab_exporter = PDFExporter()
    
    def get_available_themes(self) -> Dict[str, Dict[str, str]]:
        """Get all available themes organized by engine type"""
        return {
            'JSON Resume': self.AVAILABLE_THEMES[ThemeType.JSON_RESUME],
            'ReportLab': self.AVAILABLE_THEMES[ThemeType.REPORTLAB]
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
            theme_engine: 'json_resume' or 'reportlab'
            theme_name: Name of the theme
            output_format: 'pdf' or 'html' (html only for JSON Resume)
            
        Returns:
            File bytes (PDF or HTML)
        """
        
        engine_type = ThemeType(theme_engine.lower())
        
        if engine_type == ThemeType.JSON_RESUME:
            return self._export_json_resume(resume_data, theme_name, output_format)
        elif engine_type == ThemeType.REPORTLAB:
            return self._export_reportlab(resume_data, theme_name, output_format)
        else:
            raise ValueError(f"Unsupported theme engine: {theme_engine}")
    
    def _export_json_resume(self, 
                           resume_data: Dict[str, Any],
                           theme_name: str,
                           output_format: str) -> bytes:
        """Export using JSON Resume engine (experimental)"""
        
        try:
            # Transform data to JSON Resume format
            json_resume_data = self.json_transformer.transform_to_json_resume(resume_data)
            
            # Render using JSON Resume
            with JSONResumeRenderer() as renderer:
                if output_format.lower() == 'pdf':
                    return renderer.render_to_pdf(json_resume_data, theme_name)
                elif output_format.lower() == 'html':
                    html_content = renderer.render_to_html(json_resume_data, theme_name)
                    return html_content.encode('utf-8')
                else:
                    raise ValueError(f"Unsupported output format for JSON Resume: {output_format}")
        
        except Exception as e:
            # Fallback to ReportLab if JSON Resume fails
            print(f"JSON Resume failed ({e}), falling back to ReportLab")
            return self._export_reportlab(resume_data, 'professional', 'pdf')
    
    def _export_reportlab(self, 
                         resume_data: Dict[str, Any],
                         theme_name: str,
                         output_format: str) -> bytes:
        """Export using ReportLab engine"""
        
        if output_format.lower() != 'pdf':
            raise ValueError("ReportLab only supports PDF output")
        
        # Handle different ReportLab theme variations
        if theme_name in ['modern', 'minimal']:
            # For future theme implementations, fall back to professional for now
            theme_name = 'professional'
        
        # Generate markdown from resume data (using existing logic from app.py)
        markdown_content = self._generate_markdown_from_data(resume_data)
        
        # Export using ReportLab
        return self.reportlab_exporter.markdown_to_pdf(markdown_content)
    
    def _generate_markdown_from_data(self, resume_data: Dict[str, Any]) -> str:
        """Generate markdown content from resume data for ReportLab"""
        # This replicates the markdown generation logic
        # You could extract this from matcher.py or create a separate utility
        
        markdown_parts = []
        
        # Contact info
        contact = resume_data.get('contact', {})
        if contact.get('name'):
            markdown_parts.append(f"# {contact['name']}")
        
        # Contact details
        contact_line = []
        if contact.get('email'):
            contact_line.append(contact['email'])
        if contact.get('phone'):
            contact_line.append(contact['phone'])
        if contact.get('linkedin'):
            contact_line.append(contact['linkedin'])
        
        if contact_line:
            markdown_parts.append(' | '.join(contact_line))
        
        # Summary
        summary_data = resume_data.get('summary', {})
        if 'selected_sentences' in summary_data:
            sentences = summary_data['selected_sentences']
        else:
            sentences = summary_data.get('sentences', [])
        
        if sentences:
            markdown_parts.append("\n## Summary")
            markdown_parts.append(' '.join(sentences))
        
        # Experience
        experiences = resume_data.get('experience', [])
        if experiences:
            markdown_parts.append("\n## Experience")
            for exp in experiences:
                position = exp.get('position', '')
                company = exp.get('company', '')
                duration = exp.get('duration', '')
                
                if position and company:
                    markdown_parts.append(f"\n### {position} - {company}")
                    if duration:
                        markdown_parts.append(f"**{duration}**")
                
                # Role summary
                if 'selected_role_summary' in exp:
                    markdown_parts.append(exp['selected_role_summary'])
                elif exp.get('role_summaries'):
                    markdown_parts.append(exp['role_summaries'][0])
                
                # Accomplishments
                if 'selected_accomplishments' in exp:
                    accomplishments = exp['selected_accomplishments']
                elif exp.get('accomplishments'):
                    accomplishments = exp['accomplishments']
                else:
                    accomplishments = []
                
                for acc in accomplishments:
                    markdown_parts.append(f"• {acc}")
        
        # Projects
        projects = resume_data.get('projects', [])
        if projects:
            markdown_parts.append("\n## Projects")
            for proj in projects:
                name = proj.get('name', '')
                if name:
                    markdown_parts.append(f"\n### {name}")
                
                # Description
                if 'selected_description' in proj:
                    markdown_parts.append(proj['selected_description'])
                elif proj.get('descriptions'):
                    markdown_parts.append(proj['descriptions'][0])
                
                # Technologies
                if proj.get('technologies'):
                    tech_str = ', '.join(proj['technologies'])
                    markdown_parts.append(f"**Technologies:** {tech_str}")
        
        # Skills
        skills_data = resume_data.get('skills', {})
        if skills_data:
            markdown_parts.append("\n## Skills")
            for category, skill_list in skills_data.items():
                if skill_list:
                    category_name = category.replace('_', ' ').title()
                    skills_str = ', '.join(skill_list)
                    markdown_parts.append(f"**{category_name}:** {skills_str}")
        
        # Education
        education = resume_data.get('education', [])
        if education:
            markdown_parts.append("\n## Education")
            for edu in education:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                graduation = edu.get('graduation', '')
                
                if degree and institution:
                    markdown_parts.append(f"\n### {degree} - {institution}")
                    if graduation:
                        markdown_parts.append(f"**{graduation}**")
        
        return '\n\n'.join(markdown_parts)
    
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