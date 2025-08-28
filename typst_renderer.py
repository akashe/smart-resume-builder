import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

class TypstRenderer:
    """Render resumes using Typst templates"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='typst_resume_')
        
        # Check if Typst is available
        if not self._check_typst_cli():
            raise RuntimeError("Typst CLI not found. Install with: brew install typst")
    
    def _check_typst_cli(self) -> bool:
        """Check if Typst CLI is installed and accessible"""
        try:
            result = subprocess.run(['typst', '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def render_resume(self, 
                      resume_data: Dict[str, Any], 
                      template: str = 'modern-cv') -> bytes:
        """
        Render resume using Typst template
        
        Args:
            resume_data: Resume data in internal format
            template: Template name (currently only 'modern-cv' supported)
            
        Returns:
            PDF bytes
        """
        
        # Generate Typst content based on template
        if template == 'modern-cv':
            typst_content = self._generate_modern_cv_content(resume_data)
        elif template == 'basic-resume':
            typst_content = self._generate_basic_resume_content(resume_data)
        # elif template == 'brilliant-cv':
        #     typst_content = self._generate_brilliant_cv_content(resume_data)
        else:
            # Default to modern-cv if unsupported template
            typst_content = self._generate_modern_cv_content(resume_data)
        
        # Write Typst file
        typst_file_path = os.path.join(self.temp_dir, 'resume.typ')
        with open(typst_file_path, 'w', encoding='utf-8') as f:
            f.write(typst_content)
        
        # Compile to PDF
        pdf_output_path = os.path.join(self.temp_dir, 'resume.pdf')
        
        try:
            result = subprocess.run(
                ['typst', 'compile', typst_file_path, pdf_output_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Typst compilation failed: {result.stderr}")
            
            # Read PDF bytes
            if os.path.exists(pdf_output_path):
                with open(pdf_output_path, 'rb') as f:
                    return f.read()
            else:
                raise RuntimeError("PDF file was not generated")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Typst compilation timed out")
    
    def _generate_modern_cv_content(self, resume_data: Dict[str, Any]) -> str:
        """Generate Typst content for modern-cv template"""
        
        # Extract data
        contact = resume_data.get('contact', {})
        summary_data = resume_data.get('summary', {})
        experiences = resume_data.get('experience', [])
        projects = resume_data.get('projects', [])
        skills_data = resume_data.get('skills', {})
        education = resume_data.get('education', [])
        
        # Get summary text
        if 'selected_sentences' in summary_data:
            summary = ' '.join(summary_data['selected_sentences'])
        else:
            summary = ' '.join(summary_data.get('sentences', []))
        
        typst_content = f'''#import "@preview/modern-cv:0.8.0": *

#show: resume.with(
  author: (
    firstname: "{self._escape_typst(contact.get('name', '').split()[0] if contact.get('name') else 'John')}",
    lastname: "{self._escape_typst(' '.join(contact.get('name', '').split()[1:]) if contact.get('name') and len(contact.get('name', '').split()) > 1 else 'Doe')}",
    email: "{contact.get('email', '')}",
    phone: "{contact.get('phone', '')}",
    github: "",
    linkedin: "{contact.get('linkedin', '')}",
    address: "",
    positions: ()
  ),
  profile-picture: none,
  date: datetime.today().display()
)

'''
        
        # Add summary/objective
        if summary:
            typst_content += f'''= Summary
{self._escape_typst(summary)}

'''
        
        # Add experience
        if experiences:
            typst_content += "= Experience\n\n"
            for exp in experiences:
                company = self._escape_typst(exp.get('company', ''))
                position = self._escape_typst(exp.get('position', ''))
                duration = self._escape_typst(exp.get('duration', ''))
                
                typst_content += f'''#resume-entry(
  title: "{company}",
  location: "{position}",
  date: "{duration}"
)
'''
                
                # Role summary
                if 'selected_role_summary' in exp:
                    role_summary = self._escape_typst(exp['selected_role_summary'])
                elif exp.get('role_summaries'):
                    role_summary = self._escape_typst(exp['role_summaries'][0])
                else:
                    role_summary = ""
                
                if role_summary:
                    typst_content += f"{role_summary}\n\n"
                
                # Accomplishments
                if 'selected_accomplishments' in exp:
                    accomplishments = exp['selected_accomplishments']
                elif exp.get('accomplishments'):
                    accomplishments = exp['accomplishments']
                else:
                    accomplishments = []
                
                for acc in accomplishments:
                    typst_content += f"- {self._escape_typst(acc)}\n"
                
                typst_content += "\n"
        
        # Add projects
        if projects:
            typst_content += "= Projects\n\n"
            for proj in projects:
                name = self._escape_typst(proj.get('name', ''))
                
                # Description
                if 'selected_description' in proj:
                    description = self._escape_typst(proj['selected_description'])
                elif proj.get('descriptions'):
                    description = self._escape_typst(proj['descriptions'][0])
                else:
                    description = ""
                
                typst_content += f'''#resume-entry(
  title: "{name}",
  location: "",
  date: ""
)
{description}

'''
                
                # Technologies
                if proj.get('technologies'):
                    tech_str = ', '.join(proj['technologies'])
                    typst_content += f"*Technologies:* {self._escape_typst(tech_str)}\n\n"
        
        # Add skills
        if skills_data:
            typst_content += "= Skills\n\n"
            for category, skill_list in skills_data.items():
                if skill_list:
                    category_name = category.replace('_', ' ').title()
                    skills_str = ', '.join(skill_list)
                    typst_content += f"*{self._escape_typst(category_name)}:* {self._escape_typst(skills_str)}\n\n"
        
        # Add education
        if education:
            typst_content += "= Education\n\n"
            for edu in education:
                institution = self._escape_typst(edu.get('institution', ''))
                degree = self._escape_typst(edu.get('degree', ''))
                graduation = self._escape_typst(edu.get('graduation', ''))
                
                typst_content += f'''#resume-entry(
  title: "{institution}",
  location: "{degree}",
  date: "{graduation}"
)

'''
        
        return typst_content
    
    def _generate_basic_resume_content(self, resume_data: Dict[str, Any]) -> str:
        """Generate Typst content for basic-resume template (ATS-friendly)"""
        
        # Extract data
        contact = resume_data.get('contact', {})
        summary_data = resume_data.get('summary', {})
        experiences = resume_data.get('experience', [])
        projects = resume_data.get('projects', [])
        skills_data = resume_data.get('skills', {})
        education = resume_data.get('education', [])
        
        # Get summary text
        if 'selected_sentences' in summary_data:
            summary = ' '.join(summary_data['selected_sentences'])
        else:
            summary = ' '.join(summary_data.get('sentences', []))
        
        # Basic resume uses a simple, clean format
        typst_content = f'''#import "@preview/basic-resume:0.1.3": *

#show: resume.with(
  author: "{self._escape_typst(contact.get('name', 'Your Name'))}",
  location: "{self._escape_typst(contact.get('city', '') or contact.get('location', ''))}",
  email: "{contact.get('email', '')}",
  phone: "{contact.get('phone', '')}",
  github: "",
  linkedin: "{contact.get('linkedin', '')}",
  personal-site: ""
)

'''
        
        # Add summary
        if summary:
            typst_content += f'''= Summary
{self._escape_typst(summary)}

'''
        
        # Add experience
        if experiences:
            typst_content += "= Experience\n\n"
            for exp in experiences:
                company = self._escape_typst(exp.get('company', ''))
                position = self._escape_typst(exp.get('position', ''))
                duration = self._escape_typst(exp.get('duration', ''))
                
                typst_content += f'''*{position}* | *{company}* #h(1fr) {duration}
'''
                
                # Accomplishments as simple bullets
                if 'selected_accomplishments' in exp:
                    accomplishments = exp['selected_accomplishments']
                elif exp.get('accomplishments'):
                    accomplishments = exp['accomplishments']
                else:
                    accomplishments = []
                
                for acc in accomplishments:
                    typst_content += f"- {self._escape_typst(acc)}\n"
                
                typst_content += "\n"
        
        # Add projects
        if projects:
            typst_content += "= Projects\n\n"
            for proj in projects:
                name = self._escape_typst(proj.get('name', ''))
                
                # Description
                if 'selected_description' in proj:
                    description = self._escape_typst(proj['selected_description'])
                elif proj.get('descriptions'):
                    description = self._escape_typst(proj['descriptions'][0])
                else:
                    description = ""
                
                typst_content += f'''*{name}*
{description}
'''
                
                # Technologies
                if proj.get('technologies'):
                    tech_str = ', '.join(proj['technologies'])
                    typst_content += f"Technologies: {self._escape_typst(tech_str)}\n"
                
                typst_content += "\n"
        
        # Add skills
        if skills_data:
            typst_content += "= Skills\n\n"
            for category, skill_list in skills_data.items():
                if skill_list:
                    category_name = category.replace('_', ' ').title()
                    skills_str = ', '.join(skill_list)
                    typst_content += f"*{self._escape_typst(category_name)}:* {self._escape_typst(skills_str)}\n\n"
        
        # Add education
        if education:
            typst_content += "= Education\n\n"
            for edu in education:
                institution = self._escape_typst(edu.get('institution', ''))
                degree = self._escape_typst(edu.get('degree', ''))
                graduation = self._escape_typst(edu.get('graduation', ''))
                
                typst_content += f'''*{degree}* | *{institution}* #h(1fr) {graduation}

'''
        
        return typst_content
    
    def _generate_brilliant_cv_content(self, resume_data: Dict[str, Any]) -> str:
        """Generate Typst content for brilliant-cv template"""
        
        # Extract data
        contact = resume_data.get('contact', {})
        summary_data = resume_data.get('summary', {})
        experiences = resume_data.get('experience', [])
        projects = resume_data.get('projects', [])
        skills_data = resume_data.get('skills', {})
        education = resume_data.get('education', [])
        
        # Get summary text
        if 'selected_sentences' in summary_data:
            summary = ' '.join(summary_data['selected_sentences'])
        else:
            summary = ' '.join(summary_data.get('sentences', []))
        
        # Use a simpler brilliant-cv approach without YAML
        typst_content = f'''#import "@preview/brilliant-cv:2.0.3": *

#show: brilliantcv.with(
  metadata: (
    firstname: "{self._escape_typst(contact.get('name', '').split()[0] if contact.get('name') else 'John')}",
    lastname: "{self._escape_typst(' '.join(contact.get('name', '').split()[1:]) if contact.get('name') and len(contact.get('name', '').split()) > 1 else 'Doe')}",
    email: "{contact.get('email', '')}",
    phone: "{contact.get('phone', '')}",
    github: "",
    linkedin: "{contact.get('linkedin', '')}",
    address: "{self._escape_typst(contact.get('city', '') or contact.get('location', ''))}",
  ),
  theme: "blue",
  lang: "en"
)

'''
        
        # Add summary
        if summary:
            typst_content += f'''= Summary
{self._escape_typst(summary)}

'''
        
        # Add experience with brilliant-cv styling
        if experiences:
            typst_content += "= Professional Experience\n\n"
            for exp in experiences:
                company = self._escape_typst(exp.get('company', ''))
                position = self._escape_typst(exp.get('position', ''))
                duration = self._escape_typst(exp.get('duration', ''))
                location = self._escape_typst(exp.get('location', ''))
                
                typst_content += f'''#cvEntry(
  title: [{position}],
  society: [{company}],
  date: [{duration}],
  location: [{location}]
)[
'''
                
                # Role summary
                if 'selected_role_summary' in exp:
                    role_summary = self._escape_typst(exp['selected_role_summary'])
                    typst_content += f"  {role_summary}\n\n"
                elif exp.get('role_summaries'):
                    role_summary = self._escape_typst(exp['role_summaries'][0])
                    typst_content += f"  {role_summary}\n\n"
                
                # Accomplishments
                if 'selected_accomplishments' in exp:
                    accomplishments = exp['selected_accomplishments']
                elif exp.get('accomplishments'):
                    accomplishments = exp['accomplishments']
                else:
                    accomplishments = []
                
                for acc in accomplishments:
                    typst_content += f"  - {self._escape_typst(acc)}\n"
                
                typst_content += "]\n\n"
        
        # Add projects
        if projects:
            typst_content += "= Projects\n\n"
            for proj in projects:
                name = self._escape_typst(proj.get('name', ''))
                
                # Description
                if 'selected_description' in proj:
                    description = self._escape_typst(proj['selected_description'])
                elif proj.get('descriptions'):
                    description = self._escape_typst(proj['descriptions'][0])
                else:
                    description = ""
                
                typst_content += f'''#cvEntry(
  title: [{name}],
  society: [],
  date: [],
  location: []
)[
  {description}
'''
                
                # Technologies
                if proj.get('technologies'):
                    tech_str = ', '.join(proj['technologies'])
                    typst_content += f"\n  *Technologies:* {self._escape_typst(tech_str)}\n"
                
                typst_content += "]\n\n"
        
        # Add skills
        if skills_data:
            typst_content += "= Technical Skills\n\n"
            for category, skill_list in skills_data.items():
                if skill_list:
                    category_name = category.replace('_', ' ').title()
                    skills_str = ', '.join(skill_list)
                    typst_content += f"*{self._escape_typst(category_name)}:* {self._escape_typst(skills_str)}\n\n"
        
        # Add education
        if education:
            typst_content += "= Education\n\n"
            for edu in education:
                institution = self._escape_typst(edu.get('institution', ''))
                degree = self._escape_typst(edu.get('degree', ''))
                graduation = self._escape_typst(edu.get('graduation', ''))
                location = self._escape_typst(edu.get('location', ''))
                
                typst_content += f'''#cvEntry(
  title: [{degree}],
  society: [{institution}],
  date: [{graduation}],
  location: [{location}]
)

'''
        
        return typst_content
    
    def _escape_typst(self, text: str) -> str:
        """Escape special characters for Typst"""
        if not text:
            return ""
        
        # Basic escaping for Typst
        text = text.replace('"', '\\"')
        text = text.replace('\\', '\\\\')
        return text
    
    def cleanup(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            import shutil
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
                "email": "test@example.com"
            },
            "summary": {
                "sentences": ["This is a test resume to validate Typst rendering."]
            },
            "experience": [],
            "skills": {"technical": ["Python"]},
            "projects": [],
            "education": []
        }
        
        try:
            pdf_bytes = self.render_resume(sample_resume, 'modern-cv')
            return len(pdf_bytes) > 1000  # Basic check
        except Exception:
            return False