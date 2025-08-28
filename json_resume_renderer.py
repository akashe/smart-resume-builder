import subprocess
import json
import os
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil

class JSONResumeRenderer:
    """Render JSON Resume using various themes via resume-cli"""
    
    AVAILABLE_THEMES = [
        'elegant',
        'kendall'
    ]
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='json_resume_')
        
        # Check if resume CLI is available
        if not self._check_resume_cli():
            raise RuntimeError("resume-cli not found. Install with: npm install -g resume-cli")
    
    def _check_resume_cli(self) -> bool:
        """Check if resume CLI is installed and accessible"""
        try:
            result = subprocess.run(['resume', '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def render_to_pdf(self, 
                      json_resume_data: Dict[str, Any], 
                      theme: str = 'professional',
                      output_filename: str = 'resume.pdf') -> bytes:
        """
        Render JSON Resume to PDF using specified theme
        
        Args:
            json_resume_data: JSON Resume formatted data
            theme: Theme name (professional, elegant, etc.)
            output_filename: Output filename
            
        Returns:
            PDF bytes
        """
        
        if theme not in self.AVAILABLE_THEMES:
            raise ValueError(f"Theme '{theme}' not available. Choose from: {self.AVAILABLE_THEMES}")
        
        # Create temporary JSON file
        json_file_path = os.path.join(self.temp_dir, 'resume.json')
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_resume_data, f, indent=2, ensure_ascii=False)
        
        # Output PDF path
        pdf_output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Install theme if not already installed
            self._install_theme(theme)
            
            # Export to PDF using resume CLI
            cmd = [
                'resume', 'export', pdf_output_path,
                '--format', 'pdf',
                '--resume', json_file_path,
                '--theme', theme
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Resume export failed: {result.stderr}")
            
            # Read PDF bytes
            if os.path.exists(pdf_output_path):
                with open(pdf_output_path, 'rb') as f:
                    return f.read()
            else:
                raise RuntimeError("PDF file was not generated")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Resume export timed out")
        except Exception as e:
            raise RuntimeError(f"Error rendering resume: {str(e)}")
    
    def render_to_html(self, 
                       json_resume_data: Dict[str, Any], 
                       theme: str = 'professional',
                       output_filename: str = 'resume.html') -> str:
        """
        Render JSON Resume to HTML using specified theme
        
        Returns:
            HTML content as string
        """
        
        if theme not in self.AVAILABLE_THEMES:
            raise ValueError(f"Theme '{theme}' not available. Choose from: {self.AVAILABLE_THEMES}")
        
        # Create temporary JSON file
        json_file_path = os.path.join(self.temp_dir, 'resume.json')
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_resume_data, f, indent=2, ensure_ascii=False)
        
        # Output HTML path
        html_output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Install theme if not already installed
            self._install_theme(theme)
            
            # Export to HTML using resume CLI
            cmd = [
                'resume', 'export', html_output_path,
                '--format', 'html',
                '--resume', json_file_path,
                '--theme', theme
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Resume export failed: {result.stderr}")
            
            # Read HTML content
            if os.path.exists(html_output_path):
                with open(html_output_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise RuntimeError("HTML file was not generated")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Resume export timed out")
        except Exception as e:
            raise RuntimeError(f"Error rendering resume: {str(e)}")
    
    def _install_theme(self, theme: str) -> None:
        """Install theme locally in temp directory with force flag"""
        try:
            # Install theme locally with force to handle dependency conflicts
            install_cmd = ['npm', 'install', f'jsonresume-theme-{theme}', '--force', '--no-save']
            install_result = subprocess.run(
                install_cmd, 
                capture_output=True, 
                text=True,
                timeout=120,  # Increased timeout
                cwd=self.temp_dir
            )
            
            if install_result.returncode != 0:
                print(f"Warning: Could not install theme {theme} locally")
                # Don't print full error to avoid spam
                    
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"Warning: Theme installation failed: {e}")
    
    def list_available_themes(self) -> List[str]:
        """List all available themes"""
        return self.AVAILABLE_THEMES.copy()
    
    def validate_theme(self, theme: str) -> bool:
        """Check if theme is available"""
        return theme in self.AVAILABLE_THEMES
    
    def preview_theme(self, 
                      json_resume_data: Dict[str, Any], 
                      theme: str) -> str:
        """Generate HTML preview of resume with given theme"""
        return self.render_to_html(json_resume_data, theme, f'preview_{theme}.html')
    
    def cleanup(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def test_render(self) -> bool:
        """Test if rendering works with a sample resume"""
        sample_resume = {
            "basics": {
                "name": "Test User",
                "email": "test@example.com",
                "summary": "This is a test resume to validate JSON Resume rendering."
            },
            "work": [],
            "education": [],
            "skills": [],
            "projects": []
        }
        
        try:
            html_content = self.render_to_html(sample_resume, 'professional')
            return len(html_content) > 100  # Basic check
        except Exception:
            return False