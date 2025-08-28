import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page imports
from parser import ResumeParser
from matcher import JobMatcher
from exporter import PDFExporter
from theme_exporter import ThemeExporter
import sqlite3
import json

# Initialize session state
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = None
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'selected_content' not in st.session_state:
    st.session_state.selected_content = None
if 'final_markdown' not in st.session_state:
    st.session_state.final_markdown = ""
if 'selected_theme' not in st.session_state:
    st.session_state.selected_theme = ('json_resume', 'professional')

def init_database():
    """Initialize SQLite database for storing resume data"""
    conn = sqlite3.connect('resume_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS resume_sections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  section_name TEXT,
                  content TEXT,
                  bullet_points TEXT)''')
    
    conn.commit()
    conn.close()

def main():
    st.set_page_config(
        page_title="Resume Matcher MVP",
        page_icon="📄",
        layout="wide"
    )
    
    # Initialize database
    init_database()
    
    st.title("📄 Resume Matcher MVP")
    st.markdown("**Upload → Parse → Match → Edit → Export**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    pages = [
        "1. Upload Resume",
        "2. Edit Sections", 
        "3. Job Matching",
        "4. Edit Markdown",
        "5. Export PDF"
    ]
    
    page = st.sidebar.radio("Go to:", pages)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please set your OPENAI_API_KEY in a .env file")
        st.stop()
    
    # Page routing
    if page == "1. Upload Resume":
        upload_resume_page()
    elif page == "2. Edit Sections":
        edit_sections_page()
    elif page == "3. Job Matching":
        job_matching_page()
    elif page == "4. Edit Markdown":
        edit_markdown_page()
    elif page == "5. Export PDF":
        export_pdf_page()

def upload_resume_page():
    st.header("📤 Upload and Parse Resume")
    
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=['pdf', 'docx'],
        help="Upload PDF or DOCX file"
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        if st.button("Parse Resume", type="primary"):
            with st.spinner("Parsing resume..."):
                parser = ResumeParser()
                
                try:
                    # Parse the resume
                    resume_data = parser.parse_file(uploaded_file)
                    st.session_state.resume_data = resume_data
                    
                    st.success("✅ Resume parsed successfully!")
                    
                    # Display structured parsed data
                    st.subheader("📋 Parsed Data Overview:")
                    
                    # Contact info
                    if resume_data.get('contact', {}).get('name'):
                        with st.expander("👤 Contact Information"):
                            contact = resume_data['contact']
                            if contact['name']: st.write(f"**Name:** {contact['name']}")
                            if contact['email']: st.write(f"**Email:** {contact['email']}")
                            if contact['phone']: st.write(f"**Phone:** {contact['phone']}")
                            if contact['linkedin']: st.write(f"**LinkedIn:** {contact['linkedin']}")
                    
                    # Summary sentences
                    if resume_data.get('summary', {}).get('sentences'):
                        with st.expander(f"📝 Summary ({len(resume_data['summary']['sentences'])} sentences)"):
                            for i, sentence in enumerate(resume_data['summary']['sentences'], 1):
                                st.write(f"{i}. {sentence}")
                    
                    # Experience
                    if resume_data.get('experience'):
                        with st.expander(f"💼 Experience ({len(resume_data['experience'])} positions)"):
                            for i, exp in enumerate(resume_data['experience'], 1):
                                st.write(f"**{i}. {exp['position']} at {exp['company']}**")
                                if exp['duration']: st.write(f"   📅 {exp['duration']}")
                                st.write(f"   📍 Role Summaries: {len(exp.get('role_summaries', []))}")
                                st.write(f"   🎯 Accomplishments: {len(exp.get('accomplishments', []))}")
                    
                    # Projects
                    if resume_data.get('projects'):
                        with st.expander(f"🚀 Projects ({len(resume_data['projects'])} projects)"):
                            for i, proj in enumerate(resume_data['projects'], 1):
                                st.write(f"**{i}. {proj['name']}**")
                                st.write(f"   📝 Descriptions: {len(proj.get('descriptions', []))}")
                                if proj.get('technologies'):
                                    st.write(f"   🔧 Tech: {', '.join(proj['technologies'][:3])}...")
                    
                    # Skills
                    if resume_data.get('skills'):
                        skills = resume_data['skills']
                        total_skills = sum(len(skills[cat]) for cat in skills)
                        if total_skills > 0:
                            with st.expander(f"🛠️ Skills ({total_skills} total)"):
                                for category, skill_list in skills.items():
                                    if skill_list:
                                        st.write(f"**{category.title()}:** {len(skill_list)} skills")
                    
                    st.info("👉 Go to 'Edit Sections' to add variations and modify structured content")
                    
                except Exception as e:
                    st.error(f"Error parsing resume: {str(e)}")
                    st.exception(e)
    
    else:
        st.info("Please upload a resume file to get started")

def edit_sections_page():
    st.header("✏️ Edit Structured Resume Data")
    
    if not st.session_state.resume_data:
        st.warning("Please upload and parse a resume first!")
        return
    
    resume_data = st.session_state.resume_data
    
    st.markdown("*Add multiple variations so AI can select the best match for each job*")
    
    # Section tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Summary", "💼 Experience", "🚀 Projects", "🛠️ Skills", "🎓 Education"])
    
    with tab1:
        st.subheader("Summary Sentences")
        st.markdown("*Each sentence can be mixed and matched for different jobs*")
        
        if 'summary' not in resume_data:
            resume_data['summary'] = {'sentences': []}
        
        sentences = resume_data['summary'].get('sentences', [])
        
        # Edit existing sentences
        updated_sentences = []
        for i, sentence in enumerate(sentences):
            updated_sentence = st.text_area(
                f"Sentence {i+1}:",
                value=sentence,
                height=60,
                key=f"summary_sentence_{i}"
            )
            if updated_sentence.strip():
                updated_sentences.append(updated_sentence.strip())
        
        # Add new sentences
        new_sentence_count = st.number_input("Add new sentences:", min_value=0, max_value=5, value=0, key="new_summary")
        for i in range(new_sentence_count):
            new_sentence = st.text_area(f"New Sentence {i+1}:", height=60, key=f"new_summary_{i}")
            if new_sentence.strip():
                updated_sentences.append(new_sentence.strip())
        
        resume_data['summary']['sentences'] = updated_sentences
    
    with tab2:
        st.subheader("Work Experience")
        
        if 'experience' not in resume_data:
            resume_data['experience'] = []
        
        experiences = resume_data['experience']
        
        for exp_idx, exp in enumerate(experiences):
            with st.expander(f"📍 {exp.get('position', 'Position')} at {exp.get('company', 'Company')}", expanded=True):
                
                col1, col2 = st.columns(2)
                with col1:
                    exp['position'] = st.text_input("Position:", value=exp.get('position', ''), key=f"exp_pos_{exp_idx}")
                    exp['company'] = st.text_input("Company:", value=exp.get('company', ''), key=f"exp_comp_{exp_idx}")
                with col2:
                    exp['duration'] = st.text_input("Duration:", value=exp.get('duration', ''), key=f"exp_dur_{exp_idx}")
                    exp['location'] = st.text_input("Location:", value=exp.get('location', ''), key=f"exp_loc_{exp_idx}")
                
                st.markdown("**Role Summaries (different ways to describe the role):**")
                role_summaries = exp.get('role_summaries', [])
                updated_summaries = []
                for i, summary in enumerate(role_summaries):
                    updated_summary = st.text_area(f"Role Summary {i+1}:", value=summary, height=50, key=f"exp_summary_{exp_idx}_{i}")
                    if updated_summary.strip():
                        updated_summaries.append(updated_summary.strip())
                
                # Add new role summaries
                new_summary_count = st.number_input("Add role summaries:", min_value=0, max_value=3, value=0, key=f"new_role_summary_{exp_idx}")
                for i in range(new_summary_count):
                    new_summary = st.text_area(f"New Role Summary {i+1}:", height=50, key=f"new_exp_summary_{exp_idx}_{i}")
                    if new_summary.strip():
                        updated_summaries.append(new_summary.strip())
                exp['role_summaries'] = updated_summaries
                
                st.markdown("**Accomplishments & Responsibilities:**")
                accomplishments = exp.get('accomplishments', [])
                updated_accomplishments = []
                for i, acc in enumerate(accomplishments):
                    updated_acc = st.text_area(f"Accomplishment {i+1}:", value=acc, height=60, key=f"exp_acc_{exp_idx}_{i}")
                    if updated_acc.strip():
                        updated_accomplishments.append(updated_acc.strip())
                
                # Add new accomplishments
                new_acc_count = st.number_input("Add accomplishments:", min_value=0, max_value=5, value=0, key=f"new_acc_{exp_idx}")
                for i in range(new_acc_count):
                    new_acc = st.text_area(f"New Accomplishment {i+1}:", height=60, key=f"new_exp_acc_{exp_idx}_{i}")
                    if new_acc.strip():
                        updated_accomplishments.append(new_acc.strip())
                exp['accomplishments'] = updated_accomplishments
        
        # Add new experience
        if st.button("➕ Add New Experience"):
            new_exp = {
                'position': '', 'company': '', 'duration': '', 'location': '',
                'role_summaries': [], 'accomplishments': []
            }
            resume_data['experience'].append(new_exp)
            st.rerun()
    
    with tab3:
        st.subheader("Projects")
        
        if 'projects' not in resume_data:
            resume_data['projects'] = []
        
        projects = resume_data['projects']
        
        for proj_idx, proj in enumerate(projects):
            with st.expander(f"🚀 {proj.get('name', 'Project Name')}", expanded=True):
                
                col1, col2 = st.columns(2)
                with col1:
                    proj['name'] = st.text_input("Project Name:", value=proj.get('name', ''), key=f"proj_name_{proj_idx}")
                with col2:
                    proj['url'] = st.text_input("URL (optional):", value=proj.get('url', ''), key=f"proj_url_{proj_idx}")
                
                st.markdown("**Project Descriptions (different ways to describe it):**")
                descriptions = proj.get('descriptions', [])
                updated_descriptions = []
                for i, desc in enumerate(descriptions):
                    updated_desc = st.text_area(f"Description {i+1}:", value=desc, height=60, key=f"proj_desc_{proj_idx}_{i}")
                    if updated_desc.strip():
                        updated_descriptions.append(updated_desc.strip())
                
                # Add new descriptions
                new_desc_count = st.number_input("Add descriptions:", min_value=0, max_value=3, value=0, key=f"new_desc_{proj_idx}")
                for i in range(new_desc_count):
                    new_desc = st.text_area(f"New Description {i+1}:", height=60, key=f"new_proj_desc_{proj_idx}_{i}")
                    if new_desc.strip():
                        updated_descriptions.append(new_desc.strip())
                proj['descriptions'] = updated_descriptions
                
                # Technologies
                tech_list = ', '.join(proj.get('technologies', []))
                new_tech_list = st.text_input("Technologies (comma-separated):", value=tech_list, key=f"proj_tech_{proj_idx}")
                proj['technologies'] = [t.strip() for t in new_tech_list.split(',') if t.strip()]
        
        # Add new project
        if st.button("➕ Add New Project"):
            new_proj = {'name': '', 'url': '', 'descriptions': [], 'technologies': [], 'achievements': []}
            resume_data['projects'].append(new_proj)
            st.rerun()
    
    with tab4:
        st.subheader("Skills")
        
        if 'skills' not in resume_data:
            resume_data['skills'] = {'technical': [], 'programming': [], 'tools': [], 'soft_skills': []}
        
        skills = resume_data['skills']
        
        for category in ['technical', 'programming', 'tools', 'soft_skills']:
            skill_list = ', '.join(skills.get(category, []))
            updated_skills = st.text_input(f"{category.replace('_', ' ').title()} Skills:", value=skill_list, key=f"skills_{category}")
            skills[category] = [s.strip() for s in updated_skills.split(',') if s.strip()]
    
    with tab5:
        st.subheader("Education")
        
        if 'education' not in resume_data:
            resume_data['education'] = []
        
        education = resume_data['education']
        
        for edu_idx, edu in enumerate(education):
            with st.expander(f"🎓 {edu.get('degree', 'Degree')} - {edu.get('institution', 'Institution')}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    edu['degree'] = st.text_input("Degree:", value=edu.get('degree', ''), key=f"edu_deg_{edu_idx}")
                    edu['institution'] = st.text_input("Institution:", value=edu.get('institution', ''), key=f"edu_inst_{edu_idx}")
                with col2:
                    edu['graduation'] = st.text_input("Graduation:", value=edu.get('graduation', ''), key=f"edu_grad_{edu_idx}")
                    edu['location'] = st.text_input("Location:", value=edu.get('location', ''), key=f"edu_loc_{edu_idx}")
    
    # Save button
    if st.button("💾 Save All Changes", type="primary"):
        st.session_state.resume_data = resume_data
        st.success("✅ All changes saved!")
        st.rerun()
    
    st.info("👉 Go to 'Job Matching' to create a tailored resume")

def job_matching_page():
    st.header("🎯 Job Matching")
    
    if not st.session_state.resume_data:
        st.warning("Please upload and parse a resume first!")
        return
    
    st.subheader("Job Description")
    job_description = st.text_area(
        "Paste the job description here:",
        value=st.session_state.job_description,
        height=200,
        placeholder="Paste the complete job posting here..."
    )
    
    st.session_state.job_description = job_description
    
    # Always show the button, make it more prominent
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button(
            "🤖 Generate Matched Resume", 
            type="primary",
            use_container_width=True,
            disabled=not job_description.strip()
        )
    
    if generate_button and job_description.strip():
        with st.spinner("AI is selecting the best content for this job..."):
            try:
                matcher = JobMatcher()
                
                # Generate matched content
                selected_content = matcher.match_resume_to_job(
                    st.session_state.resume_data,
                    job_description
                )
                
                st.session_state.selected_content = selected_content
                
                st.success("✅ Resume matched successfully!")
                
                # Display selected content with proper structured format
                st.subheader("🎯 AI Selected Content")
                
                # Contact
                if 'contact' in selected_content:
                    contact = selected_content['contact']
                    with st.expander("👤 Contact"):
                        if contact.get('name'):
                            st.write(f"**Name:** {contact['name']}")
                        if contact.get('email'):
                            st.write(f"**Email:** {contact['email']}")
                        if contact.get('phone'):
                            st.write(f"**Phone:** {contact['phone']}")
                
                # Summary
                if 'summary' in selected_content:
                    summary = selected_content['summary']
                    with st.expander("📝 Summary"):
                        selected_sentences = summary.get('selected_sentences', [])
                        if selected_sentences:
                            for i, sentence in enumerate(selected_sentences, 1):
                                st.write(f"{i}. {sentence}")
                        else:
                            st.write("No sentences selected")
                
                # Experience
                if 'experience' in selected_content:
                    experiences = selected_content['experience']
                    with st.expander("💼 Experience"):
                        if experiences:
                            for i, exp in enumerate(experiences, 1):
                                st.write(f"**{i}. {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')}**")
                                if exp.get('selected_role_summary'):
                                    st.write(f"📝 Role: {exp['selected_role_summary']}")
                                if exp.get('selected_accomplishments'):
                                    st.write("🎯 Selected accomplishments:")
                                    for acc in exp['selected_accomplishments']:
                                        st.write(f"  • {acc}")
                        else:
                            st.write("No experience selected")
                
                # Projects
                if 'projects' in selected_content:
                    projects = selected_content['projects']
                    with st.expander("🚀 Projects"):
                        if projects:
                            for i, proj in enumerate(projects, 1):
                                st.write(f"**{i}. {proj.get('name', 'N/A')}**")
                                if proj.get('selected_description'):
                                    st.write(f"📝 Description: {proj['selected_description']}")
                        else:
                            st.write("No projects selected")
                
                # Skills
                if 'skills' in selected_content:
                    skills = selected_content['skills']
                    with st.expander("🛠️ Skills"):
                        for category, skill_list in skills.items():
                            if skill_list:
                                st.write(f"**{category.title()}:** {', '.join(skill_list)}")
                
                # Generate initial markdown
                markdown_content = matcher.generate_markdown(selected_content)
                st.session_state.final_markdown = markdown_content
                
                st.info("👉 Go to 'Edit Markdown' to review and modify the generated resume")
                
            except Exception as e:
                st.error(f"Error during job matching: {str(e)}")
                
                # Debug information
                st.subheader("🔍 Debug Info")
                st.write("Resume data structure:")
                st.json(st.session_state.resume_data)
                
                if 'selected_content' in locals():
                    st.write("Selected content structure:")
                    st.json(selected_content)
    
    elif not job_description.strip():
        st.info("Please paste a job description to proceed")

def edit_markdown_page():
    st.header("📝 Edit Markdown Resume")
    
    if not st.session_state.final_markdown:
        st.warning("Please complete job matching first!")
        return
    
    st.subheader("Markdown Editor")
    
    # Use streamlit-ace for better editing experience
    try:
        from streamlit_ace import st_ace
        
        edited_markdown = st_ace(
            value=st.session_state.final_markdown,
            language='markdown',
            theme='github',
            height=600,
            auto_update=False,
            key="markdown_editor"
        )
        
    except ImportError:
        # Fallback to text area if streamlit-ace is not available
        edited_markdown = st.text_area(
            "Edit your resume markdown:",
            value=st.session_state.final_markdown,
            height=600
        )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            st.session_state.final_markdown = edited_markdown
            st.success("✅ Markdown saved!")
    
    with col2:
        if st.button("👁️ Preview"):
            with st.expander("Preview", expanded=True):
                st.markdown(edited_markdown)
    
    st.info("👉 Go to 'Export PDF' to generate the final resume")

def export_pdf_page():
    st.header("📄 Export to PDF")
    
    if not st.session_state.resume_data:
        st.warning("Please upload and parse a resume first!")
        return
    
    # Theme Selection Section
    st.subheader("🎨 Choose Resume Theme")
    
    try:
        theme_exporter = ThemeExporter()
        available_themes = theme_exporter.get_theme_list()
        
        # Create theme options for selectbox
        theme_options = []
        theme_mapping = {}
        
        for engine, theme_name, _ in available_themes:
            display_name = f"{engine} - {theme_name.title()}"
            theme_options.append(display_name)
            theme_mapping[display_name] = (engine.lower().replace(' ', '_'), theme_name)
        
        # Theme selection
        selected_display = st.selectbox(
            "Select a theme:",
            theme_options,
            index=0,
            help="Choose from various professional resume themes"
        )
        
        selected_engine, selected_theme = theme_mapping[selected_display]
        st.session_state.selected_theme = (selected_engine, selected_theme)
        
        # Show theme info
        theme_info = theme_exporter.get_theme_info(selected_engine, selected_theme)
        if theme_info:
            st.info(f"📝 {theme_info}")
        
        # Preview section (only for JSON Resume themes)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if selected_engine == 'json_resume':
                if st.button("👁️ Preview Theme", help="Generate HTML preview"):
                    with st.spinner("Generating preview..."):
                        try:
                            html_preview = theme_exporter.preview_theme(
                                st.session_state.resume_data, 
                                selected_engine, 
                                selected_theme
                            )
                            
                            # Display preview in expander
                            with st.expander("Theme Preview", expanded=True):
                                st.components.v1.html(html_preview, height=400, scrolling=True)
                                
                        except Exception as e:
                            st.error(f"Preview error: {str(e)}")
            else:
                st.info("Preview available only for JSON Resume themes")
        
        with col2:
            # Generate PDF button
            if st.button("📄 Generate PDF", type="primary"):
                with st.spinner(f"Generating PDF with {selected_display}..."):
                    try:
                        # Use selected content if available, otherwise use full resume data
                        resume_data = st.session_state.selected_content or st.session_state.resume_data
                        
                        pdf_bytes = theme_exporter.export_resume(
                            resume_data,
                            selected_engine,
                            selected_theme,
                            'pdf'
                        )
                        
                        # Filename based on theme
                        filename = f"resume_{selected_theme}_{selected_engine}.pdf"
                        
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf"
                        )
                        
                        st.success("✅ PDF generated successfully!")
                        
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        st.exception(e)
        
        # Additional export options
        st.subheader("📋 Additional Options")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("📄 Export All Themes", help="Generate PDFs with multiple themes"):
                with st.spinner("Generating multiple themes..."):
                    try:
                        resume_data = st.session_state.selected_content or st.session_state.resume_data
                        
                        # Generate a few popular themes
                        popular_themes = [
                            ('json_resume', 'professional'),
                            ('json_resume', 'elegant'),
                            ('json_resume', 'stackoverflow'),
                            ('reportlab', 'professional')
                        ]
                        
                        for engine, theme in popular_themes:
                            try:
                                pdf_bytes = theme_exporter.export_resume(
                                    resume_data, engine, theme, 'pdf'
                                )
                                
                                filename = f"resume_{theme}_{engine}.pdf"
                                st.download_button(
                                    label=f"⬇️ {engine.title()} - {theme.title()}",
                                    data=pdf_bytes,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=f"download_{engine}_{theme}"
                                )
                            except Exception as e:
                                st.warning(f"Could not generate {engine} - {theme}: {str(e)}")
                        
                        st.success("✅ Multiple themes generated!")
                        
                    except Exception as e:
                        st.error(f"Error generating multiple themes: {str(e)}")
        
        with col4:
            if st.button("📋 Copy Markdown"):
                if st.session_state.final_markdown:
                    st.code(st.session_state.final_markdown, language="markdown")
                    st.info("Copy the markdown above to use elsewhere")
                else:
                    st.warning("No markdown content available. Please complete job matching first.")
    
    except Exception as e:
        st.error(f"Theme system error: {str(e)}")
        st.info("Falling back to basic export...")
        
        # Fallback to original export
        if st.session_state.final_markdown:
            if st.button("📄 Generate Basic PDF", type="primary"):
                with st.spinner("Generating PDF..."):
                    try:
                        exporter = PDFExporter()
                        pdf_bytes = exporter.markdown_to_pdf(
                            st.session_state.final_markdown,
                            filename="resume.pdf"
                        )
                        
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name="resume.pdf",
                            mime="application/pdf"
                        )
                        
                        st.success("✅ PDF generated successfully!")
                        
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
        else:
            st.warning("Please complete markdown editing first!")

if __name__ == "__main__":
    main()