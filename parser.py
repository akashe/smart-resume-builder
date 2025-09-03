import io
import re
from docx import Document
import PyPDF2
from typing import Dict, List, Any
from openai import OpenAI
import os

class ResumeParser:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        self.section_keywords = {
            'experience': [
                'experience', 'employment', 'work history', 'professional experience', 
                'career', 'work experience', 'professional history', 'employment history',
                'career summary', 'work', 'professional background'
            ],
            'education': [
                'education', 'academic', 'degree', 'university', 'college', 'school',
                'academic background', 'educational background', 'qualifications',
                'academic qualifications', 'degrees', 'certification'
            ],
            'skills': [
                'skills', 'technical skills', 'competencies', 'technologies', 'programming',
                'technical competencies', 'core competencies', 'expertise', 'proficiencies',
                'technical expertise', 'programming languages', 'software', 'tools'
            ],
            'summary': [
                'summary', 'profile', 'objective', 'about', 'overview', 'professional summary',
                'career objective', 'professional profile', 'personal summary', 'introduction',
                'career summary', 'executive summary', 'professional overview'
            ],
            'projects': [
                'projects', 'portfolio', 'personal projects', 'side projects', 'key projects',
                'notable projects', 'academic projects', 'research projects', 'project experience'
            ],
            'certifications': [
                'certifications', 'certificates', 'credentials', 'licenses', 'professional certifications',
                'industry certifications', 'training', 'courses'
            ],
            'achievements': [
                'achievements', 'awards', 'honors', 'accomplishments', 'recognition',
                'accolades', 'distinctions', 'notable achievements'
            ]
        }
    
    def parse_file(self, uploaded_file) -> Dict[str, Any]:
        """Parse uploaded resume file and extract structured data"""
        
        if uploaded_file.type == "application/pdf":
            text = self._extract_pdf_text(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = self._extract_docx_text(uploaded_file)
        else:
            raise ValueError("Unsupported file format")
        
        # Use AI to help parse sections more accurately
        parsed_data = self._ai_parse_sections(text)
        
        return parsed_data
    
    def _extract_pdf_text(self, uploaded_file) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                # Clean up the text
                page_text = re.sub(r'\n\s*\n', '\n', page_text)  # Remove multiple newlines
                text += page_text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")
    
    def _extract_docx_text(self, uploaded_file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting DOCX text: {str(e)}")
    
    def _ai_parse_sections(self, text: str) -> Dict[str, Any]:
        """Use AI to intelligently parse resume sections into structured data"""
        
        try:
            prompt = f"""
            Parse this resume text into highly structured sections for intelligent job matching.
            
            Resume Text:
            {text}
            
            Return JSON with these EXACT structures:
            
            {{
                "contact": {{
                    "name": "Full Name",
                    "email": "email@domain.com", 
                    "phone": "phone number",
                    "location": "City, State",
                    "linkedin": "linkedin url",
                    "github": "github url",
                    "website": "personal website",
                    "title": "Professional Title/Designation (e.g., 'AI & NLP Expert', 'Senior Software Engineer')"
                }},
                "summary": {{
                    "sentences": [
                        "Individual sentence 1 from summary",
                        "Individual sentence 2 from summary",
                        "Individual sentence 3 from summary"
                    ]
                }},
                "experience": [
                    {{
                        "position": "Job Title",
                        "company": "Company Name", 
                        "duration": "Start Date - End Date",
                        "location": "City, State",
                        "role_summaries": [
                            "Brief role description option 1",
                            "Brief role description option 2"
                        ],
                        "accomplishments": [
                            "Specific achievement or responsibility 1",
                            "Specific achievement or responsibility 2",
                            "Quantified result or impact 3"
                        ]
                    }}
                ],
                "education": [
                    {{
                        "degree": "Degree Name",
                        "specialization": "Field of Study/Major/Specialization",
                        "institution": "School Name",
                        "graduation": "Year or Month/Year",
                        "location": "City, State",
                        "details": ["GPA: X.X", "Relevant coursework", "Honors/Awards"]
                    }}
                ],
                "skills": {{
                    "technical": ["skill1", "skill2", "skill3"],
                    "programming": ["language1", "language2"],
                    "tools": ["tool1", "tool2"],
                    "soft_skills": ["skill1", "skill2"]
                }},
                "projects": [
                    {{
                        "name": "Project Name",
                        "url": "project url if available",
                        "descriptions": [
                            "Project description variant 1",
                            "Project description variant 2"
                        ],
                        "technologies": ["tech1", "tech2"],
                        "achievements": ["measurable result 1", "key feature 2"]
                    }}
                ],
                "certifications": [
                    {{
                        "name": "Certification Name",
                        "issuer": "Issuing Organization",
                        "date": "Date obtained",
                        "expiry": "Expiry date if applicable"
                    }}
                ],
                "achievements": [
                    "Award or recognition 1",
                    "Notable accomplishment 2"
                ]
            }}
            
            IMPORTANT RULES:
            1. Break summary into individual sentences
            2. Each experience is a separate object with structured fields
            3. Each project is a separate object with multiple description options
            4. If information is missing, use empty string or empty array
            5. Extract ALL variations/details for maximum matching flexibility
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            import json
            ai_parsed = json.loads(response.choices[0].message.content)
            
            # Validate and clean the response
            return self._validate_ai_parsed_data(ai_parsed)
            
        except Exception as e:
            print(f"AI parsing failed: {e}, falling back to rule-based parsing")
            return self._fallback_parse(text)
    
    def _validate_ai_parsed_data(self, ai_parsed: Dict) -> Dict[str, Any]:
        """Validate and clean structured AI-parsed data"""
        
        validated_data = {}
        
        # Contact info - structured object
        if 'contact' in ai_parsed and isinstance(ai_parsed['contact'], dict):
            validated_data['contact'] = {
                'name': str(ai_parsed['contact'].get('name', '')).strip(),
                'email': str(ai_parsed['contact'].get('email', '')).strip(),
                'phone': str(ai_parsed['contact'].get('phone', '')).strip(),
                'location': str(ai_parsed['contact'].get('location', '')).strip(),
                'linkedin': str(ai_parsed['contact'].get('linkedin', '')).strip(),
                'github': str(ai_parsed['contact'].get('github', '')).strip(),
                'website': str(ai_parsed['contact'].get('website', '')).strip(),
                'title': str(ai_parsed['contact'].get('title', '')).strip()
            }
        else:
            validated_data['contact'] = {
                'name': '', 'email': '', 'phone': '', 'location': '', 
                'linkedin': '', 'github': '', 'website': '', 'title': ''
            }
        
        # Summary - array of sentences
        if 'summary' in ai_parsed and isinstance(ai_parsed['summary'], dict):
            sentences = ai_parsed['summary'].get('sentences', [])
            validated_data['summary'] = {
                'sentences': [str(s).strip() for s in sentences if str(s).strip()]
            }
        else:
            validated_data['summary'] = {'sentences': []}
        
        # Experience - array of structured objects
        if 'experience' in ai_parsed and isinstance(ai_parsed['experience'], list):
            validated_data['experience'] = []
            for exp in ai_parsed['experience']:
                if isinstance(exp, dict):
                    validated_data['experience'].append({
                        'position': str(exp.get('position', '')).strip(),
                        'company': str(exp.get('company', '')).strip(),
                        'duration': str(exp.get('duration', '')).strip(),
                        'location': str(exp.get('location', '')).strip(),
                        'role_summaries': [
                            str(rs).strip() for rs in exp.get('role_summaries', []) 
                            if str(rs).strip()
                        ],
                        'accomplishments': [
                            str(acc).strip() for acc in exp.get('accomplishments', [])
                            if str(acc).strip()
                        ]
                    })
        else:
            validated_data['experience'] = []
        
        # Education - array of structured objects
        if 'education' in ai_parsed and isinstance(ai_parsed['education'], list):
            validated_data['education'] = []
            for edu in ai_parsed['education']:
                if isinstance(edu, dict):
                    validated_data['education'].append({
                        'degree': str(edu.get('degree', '')).strip(),
                        'specialization': str(edu.get('specialization', '')).strip(),
                        'institution': str(edu.get('institution', '')).strip(),
                        'graduation': str(edu.get('graduation', '')).strip(),
                        'location': str(edu.get('location', '')).strip(),
                        'details': [
                            str(d).strip() for d in edu.get('details', [])
                            if str(d).strip()
                        ]
                    })
        else:
            validated_data['education'] = []
        
        # Skills - categorized object
        if 'skills' in ai_parsed and isinstance(ai_parsed['skills'], dict):
            skills_data = ai_parsed['skills']
            validated_data['skills'] = {
                'technical': [str(s).strip() for s in skills_data.get('technical', []) if str(s).strip()],
                'programming': [str(s).strip() for s in skills_data.get('programming', []) if str(s).strip()],
                'tools': [str(s).strip() for s in skills_data.get('tools', []) if str(s).strip()],
                'soft_skills': [str(s).strip() for s in skills_data.get('soft_skills', []) if str(s).strip()]
            }
        else:
            validated_data['skills'] = {
                'technical': [], 'programming': [], 'tools': [], 'soft_skills': []
            }
        
        # Projects - array of structured objects
        if 'projects' in ai_parsed and isinstance(ai_parsed['projects'], list):
            validated_data['projects'] = []
            for proj in ai_parsed['projects']:
                if isinstance(proj, dict):
                    validated_data['projects'].append({
                        'name': str(proj.get('name', '')).strip(),
                        'url': str(proj.get('url', '')).strip(),
                        'descriptions': [
                            str(desc).strip() for desc in proj.get('descriptions', [])
                            if str(desc).strip()
                        ],
                        'technologies': [
                            str(tech).strip() for tech in proj.get('technologies', [])
                            if str(tech).strip()
                        ],
                        'achievements': [
                            str(ach).strip() for ach in proj.get('achievements', [])
                            if str(ach).strip()
                        ]
                    })
        else:
            validated_data['projects'] = []
        
        # Certifications - array of structured objects
        if 'certifications' in ai_parsed and isinstance(ai_parsed['certifications'], list):
            validated_data['certifications'] = []
            for cert in ai_parsed['certifications']:
                if isinstance(cert, dict):
                    validated_data['certifications'].append({
                        'name': str(cert.get('name', '')).strip(),
                        'issuer': str(cert.get('issuer', '')).strip(),
                        'date': str(cert.get('date', '')).strip(),
                        'expiry': str(cert.get('expiry', '')).strip()
                    })
        else:
            validated_data['certifications'] = []
        
        # Achievements - simple array
        if 'achievements' in ai_parsed and isinstance(ai_parsed['achievements'], list):
            validated_data['achievements'] = [
                str(ach).strip() for ach in ai_parsed['achievements'] if str(ach).strip()
            ]
        else:
            validated_data['achievements'] = []
        
        return validated_data
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback to rule-based parsing if AI fails"""
        
        sections = {}
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract contact info first
        sections['contact'] = self._extract_contact_info(text)
        
        # Find section boundaries using improved detection
        section_boundaries = self._find_section_boundaries(lines)
        
        # Extract content for each section
        for section_name in ['summary', 'experience', 'education', 'skills', 'projects', 'certifications', 'achievements']:
            sections[section_name] = self._extract_section_content(
                lines, section_name, section_boundaries
            )
        
        return sections
    
    def _find_section_boundaries(self, lines: List[str]) -> Dict[str, int]:
        """Find where each section starts in the text"""
        
        boundaries = {}
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Skip very short lines or lines with too many words (unlikely to be headers)
            if len(line_lower) < 3 or len(line.split()) > 6:
                continue
            
            # Check for section headers
            for section_name, keywords in self.section_keywords.items():
                for keyword in keywords:
                    # More flexible matching
                    if keyword in line_lower:
                        # Additional checks to confirm it's a header
                        if (
                            line_lower == keyword or  # Exact match
                            line_lower.startswith(keyword) or  # Starts with keyword
                            (keyword in line_lower and len(line.split()) <= 3)  # Short line with keyword
                        ):
                            boundaries[section_name] = i
                            break
                
                if section_name in boundaries:
                    break
        
        return boundaries
    
    def _extract_section_content(self, lines: List[str], section_name: str, boundaries: Dict[str, int]) -> Dict[str, Any]:
        """Extract content for a specific section"""
        
        if section_name not in boundaries:
            return {'text': '', 'bullet_points': []}
        
        start_idx = boundaries[section_name] + 1  # Skip the header line
        
        # Find end of section (start of next section or end of document)
        end_idx = len(lines)
        current_section_start = boundaries[section_name]
        
        for other_section, other_start in boundaries.items():
            if other_start > current_section_start and other_start < end_idx:
                end_idx = other_start
        
        # Extract content between boundaries
        section_lines = lines[start_idx:end_idx]
        
        text_content = ""
        bullet_points = []
        
        for line in section_lines:
            if self._is_bullet_point(line):
                bullet_points.append(self._clean_bullet_point(line))
            else:
                # Only add to text if it's substantial content
                if len(line.strip()) > 10:
                    text_content += line + " "
        
        # Special handling for experience section
        if section_name == 'experience':
            job_entries = self._extract_job_entries_improved(section_lines)
            if job_entries:
                bullet_points = job_entries
        
        # Special handling for skills section
        elif section_name == 'skills':
            skills = self._extract_skills_improved(section_lines)
            if skills:
                bullet_points.extend(skills)
        
        return {
            'text': text_content.strip(),
            'bullet_points': bullet_points
        }
    
    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract contact information from text"""
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Extract phone - more comprehensive patterns
        phone_patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
        ]
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                phones.extend(['-'.join(match) for match in matches])
        
        # Extract LinkedIn
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+',
            r'http[s]?://(?:www\.)?linkedin\.com/in/[\w-]+'
        ]
        linkedins = []
        for pattern in linkedin_patterns:
            linkedins.extend(re.findall(pattern, text.lower()))
        
        # Extract name (first substantial line that looks like a name)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        potential_name = ""
        
        for line in lines[:5]:  # Check first 5 lines
            # Skip lines with contact info
            if any(pattern in line.lower() for pattern in ['@', 'phone', 'email', 'linkedin', 'github']):
                continue
            
            # Look for name-like patterns
            words = line.split()
            if (len(words) >= 2 and len(words) <= 4 and 
                all(word.replace(',', '').replace('.', '').isalpha() for word in words) and
                len(line) < 60):
                potential_name = line
                break
        
        contact_bullets = []
        if emails:
            contact_bullets.append(f"Email: {emails[0]}")
        if phones:
            contact_bullets.append(f"Phone: {phones[0]}")
        if linkedins:
            contact_bullets.append(f"LinkedIn: {linkedins[0]}")
        
        return {
            'text': potential_name,
            'bullet_points': contact_bullets
        }
    
    def _is_bullet_point(self, line: str) -> bool:
        """Check if line is a bullet point"""
        line = line.strip()
        bullet_indicators = ['•', '–', '-', '→', '▪', '▫', '◦', '*', '●', '○']
        
        return (
            any(line.startswith(indicator) for indicator in bullet_indicators) or
            (line and line[0].isdigit() and ('.', ')') in line[:3])
        )
    
    def _clean_bullet_point(self, line: str) -> str:
        """Clean bullet point text"""
        line = line.strip()
        
        # Remove bullet indicators
        bullet_indicators = ['•', '–', '-', '→', '▪', '▫', '◦', '*', '●', '○']
        for indicator in bullet_indicators:
            if line.startswith(indicator):
                line = line[len(indicator):].strip()
                break
        
        # Remove numbered list indicators
        if line and line[0].isdigit():
            if '.' in line[:4]:
                line = line.split('.', 1)[1].strip()
            elif ')' in line[:4]:
                line = line.split(')', 1)[1].strip()
        
        return line
    
    def _extract_job_entries_improved(self, lines: List[str]) -> List[str]:
        """Extract job entries with better logic"""
        
        job_entries = []
        current_job = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect job/company headers with better patterns
            if self._looks_like_job_header_improved(line):
                # Save previous job
                if current_job:
                    job_text = " ".join(current_job)
                    if len(job_text.strip()) > 15:
                        job_entries.append(job_text.strip())
                
                # Start new job
                current_job = [line]
            else:
                if current_job:  # Only add if we're in a job section
                    current_job.append(line)
        
        # Don't forget the last job
        if current_job:
            job_text = " ".join(current_job)
            if len(job_text.strip()) > 15:
                job_entries.append(job_text.strip())
        
        return job_entries
    
    def _looks_like_job_header_improved(self, line: str) -> bool:
        """Improved job header detection"""
        
        line_lower = line.lower()
        
        # Job title indicators
        job_titles = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator',
            'assistant', 'director', 'lead', 'senior', 'junior', 'intern', 'consultant',
            'architect', 'administrator', 'designer', 'scientist', 'researcher', 'officer',
            'executive', 'supervisor', 'technician', 'associate', 'representative'
        ]
        
        # Check for job titles
        if any(title in line_lower for title in job_titles):
            return True
        
        # Date patterns (common in job headers)
        date_patterns = [
            r'\b\d{4}\b',  # Year
            r'\d{1,2}/\d{4}',  # Month/Year
            r'\d{1,2}-\d{4}',  # Month-Year
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month names
            r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        ]
        
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in date_patterns):
            return True
        
        # Company-like patterns (capitalized words, reasonable length)
        words = line.split()
        if (len(words) <= 6 and len(words) >= 2 and
            sum(1 for word in words if word and word[0].isupper()) >= 2):
            return True
        
        return False
    
    def _extract_skills_improved(self, lines: List[str]) -> List[str]:
        """Extract skills with better parsing"""
        
        skills = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Split by common delimiters
            potential_skills = re.split(r'[,;|•–-]', line)
            
            for skill in potential_skills:
                skill = skill.strip()
                # Better skill validation
                if (skill and 2 <= len(skill) <= 50 and 
                    not any(char.isdigit() for char in skill[:3]) and  # Avoid dates/numbers
                    len(skill.split()) <= 4):  # Reasonable skill length
                    skills.append(skill)
        
        return skills