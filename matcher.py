from openai import OpenAI
import os
from typing import Dict, Any, List
import json
import re

class JobMatcher:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    def match_resume_to_job(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Use AI to select the best resume content for a specific job from structured data"""
        
        # Debug: Print the resume data structure
        print("DEBUG: Resume data keys:", list(resume_data.keys()))
        print("DEBUG: Resume data structure:")
        for key, value in resume_data.items():
            print(f"  {key}: {type(value)}")
            if isinstance(value, dict):
                print(f"    Dict keys: {list(value.keys())}")
            elif isinstance(value, list):
                print(f"    List length: {len(value)}")
        
        # Extract keywords from job description
        job_keywords = self._extract_job_keywords(job_description)
        
        selected_content = {}
        
        # Handle contact info (always include)
        selected_content['contact'] = resume_data.get('contact', {})
        
        # Handle summary sentences
        if 'summary' in resume_data:
            selected_content['summary'] = self._select_summary_sentences(
                resume_data['summary'], job_description, job_keywords
            )
        
        # Handle experience objects
        if 'experience' in resume_data:
            selected_content['experience'] = self._select_experience_content(
                resume_data['experience'], job_description, job_keywords
            )
        
        # Handle projects objects  
        if 'projects' in resume_data:
            selected_content['projects'] = self._select_project_content(
                resume_data['projects'], job_description, job_keywords
            )
        
        # Handle skills (select relevant categories)
        if 'skills' in resume_data:
            selected_content['skills'] = self._select_skills_content(
                resume_data['skills'], job_description, job_keywords
            )
        
        # Handle education (usually include all)
        selected_content['education'] = resume_data.get('education', [])
        selected_content['certifications'] = resume_data.get('certifications', [])
        selected_content['achievements'] = resume_data.get('achievements', [])
        
        return selected_content
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract key skills and requirements from job description"""
        
        prompt = f"""
        Extract the most important skills, technologies, and qualifications from this job description.
        Return only a JSON array of keywords (max 20 items).
        
        Job Description:
        {job_description}
        
        Format: ["keyword1", "keyword2", "keyword3", ...]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            keywords_text = response.choices[0].message.content.strip()
            keywords = json.loads(keywords_text)
            return keywords
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback: simple keyword extraction
            return self._simple_keyword_extraction(job_description)
    
    def _simple_keyword_extraction(self, job_description: str) -> List[str]:
        """Fallback keyword extraction without AI"""
        
        # Common technical and professional keywords
        tech_keywords = [
            'python', 'javascript', 'react', 'java', 'sql', 'aws', 'docker', 
            'kubernetes', 'machine learning', 'data analysis', 'git', 'agile',
            'node.js', 'postgresql', 'mongodb', 'api', 'rest', 'microservices'
        ]
        
        # Extract keywords that appear in job description
        job_lower = job_description.lower()
        found_keywords = [kw for kw in tech_keywords if kw in job_lower]
        
        # Add some generic important terms
        important_terms = ['experience', 'development', 'management', 'analysis', 'design']
        found_keywords.extend([term for term in important_terms if term in job_lower])
        
        return found_keywords[:15]  # Limit to 15 keywords
    
    def _select_section_content(self, section_name: str, section_data: Dict[str, Any], 
                               job_description: str, job_keywords: List[str]) -> Dict[str, Any]:
        """Select the best content for a specific section"""
        
        if not section_data.get('bullet_points'):
            return section_data  # Return as-is if no bullet points to select from
        
        bullet_points = section_data['bullet_points']
        
        # If only a few bullet points, include all
        if len(bullet_points) <= 3:
            return {
                'text': section_data.get('text', ''),
                'selected_bullets': bullet_points
            }
        
        # Use AI to select best bullet points
        selected_bullets = self._ai_select_bullets(
            section_name, 
            bullet_points, 
            job_description, 
            job_keywords
        )
        
        return {
            'text': section_data.get('text', ''),
            'selected_bullets': selected_bullets
        }
    
    def _ai_select_bullets(self, section_name: str, bullet_points: List[str], 
                          job_description: str, job_keywords: List[str]) -> List[str]:
        """Use AI to select the most relevant bullet points"""
        
        # Create numbered list of bullets for AI
        bullets_text = ""
        for i, bullet in enumerate(bullet_points, 1):
            bullets_text += f"{i}. {bullet}\n"
        
        prompt = f"""
        You are helping to tailor a resume for a specific job. 
        
        Job Description (key requirements):
        {job_description[:1000]}...
        
        Key Job Keywords: {', '.join(job_keywords)}
        
        Section: {section_name}
        Available bullet points:
        {bullets_text}
        
        Select the BEST 3-5 bullet points that most closely match the job requirements.
        Consider:
        1. Keyword relevance
        2. Skill alignment  
        3. Experience level match
        4. Impact and achievements
        
        Return only the numbers of selected bullets (e.g., "1,3,5,7") - no explanations.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            selection_text = response.choices[0].message.content.strip()
            
            # Parse selected numbers
            selected_numbers = []
            for num_str in re.findall(r'\d+', selection_text):
                num = int(num_str)
                if 1 <= num <= len(bullet_points):
                    selected_numbers.append(num - 1)  # Convert to 0-based index
            
            # Return selected bullets
            selected_bullets = [bullet_points[i] for i in selected_numbers]
            
            # Ensure we have at least 2 bullets
            if len(selected_bullets) < 2 and len(bullet_points) >= 2:
                selected_bullets = bullet_points[:3]  # Fallback to first 3
            
            return selected_bullets
            
        except Exception as e:
            print(f"Error in AI bullet selection: {e}")
            # Fallback: return first few bullets
            return bullet_points[:min(4, len(bullet_points))]
    
    def generate_markdown(self, selected_content: Dict[str, Any]) -> str:
        """Generate markdown resume from structured selected content"""
        
        markdown = ""
        
        # Header with contact info
        if 'contact' in selected_content:
            contact = selected_content['contact']
            if contact.get('name'):
                markdown += f"# {contact['name']}\n\n"
            
            # Add title/designation if available
            if contact.get('title'):
                markdown += f"**{contact['title']}**\n\n"
            
            contact_info = []
            if contact.get('email'):
                contact_info.append(contact['email'])
            if contact.get('phone'):
                contact_info.append(contact['phone'])
            if contact.get('location'):
                contact_info.append(contact['location'])
            if contact.get('linkedin'):
                contact_info.append(contact['linkedin'])
            if contact.get('github'):
                contact_info.append(contact['github'])
            if contact.get('website'):
                contact_info.append(contact['website'])
            
            if contact_info:
                markdown += " | ".join(contact_info) + "\n\n"
        
        # Summary from selected sentences
        if 'summary' in selected_content:
            selected_sentences = selected_content['summary'].get('selected_sentences', [])
            if selected_sentences:
                markdown += "## Summary\n\n"
                markdown += " ".join(selected_sentences) + "\n\n"
        
        # Experience from structured objects
        if 'experience' in selected_content and selected_content['experience']:
            markdown += "## Professional Experience\n\n"
            
            for exp in selected_content['experience']:
                if exp.get('position') and exp.get('company'):
                    markdown += f"### {exp['position']} | {exp['company']}"
                    if exp.get('duration'):
                        markdown += f" | {exp['duration']}"
                    markdown += "\n\n"
                
                # Add role summary if selected
                if exp.get('selected_role_summary'):
                    markdown += f"{exp['selected_role_summary']}\n\n"
                
                # Add selected accomplishments
                if exp.get('selected_accomplishments'):
                    for acc in exp['selected_accomplishments']:
                        markdown += f"• {acc}\n"
                    markdown += "\n\n"
        
        # Skills from categorized structure
        if 'skills' in selected_content:
            skills_data = selected_content['skills']
            all_skills = []
            
            for category, skill_list in skills_data.items():
                if skill_list:
                    all_skills.extend(skill_list)
            
            if all_skills:
                markdown += "## Technical Skills\n\n"
                markdown += ", ".join(all_skills) + "\n\n"
        
        # Projects from structured objects
        if 'projects' in selected_content and selected_content['projects']:
            markdown += "## Projects\n\n"
            
            for proj in selected_content['projects']:
                if proj.get('name'):
                    project_header = f"### {proj['name']}"
                    if proj.get('url'):
                        project_header += f" | {proj['url']}"
                    markdown += project_header + "\n\n"
                
                # Add selected description
                if proj.get('selected_description'):
                    markdown += f"{proj['selected_description']}\n\n"
                
                # Add technologies
                if proj.get('technologies'):
                    markdown += f"**Technologies:** {', '.join(proj['technologies'])}\n\n"
        
        # Education from structured objects
        if 'education' in selected_content and selected_content['education']:
            markdown += "## Education\n\n"
            
            for edu in selected_content['education']:
                if edu.get('degree') and edu.get('institution'):
                    edu_line = f"### {edu['degree']} | {edu['institution']}"
                    if edu.get('graduation'):
                        edu_line += f" | {edu['graduation']}"
                    markdown += edu_line + "\n\n"
                
                # Add education details
                if edu.get('details'):
                    for detail in edu['details']:
                        markdown += f"• {detail}\n"
                    markdown += "\n"
        
        # Certifications
        if 'certifications' in selected_content and selected_content['certifications']:
            markdown += "## Certifications\n\n"
            
            for cert in selected_content['certifications']:
                if cert.get('name'):
                    cert_line = f"• {cert['name']}"
                    if cert.get('issuer'):
                        cert_line += f" - {cert['issuer']}"
                    if cert.get('date'):
                        cert_line += f" ({cert['date']})"
                    markdown += cert_line + "\n"
            markdown += "\n"
        
        # Achievements
        if 'achievements' in selected_content and selected_content['achievements']:
            markdown += "## Achievements\n\n"
            
            for achievement in selected_content['achievements']:
                markdown += f"• {achievement}\n"
            markdown += "\n"
        
        return markdown.strip()
    
    def improve_bullet_point(self, bullet_point: str, job_keywords: List[str]) -> str:
        """Improve a bullet point to better match job requirements"""
        
        prompt = f"""
        Improve this resume bullet point to better match the job requirements while keeping it truthful.
        
        Original: {bullet_point}
        Job Keywords to emphasize: {', '.join(job_keywords)}
        
        Make it:
        1. More impactful with quantified results if possible
        2. Include relevant keywords naturally
        3. Use strong action verbs
        4. Keep under 150 characters
        
        Return only the improved bullet point, no explanations.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            improved_bullet = response.choices[0].message.content.strip()
            return improved_bullet
            
        except Exception as e:
            print(f"Error improving bullet point: {e}")
            return bullet_point  # Return original if improvement fails
    
    def _select_summary_sentences(self, summary_data: Dict, job_description: str, job_keywords: List[str]) -> Dict[str, Any]:
        """Select best summary sentences for the job"""
        
        sentences = summary_data.get('sentences', [])
        if not sentences:
            return {'sentences': []}
        
        if len(sentences) <= 2:
            return {'sentences': sentences}
        
        # Use AI to select best sentences
        prompt = f"""
        Select the 2-3 BEST summary sentences that match this job description.
        
        Job Description: {job_description[:800]}...
        Job Keywords: {', '.join(job_keywords)}
        
        Available sentences:
        {chr(10).join([f"{i+1}. {s}" for i, s in enumerate(sentences)])}
        
        Return only the numbers of selected sentences (e.g., "1,3,4").
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            selection_text = response.choices[0].message.content.strip()
            selected_numbers = [int(num.strip()) - 1 for num in selection_text.split(',') if num.strip().isdigit()]
            selected_sentences = [sentences[i] for i in selected_numbers if 0 <= i < len(sentences)]
            
            if not selected_sentences:
                selected_sentences = sentences[:2]  # Fallback
                
            return {'sentences': selected_sentences}
            
        except Exception as e:
            print(f"Error selecting summary sentences: {e}")
            return {'sentences': sentences[:2]}
    
    def _select_experience_content(self, experience_list: List[Dict], job_description: str, job_keywords: List[str]) -> List[Dict]:
        """Select best content for each experience"""
        
        selected_experiences = []
        
        for exp in experience_list:
            selected_exp = {
                'position': exp.get('position', ''),
                'company': exp.get('company', ''),
                'duration': exp.get('duration', ''),
                'location': exp.get('location', ''),
                'role_summaries': [],
                'accomplishments': []
            }
            
            # Select best role summary
            role_summaries = exp.get('role_summaries', [])
            if role_summaries:
                if len(role_summaries) == 1:
                    selected_exp['role_summaries'] = [role_summaries[0]]
                else:
                    best_role_summary = self._ai_select_best_option(
                        role_summaries, job_description, job_keywords, "role summary"
                    )
                    selected_exp['role_summaries'] = [best_role_summary] if best_role_summary else []
            
            # Select best accomplishments (up to 6)
            accomplishments = exp.get('accomplishments', [])
            if accomplishments:
                if len(accomplishments) <= 2:
                    selected_exp['accomplishments'] = accomplishments
                else:
                    selected_exp['accomplishments'] = self._ai_select_multiple_options(
                        accomplishments, job_description, job_keywords, "accomplishments", max_selections=6, min_selections=2
                    )
            
            selected_experiences.append(selected_exp)
        
        return selected_experiences
    
    def _select_project_content(self, projects_list: List[Dict], job_description: str, job_keywords: List[str]) -> List[Dict]:
        """Select best project content and descriptions"""
        
        selected_projects = []
        
        for proj in projects_list:
            selected_proj = {
                'name': proj.get('name', ''),
                'url': proj.get('url', ''),
                'descriptions': [],
                'technologies': proj.get('technologies', []),
                'achievements': proj.get('achievements', [])
            }
            
            # Select best project description
            descriptions = proj.get('descriptions', [])
            if descriptions:
                if len(descriptions) == 1:
                    selected_proj['descriptions'] = [descriptions[0]]
                else:
                    best_description = self._ai_select_best_option(
                        descriptions, job_description, job_keywords, "project description"
                    )
                    selected_proj['descriptions'] = [best_description] if best_description else []
            
            selected_projects.append(selected_proj)
        
        return selected_projects
    
    def _select_skills_content(self, skills_data: Dict, job_description: str, job_keywords: List[str]) -> Dict:
        """Select most relevant skills for the job"""
        
        # For now, include all skills but prioritize based on job keywords
        # Could be enhanced with AI selection later
        return skills_data
    
    def _ai_select_best_option(self, options: List[str], job_description: str, job_keywords: List[str], content_type: str) -> str:
        """Use AI to select the single best option from a list"""
        
        if not options:
            return ""
        if len(options) == 1:
            return options[0]
        
        prompt = f"""
        Select the BEST {content_type} that matches this job.
        
        Job Keywords: {', '.join(job_keywords)}
        
        Options:
        {chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(options)])}
        
        Return only the number of the best option (1, 2, 3, etc.).
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            selection_num = int(response.choices[0].message.content.strip()) - 1
            if 0 <= selection_num < len(options):
                return options[selection_num]
            else:
                print(f"Invalid selection number: {selection_num}")
                return ["Error while selecting accomplishments. Please try again."]  # Fallback
                
        except Exception as e:
            print(f"Error selecting best {content_type}: {e}")
            return ["Error while selecting accomplishments. Please try again."]  # Fallback
    
    def _ai_select_multiple_options(self, options: List[str], job_description: str, job_keywords: List[str], content_type: str, max_selections: int = 6, min_selections: int=2) -> List[str]:
        """Use AI to select multiple best options from a list"""
        
        if not options:
            return []
        if len(options) <= min_selections:
            return options
        
        prompt = f"""
        Select the BEST {content_type} that match this job description.
        
        IMPORTANT RULES:
        1. Choose accomplishments that are MOST RELEVANT to the job requirements
        2. AVOID selecting accomplishments that describe the same achievement in different ways. Same achievements talk about the same result and same technology being used.
        3. Prioritize DIVERSE accomplishments that showcase different skills and impacts
        4. Select accomplishments with QUANTIFIABLE results when available
        5. Select between {min_selections} and {max_selections} accomplishments
        
        Job Keywords: {', '.join(job_keywords)}
        
        Options:
        {chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(options)])}
        
        Return only the numbers separated by commas (e.g., "1,3,5").
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            selection_text = response.choices[0].message.content.strip()
            selected_numbers = [int(num.strip()) - 1 for num in selection_text.split(',') if num.strip().isdigit()]
            selected_options = [options[i] for i in selected_numbers if 0 <= i < len(options)]
            
            if not selected_options:
                print(f"Fallback for selection option")
                selected_options = ["Error while selecting accomplishments. Please try again."]
                
            return selected_options
            
        except Exception as e:
            print(f"Error selecting multiple {content_type}: {e}")
            return ["Error while selecting accomplishments. Please try again."]  # Fallback