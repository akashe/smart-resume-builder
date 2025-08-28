from typing import Dict, Any, List
import tempfile
import os
from datetime import datetime
import yaml
import re

class RenderCVTransformer:
    """Transform internal resume data to RenderCV YAML format"""
    
    def __init__(self):
        pass
    
    def transform_to_rendercv(self, resume_data: Dict[str, Any], theme: str = 'classic') -> Dict[str, Any]:
        """
        Transform internal resume structure to RenderCV YAML format
        """
        # Extract contact info
        contact = resume_data.get('contact', {})
        
        # Build CV structure
        cv_data = {
            'name': contact.get('name', 'Your Name'),
            'title': contact.get('title', ''),
            'location': contact.get('city', '') or contact.get('location', '') or 'Location',
            'email': contact.get('email', 'email@example.com'),
            'phone': self._format_phone(contact.get('phone', '')),
            'website': contact.get('website', 'www.akashe.io'),
            'social_networks': self._build_social_networks(contact),
            'sections': self._build_sections(resume_data)
        }

        rendercv_data = {
            'cv': cv_data,
            'design': self._get_design_config(theme),
            'locale': {
                'language': 'en',
                'phone_number_format': 'national'
            },
            'rendercv_settings': {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'render_command': {},
                'bold_keywords': []
            }
        }
        
        return rendercv_data
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number for RenderCV validation"""
        # Always return the working phone number format that RenderCV accepts
        # RenderCV seems very strict about phone validation
        return phone
    
    def _build_social_networks(self, contact: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build social networks section"""
        networks = []
        
        if contact.get('linkedin'):
            linkedin = contact['linkedin']
            # Extract username from LinkedIn URL
            if 'linkedin.com/in/' in linkedin:
                username = linkedin.split('linkedin.com/in/')[-1].strip('/')
            else:
                username = linkedin
            
            networks.append({
                'network': 'LinkedIn',
                'username': username
            })
        
        if contact.get('github'):
            github = contact['github']
            # Extract username from GitHub URL
            if 'github.com/' in github:
                username = github.split('github.com/')[-1].strip('/')
            else:
                username = github
                
            networks.append({
                'network': 'GitHub',
                'username': username
            })
        
        return networks
    
    def _build_sections(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build all resume sections"""
        sections = {}
        
        # Summary/Welcome section
        summary_data = resume_data.get('summary', {})
        if 'selected_sentences' in summary_data:
            summary_text = summary_data['selected_sentences']
        else:
            summary_text = summary_data.get('sentences', [])
        
        if summary_text:
            sections['summary'] = summary_text
        
        # Experience section
        experiences = resume_data.get('experience', [])
        if experiences:
            sections['experience'] = self._build_experience_entries(experiences)
        
        # Education section
        education = resume_data.get('education', [])
        if education:
            sections['education'] = self._build_education_entries(education)
        
        # Projects section
        projects = resume_data.get('projects', [])
        if projects:
            sections['projects'] = self._build_project_entries(projects)
        
        # Skills section
        skills_data = resume_data.get('skills', {})
        if skills_data:
            sections['skills'] = self._build_skills_entries(skills_data)
        
        return sections
    
    def _build_experience_entries(self, experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build experience entries"""
        entries = []
        
        for exp in experiences:
            # Get selected or first available data
            highlights = []
            if 'selected_accomplishments' in exp:
                highlights = exp['selected_accomplishments']
            elif exp.get('accomplishments'):
                highlights = exp['accomplishments']
            
            # Parse dates
            start_date, end_date = self._parse_duration(exp.get('duration', ''))
            
            entry = {
                'company': exp.get('company', ''),
                'position': exp.get('position', ''),
                'location': exp.get('location', ''),
                'start_date': start_date,
                'end_date': end_date,
                'highlights': highlights
            }
            
            # Add role summary if available
            if 'selected_role_summary' in exp:
                entry['summary'] = exp['selected_role_summary']
            elif exp.get('role_summaries'):
                entry['summary'] = exp['role_summaries'][0]
            
            entries.append(entry)
        
        return entries
    
    def _build_education_entries(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build education entries according to RenderCV EducationEntry model"""
        entries = []
        
        for edu in education:
            # Parse graduation date to extract start/end dates
            graduation = edu.get('graduation', '')
            start_date, end_date = self._parse_education_dates(graduation)
            
            # RenderCV EducationEntry requires institution and area fields
            institution = edu.get('institution', '')
            area = edu.get('field', '') or edu.get('area', '') or edu.get('degree', '')
            
            # Skip entry if we don't have required fields
            if not institution or not area:
                continue
                
            entry = {
                'institution': institution,
                'area': area
            }
            
            # Add optional fields only if they have valid values
            degree = edu.get('degree', '')
            if degree:
                entry['degree'] = degree
                
            location = edu.get('location', '')
            if location:
                entry['location'] = location
                
            if start_date:
                entry['start_date'] = start_date
                
            if end_date:
                entry['end_date'] = end_date
            
            # Build highlights array
            highlights = edu.get('highlights', [])
            if edu.get('gpa'):
                highlights.append(f"GPA: {edu['gpa']}")
                
            if highlights:
                entry['highlights'] = highlights
                
            entries.append(entry)
        
        return entries
    
    def _build_project_entries(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build project entries according to RenderCV NormalEntry model"""
        entries = []
        
        for proj in projects:
            # Get selected or first description
            summary = ""
            if 'selected_description' in proj:
                summary = proj['selected_description']
            elif proj.get('descriptions'):
                summary = proj['descriptions'][0]
            
            # Build highlights from technologies and achievements
            highlights = []
            if proj.get('technologies'):
                tech_str = ', '.join(proj['technologies'])
                highlights.append(f"Technologies: {tech_str}")
            
            if proj.get('achievements'):
                highlights.extend(proj['achievements'])
            
            # RenderCV NormalEntry requires name field
            project_name = proj.get('name', '')
            if not project_name:
                continue  # Skip projects without names
            
            entry = {
                'name': project_name,
                'highlights': highlights
            }
            
            # Add optional fields only if they have valid values
            if summary:
                entry['summary'] = summary
            
            # Add location if available
            if proj.get('location'):
                entry['location'] = proj['location']
            
            # Handle URL - RenderCV expects markdown links in the name field
            if proj.get('url'):
                entry['name'] = f"[{project_name}]({proj['url']})"
            
            entries.append(entry)
        
        return entries
    
    def _build_skills_entries(self, skills_data: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """Build skills entries"""
        entries = []
        
        for category, skill_list in skills_data.items():
            if skill_list:
                label = category.replace('_', ' ').title()
                details = ', '.join(skill_list)
                
                entries.append({
                    'label': label,
                    'details': details
                })
        
        return entries
    
    def _parse_education_dates(self, graduation_str: str) -> tuple:
        """Parse education graduation string to start_date and end_date"""
        if not graduation_str:
            return '', ''
        
        graduation_str = graduation_str.strip()
        
        # If it's just a year like "2020", assume it's graduation year
        if graduation_str.isdigit() and len(graduation_str) == 4:
            year = graduation_str
            # Assume 4 year program ending in graduation year
            try:
                start_year = str(int(year) - 4)
                return f"{start_year}-09", f"{year}-05"  # Sept to May typical academic year
            except:
                return f"{year}-01", f"{year}-12"
        
        # If it contains a range like "2016 - 2020" 
        if ' - ' in graduation_str:
            parts = graduation_str.split(' - ')
            if len(parts) >= 2:
                start_year = parts[0].strip()
                end_year = parts[1].strip()
                
                # Ensure we have valid years
                if start_year.isdigit() and len(start_year) == 4:
                    start_date = f"{start_year}-09"  # Assume Sept start
                else:
                    start_date = self._normalize_date(start_year)
                
                if end_year.isdigit() and len(end_year) == 4:
                    end_date = f"{end_year}-05"  # Assume May graduation
                elif end_year.lower() in ['present', 'current', 'now']:
                    end_date = 'present'
                else:
                    end_date = self._normalize_date(end_year)
                
                return start_date, end_date
        
        # Try to parse as a single date
        normalized = self._normalize_date(graduation_str)
        if normalized and normalized != graduation_str:
            return normalized, normalized
        
        # If we can't parse it properly, return empty
        return '', ''

    def _parse_duration(self, duration_str: str) -> tuple:
        """Parse duration string to start_date and end_date"""
        if not duration_str:
            return '', ''
        
        parts = duration_str.split(' - ')
        if len(parts) >= 2:
            start_date = self._normalize_date(parts[0].strip())
            end_date_str = parts[1].strip()
            
            if end_date_str.lower() in ['present', 'current', 'now']:
                end_date = 'present'
            else:
                end_date = self._normalize_date(end_date_str)
            
            return start_date, end_date
        else:
            # Single date
            return self._normalize_date(duration_str), ''
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert date to RenderCV format (YYYY-MM-DD, YYYY-MM, or YYYY)"""
        if not date_str:
            return ''
        
        date_str = date_str.strip()
        
        # If it's already in a valid RenderCV format, return it
        if re.match(r'^\d{4}$', date_str):  # YYYY format
            return date_str
        elif re.match(r'^\d{4}-\d{2}$', date_str):  # YYYY-MM format  
            return date_str
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):  # YYYY-MM-DD format
            return date_str
        
        # Handle formats like "Jan 2020", "January 2020"
        month_mapping = {
            'jan': '01', 'january': '01',
            'feb': '02', 'february': '02',
            'mar': '03', 'march': '03',
            'apr': '04', 'april': '04',
            'may': '05',
            'jun': '06', 'june': '06',
            'jul': '07', 'july': '07',
            'aug': '08', 'august': '08',
            'sep': '09', 'sept': '09', 'september': '09',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12'
        }
        
        parts = date_str.lower().split()
        if len(parts) >= 2:
            month_name = parts[0]
            year = parts[1]
            
            # Validate year format
            if year.isdigit() and len(year) == 4:
                if month_name in month_mapping:
                    return f"{year}-{month_mapping[month_name]}"
        
        # If it's just a year (like "2020")
        if date_str.isdigit() and len(date_str) == 4:
            return date_str
            
        # Try to extract year from formats like "2020-21", "20-21", etc
        if '-' in date_str:
            year_part = date_str.split('-')[0]
            if year_part.isdigit():
                if len(year_part) == 4:
                    return year_part
                elif len(year_part) == 2:
                    # Assume 20xx format
                    return f"20{year_part}"
        
        # If we can't parse it properly, return empty string to avoid validation errors
        print(f"Warning: Could not parse date '{date_str}', returning empty string")
        return ''
    
    def _get_design_config(self, theme: str) -> Dict[str, Any]:
        """Get design configuration for specified theme"""
        
        base_config = {
            'theme': theme,
            'page': {
                'size': 'us-letter',
                'top_margin': '2cm',
                'bottom_margin': '2cm',
                'left_margin': '2cm',
                'right_margin': '2cm'
            },
            'colors': {
                'text': 'black',
                'name': '#004f90'
            }
        }
        
        return base_config
    
    def save_yaml(self, resume_data: Dict[str, Any], output_path: str, theme: str = 'classic') -> str:
        """Transform and save resume data as RenderCV YAML"""
        rendercv_data = self.transform_to_rendercv(resume_data, theme)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(rendercv_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return output_path