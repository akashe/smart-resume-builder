import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import shutil
import pdb

from rendercv_transformer import RenderCVTransformer

class RenderCVRenderer:
    """Render resumes using RenderCV"""
    
    AVAILABLE_THEMES = [
        'classic',
        'engineeringresumes', 
        'sb2nov',
        'moderncv',
        'engineeringclassic'
    ]
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='rendercv_resume_')
        self.transformer = RenderCVTransformer()
        
        # Check if RenderCV is available
        if not self._check_rendercv():
            raise RuntimeError("RenderCV not found. Install with: pip install 'rendercv[full]'")
    
    def _check_rendercv(self) -> bool:
        """Check if RenderCV is installed and accessible"""
        try:
            import rendercv
            return True
        except ImportError:
            return False
    
    def render_resume(self, 
                      resume_data: Dict[str, Any], 
                      theme: str = 'classic') -> bytes:
        """
        Render resume using RenderCV
        
        Args:
            resume_data: Resume data in internal format
            theme: RenderCV theme name
            
        Returns:
            PDF bytes
        """
        
        if theme not in self.AVAILABLE_THEMES:
            theme = 'classic'  # Fallback to classic
        
        try:
            # Transform data to RenderCV format
            rendercv_data = self.transformer.transform_to_rendercv(resume_data, theme)
            
            # Save YAML file
            # pdb.set_trace()
            yaml_file_path = os.path.join("test_folder", 'resume.yaml')
            with open(yaml_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(rendercv_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Render using RenderCV command line (which works)
            pdf_bytes = self._render_with_subprocess(yaml_file_path)
            
            return pdf_bytes
            
        except Exception as e:
            raise RuntimeError(f"RenderCV compilation failed: {str(e)}")
    
    def _render_with_api(self, yaml_file_path: str) -> bytes:
        """Render using RenderCV Python API"""
        try:
            import rendercv.cli as rendercv_cli
            import rendercv.renderer as rendercv_renderer
            from rendercv.data import read_input_file
            
            # Read the YAML file
            data_model = read_input_file(yaml_file_path)
            
            # Render to PDF
            output_dir = Path(self.temp_dir)
            
            # Use the renderer directly
            rendercv_renderer.render_rendercv_model(
                data_model=data_model,
                output_directory_name=str(output_dir),
                latex_command="typst",
                html_command=None
            )
            
            # Find the generated PDF
            pdf_files = list(output_dir.glob("*.pdf"))
            if pdf_files:
                with open(pdf_files[0], 'rb') as f:
                    return f.read()
            else:
                raise RuntimeError("No PDF file was generated")
                
        except ImportError as e:
            raise RuntimeError(f"RenderCV API not available: {e}")
        except Exception as e:
            # Try alternative approach using subprocess as fallback
            return self._render_with_subprocess(yaml_file_path)
    
    def _render_with_subprocess(self, yaml_file_path: str) -> bytes:
        """Render using the working rendercv render command"""
        import subprocess
        
        try:
            # Use the working rendercv render command directly
            # Note: RenderCV creates output in the directory where the YAML file is located
            result = subprocess.run(
                ['rendercv', 'render', os.path.basename(yaml_file_path)],
                capture_output=True,
                text=True,
                timeout=90,  # Increased timeout for theme downloads
                cwd=os.path.dirname(yaml_file_path)
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"RenderCV render failed: {result.stderr}")
            
            # Look for PDF files in the directory containing the YAML file
            search_dir = os.path.dirname(yaml_file_path)
            pdf_files = [f for f in os.listdir(search_dir) if f.endswith('.pdf')]
            
            # Also check subdirectories that RenderCV might create
            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)
                if os.path.isdir(item_path):
                    subdir_pdfs = [f for f in os.listdir(item_path) if f.endswith('.pdf')]
                    pdf_files.extend([os.path.join(item, f) for f in subdir_pdfs])
            
            if pdf_files:
                # Use the first PDF found
                pdf_path = os.path.join(search_dir, pdf_files[0])
                with open(pdf_path, 'rb') as f:
                    return f.read()
            else:
                # Debug: list all files created
                all_files = []
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        all_files.append(os.path.relpath(os.path.join(root, file), search_dir))
                raise RuntimeError(f"No PDF file was generated by RenderCV. Files created: {all_files}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("RenderCV render timed out")
        except FileNotFoundError:
            raise RuntimeError("rendercv command not found. Make sure RenderCV is installed.")
    
    def _render_direct_import(self, yaml_file_path: str) -> bytes:
        """Direct import approach"""
        try:
            # Import RenderCV components
            from rendercv.data import read_input_file
            from rendercv.renderer import create_theme, create_rendercv_model_and_html_from_directory
            
            # Read and validate data
            data_model = read_input_file(yaml_file_path)
            
            # Create output directory
            output_dir = Path(self.temp_dir) / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Generate PDF using Typst
            theme = create_theme(data_model.design)
            
            # Generate the CV
            from rendercv.renderer import typst
            
            # Create Typst content
            typst_content = theme.render_cv(data_model.cv)
            
            # Write Typst file
            typst_file = output_dir / "resume.typ"
            with open(typst_file, 'w', encoding='utf-8') as f:
                f.write(typst_content)
            
            # Compile with Typst
            import typst as typst_lib
            pdf_bytes = typst_lib.compile(typst_content)
            
            return pdf_bytes
            
        except Exception as e:
            raise RuntimeError(f"Direct import rendering failed: {e}")
    
    def list_available_themes(self) -> list:
        """List all available themes"""
        return self.AVAILABLE_THEMES.copy()
    
    def validate_theme(self, theme: str) -> bool:
        """Check if theme is available"""
        return theme in self.AVAILABLE_THEMES
    
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
            "contact": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+1-555-123-4567"
            },
            "summary": {
                "sentences": ["This is a test resume to validate RenderCV rendering."]
            },
            "experience": [{
                "company": "Test Company",
                "position": "Test Position",
                "duration": "Jan 2020 - Present",
                "accomplishments": ["Test accomplishment"]
            }],
            "skills": {"technical": ["Python"]},
            "projects": [],
            "education": []
        }
        
        try:
            pdf_bytes = self.render_resume(sample_resume, 'classic')
            return len(pdf_bytes) > 1000  # Basic check
        except Exception:
            return False