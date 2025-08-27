import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from typing import Optional
from io import BytesIO
import re

class PDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create elegant, minimal styles for professional resume"""
        
        # Define elegant color palette
        dark_text = colors.Color(0.15, 0.15, 0.15)  # Near black
        accent_color = colors.Color(0.2, 0.3, 0.5)  # Professional blue-gray
        light_gray = colors.Color(0.7, 0.7, 0.7)    # Light gray for lines
        
        # Name/Title style - Clean and prominent
        self.name_style = ParagraphStyle(
            'Name',
            parent=self.styles['Heading1'],
            fontSize=28,
            alignment=TA_CENTER,
            spaceAfter=8,
            textColor=dark_text,
            fontName='Helvetica-Bold',
            leading=32
        )
        
        # Contact info style - Elegant and understated
        self.contact_style = ParagraphStyle(
            'Contact',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=24,
            textColor=colors.Color(0.4, 0.4, 0.4),
            fontName='Helvetica'
        )
        
        # Section header style - Clean with subtle line
        self.section_style = ParagraphStyle(
            'Section',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=accent_color,
            fontName='Helvetica-Bold',
            leading=16
        )
        
        # Job title/company style - Professional hierarchy
        self.job_title_style = ParagraphStyle(
            'JobTitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=4,
            textColor=dark_text,
            fontName='Helvetica-Bold',
            leading=14
        )
        
        # Job details style (dates, location)
        self.job_details_style = ParagraphStyle(
            'JobDetails',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.Color(0.5, 0.5, 0.5),
            fontName='Helvetica-Oblique'
        )
        
        # Role description style
        self.role_desc_style = ParagraphStyle(
            'RoleDescription', 
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=dark_text,
            fontName='Helvetica',
            leading=13
        )
        
        # Bullet point style - Clean and well-spaced
        self.bullet_style = ParagraphStyle(
            'Bullet',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            leftIndent=16,
            bulletIndent=8,
            textColor=dark_text,
            fontName='Helvetica',
            leading=13
        )
        
        # Skills/Education content style
        self.content_style = ParagraphStyle(
            'Content',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=dark_text,
            fontName='Helvetica',
            leading=13
        )
        
        # Summary style - Slightly larger for readability
        self.summary_style = ParagraphStyle(
            'Summary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=16,
            textColor=dark_text,
            fontName='Helvetica',
            leading=15,
            alignment=TA_JUSTIFY
        )
    
    def markdown_to_pdf(self, markdown_content: str, filename: Optional[str] = None) -> bytes:
        """Convert markdown to ATS-friendly PDF using ReportLab"""
        
        buffer = BytesIO()
        
        # Create document with professional margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.8*inch,
            bottomMargin=0.8*inch, 
            leftMargin=0.9*inch,
            rightMargin=0.9*inch,
            title="Professional Resume"
        )
        
        # Parse markdown and create story
        story = self._parse_markdown_to_story(markdown_content)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        buffer.seek(0)
        return buffer.getvalue()
    
    def _parse_markdown_to_story(self, markdown_content: str) -> list:
        """Parse markdown content into elegant ReportLab story elements"""
        from reportlab.platypus import HRFlowable
        
        story = []
        lines = markdown_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            if line.startswith('# '):
                # Name - Clean and prominent
                name = line[2:].strip()
                story.append(Paragraph(name, self.name_style))
                
            elif line.startswith('## '):
                # Section headers - Add elegant spacing and subtle line
                section_title = line[3:].strip()
                story.append(Spacer(1, 8))
                story.append(Paragraph(section_title, self.section_style))
                
                # Add subtle line under section header
                story.append(Spacer(1, 2))
                story.append(HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=colors.Color(0.7, 0.7, 0.7),
                    spaceAfter=8
                ))
                
            elif line.startswith('### '):
                # Job titles/education - Professional hierarchy
                job_title = line[4:].strip()
                story.append(Paragraph(job_title, self.job_title_style))
                
            elif line.startswith('• '):
                # Bullet points - Clean formatting
                bullet_text = line[2:].strip()
                story.append(Paragraph(f"• {bullet_text}", self.bullet_style))
                
            elif '|' in line and i < 5:  
                # Contact info - Clean and centered
                story.append(Paragraph(line, self.contact_style))
                
            elif line.startswith('**') and line.endswith('**'):
                # Bold content like "Technologies: Python, React"
                content = line[2:-2]  # Remove ** markers
                story.append(Paragraph(content, self.content_style))
                
            else:
                # Regular content - Check if it's a summary or description
                if i < 10 and len(line) > 50:  # Likely summary
                    story.append(Paragraph(line, self.summary_style))
                elif line:
                    story.append(Paragraph(line, self.content_style))
            
            i += 1
        
        return story
    
    def save_pdf_file(self, markdown_content: str, output_path: str) -> str:
        """Save PDF to file and return the path"""
        
        pdf_bytes = self.markdown_to_pdf(markdown_content)
        
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        return output_path
    
    def validate_pdf_generation(self) -> bool:
        """Test if PDF generation is working properly"""
        
        test_markdown = """# Test Resume

test@email.com | (555) 123-4567

## Summary
This is a test resume to validate PDF generation.

## Experience
• Test bullet point
• Another test point

## Skills
Python, JavaScript, React"""
        
        try:
            pdf_bytes = self.markdown_to_pdf(test_markdown)
            return len(pdf_bytes) > 1000
        except Exception:
            return False