import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class JSONResumeTransformer:
    """Transform internal resume data to JSON Resume schema format"""
    
    def __init__(self):
        pass
    
    def transform_to_json_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform internal resume structure to JSON Resume schema
        https://jsonresume.org/schema/
        """
        json_resume = {
            "basics": self._transform_basics(resume_data),
            "work": self._transform_work(resume_data),
            "volunteer": [],
            "education": self._transform_education(resume_data),
            "awards": [],
            "certificates": [],
            "publications": [],
            "skills": self._transform_skills(resume_data),
            "languages": [],
            "interests": [],
            "references": [],
            "projects": self._transform_projects(resume_data)
        }
        
        return json_resume
    
    def _transform_basics(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform contact info to JSON Resume basics section"""
        contact = resume_data.get('contact', {})
        
        basics = {
            "name": contact.get('name', ''),
            "label": "",  # Professional title/label
            "image": "",
            "email": contact.get('email', ''),
            "phone": contact.get('phone', ''),
            "url": "",
            "summary": self._get_summary_text(resume_data),
            "location": {
                "address": "",
                "postalCode": "",
                "city": "",
                "countryCode": "",
                "region": ""
            },
            "profiles": []
        }
        
        # Add LinkedIn profile if available
        if contact.get('linkedin'):
            linkedin_url = contact['linkedin']
            if not linkedin_url.startswith('http'):
                linkedin_url = f"https://linkedin.com/in/{linkedin_url}"
            
            basics["profiles"].append({
                "network": "LinkedIn",
                "username": contact['linkedin'].replace('https://linkedin.com/in/', ''),
                "url": linkedin_url
            })
        
        return basics
    
    def _get_summary_text(self, resume_data: Dict[str, Any]) -> str:
        """Get summary text from selected sentences or original"""
        summary_data = resume_data.get('summary', {})
        
        # If we have selected sentences (from matching), use those
        if 'selected_sentences' in summary_data:
            return ' '.join(summary_data['selected_sentences'])
        
        # Otherwise use all available sentences
        sentences = summary_data.get('sentences', [])
        return ' '.join(sentences)
    
    def _transform_work(self, resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform work experience to JSON Resume work section"""
        work_experiences = []
        
        experiences = resume_data.get('experience', [])
        for exp in experiences:
            work_exp = {
                "name": exp.get('company', ''),
                "position": exp.get('position', ''),
                "url": "",
                "startDate": self._parse_start_date(exp.get('duration', '')),
                "endDate": self._parse_end_date(exp.get('duration', '')),
                "summary": self._get_work_summary(exp),
                "highlights": self._get_work_highlights(exp)
            }
            work_experiences.append(work_exp)
        
        return work_experiences
    
    def _get_work_summary(self, exp: Dict[str, Any]) -> str:
        """Get work summary from selected role summary or first available"""
        if 'selected_role_summary' in exp:
            return exp['selected_role_summary']
        
        role_summaries = exp.get('role_summaries', [])
        return role_summaries[0] if role_summaries else ""
    
    def _get_work_highlights(self, exp: Dict[str, Any]) -> List[str]:
        """Get work highlights from selected accomplishments or all available"""
        if 'selected_accomplishments' in exp:
            return exp['selected_accomplishments']
        
        return exp.get('accomplishments', [])
    
    def _transform_education(self, resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform education to JSON Resume education section"""
        education_list = []
        
        education = resume_data.get('education', [])
        for edu in education:
            edu_entry = {
                "institution": edu.get('institution', ''),
                "url": "",
                "area": edu.get('degree', ''),
                "studyType": "",
                "startDate": "",
                "endDate": edu.get('graduation', ''),
                "score": "",
                "courses": []
            }
            education_list.append(edu_entry)
        
        return education_list
    
    def _transform_skills(self, resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform skills to JSON Resume skills section"""
        skills_list = []
        
        skills_data = resume_data.get('skills', {})
        
        # Group skills by category
        skill_categories = {
            'Programming Languages': skills_data.get('programming', []),
            'Technical Skills': skills_data.get('technical', []),
            'Tools & Technologies': skills_data.get('tools', []),
            'Soft Skills': skills_data.get('soft_skills', [])
        }
        
        for category, skill_list in skill_categories.items():
            if skill_list:
                skills_entry = {
                    "name": category,
                    "level": "",
                    "keywords": skill_list
                }
                skills_list.append(skills_entry)
        
        return skills_list
    
    def _transform_projects(self, resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform projects (non-standard JSON Resume extension)"""
        projects_list = []
        
        projects = resume_data.get('projects', [])
        for proj in projects:
            project_entry = {
                "name": proj.get('name', ''),
                "description": self._get_project_description(proj),
                "highlights": proj.get('achievements', []),
                "keywords": proj.get('technologies', []),
                "startDate": "",
                "endDate": "",
                "url": proj.get('url', ''),
                "roles": [],
                "entity": "",
                "type": "project"
            }
            projects_list.append(project_entry)
        
        return projects_list
    
    def _get_project_description(self, proj: Dict[str, Any]) -> str:
        """Get project description from selected or first available"""
        if 'selected_description' in proj:
            return proj['selected_description']
        
        descriptions = proj.get('descriptions', [])
        return descriptions[0] if descriptions else ""
    
    def _parse_start_date(self, duration_str: str) -> str:
        """Parse start date from duration string like 'Jan 2020 - Present'"""
        if not duration_str:
            return ""
        
        # Simple parsing - can be enhanced
        parts = duration_str.split(' - ')
        if len(parts) >= 1:
            start_part = parts[0].strip()
            return self._normalize_date(start_part)
        
        return ""
    
    def _parse_end_date(self, duration_str: str) -> str:
        """Parse end date from duration string"""
        if not duration_str:
            return ""
        
        parts = duration_str.split(' - ')
        if len(parts) >= 2:
            end_part = parts[1].strip()
            if end_part.lower() in ['present', 'current', 'now']:
                return ""  # Empty string indicates current position
            return self._normalize_date(end_part)
        
        return ""
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert various date formats to ISO format (YYYY-MM-DD)"""
        if not date_str:
            return ""
        
        # This is a simple implementation - can be enhanced with proper date parsing
        # For now, just return the original string
        return date_str
    
    def save_json_resume(self, resume_data: Dict[str, Any], output_path: str) -> str:
        """Transform and save resume data as JSON Resume format"""
        json_resume = self.transform_to_json_resume(resume_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_resume, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def validate_json_resume(self, json_resume: Dict[str, Any]) -> bool:
        """Basic validation of JSON Resume structure"""
        required_sections = ['basics', 'work', 'education', 'skills']
        
        for section in required_sections:
            if section not in json_resume:
                return False
        
        # Validate basics section has required fields
        basics = json_resume.get('basics', {})
        if not basics.get('name'):
            return False
        
        return True