import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page imports
from parser import ResumeParser
from matcher import JobMatcher
from theme_exporter import ThemeExporter
from company_analyzer import CompanyAnalyzer
from positioning_coach import PositioningCoach
from company_researcher import CompanyResearcher
from db_operations import *

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
if 'company_analysis' not in st.session_state:
    st.session_state.company_analysis = None
if 'show_final_editor' not in st.session_state:
    st.session_state.show_final_editor = False

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
        "2. Edit & Add Information", 
        "3. Job Matching",
        "4. Edit Resume Sections",
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
    elif page == "2. Edit & Add Information":
        edit_sections_page()
    elif page == "3. Job Matching":
        job_matching_page()
    elif page == "4. Edit Resume Sections":
        edit_markdown_page()
    elif page == "5. Export PDF":
        export_pdf_page()

def upload_resume_page():
    st.header("📤 Upload and Parse Resume")

    # Load from DB option
    profiles = load_resume_profiles()

    if profiles:
        profile_options = {f"{name} (ID: {pid})": pid for pid, name in profiles}
        selected_profile = st.selectbox("Or load a saved profile:", ["Dont want to load a saved profile"] + list(profile_options.keys()))
        if selected_profile != "Dont want to load a saved profile":
            profile_id = profile_options[selected_profile]
            resume_data = get_resume_by_id(profile_id)
            st.session_state.resume_data = resume_data
            st.success(f"Loaded profile: {selected_profile}")
            st.stop()
    
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
                        with st.expander("👤 Contact Information (Editable in Edit Sections)"):
                            contact = resume_data['contact']
                            if contact['name']: st.write(f"**Name:** {contact['name']}")
                            if contact.get('title'): st.write(f"**Title:** {contact['title']}")
                            if contact['email']: st.write(f"**Email:** {contact['email']}")
                            if contact['phone']: st.write(f"**Phone:** {contact['phone']}")
                            if contact.get('location'): st.write(f"**Location:** {contact['location']}")
                            if contact['linkedin']: st.write(f"**LinkedIn:** {contact['linkedin']}")
                            if contact.get('github'): st.write(f"**GitHub:** {contact['github']}")
                            if contact.get('website'): st.write(f"**Website:** {contact['website']}")
                    
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
    st.header("✏️ Edit & Add Information")
    
    if not st.session_state.resume_data:
        st.warning("Please upload and parse a resume first!")
        return
    
    resume_data = st.session_state.resume_data
    
    st.markdown("*Add multiple variations and expand your resume content so AI can select the best match for each job*")
    
    # Simple guidance without AI suggestion references
    st.info("💡 Add variations and details here → Go to 'Job Matching' for AI analysis → Use 'Edit Resume Sections' for AI suggestions")
    
    # Section tabs
    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Contact", "📝 Summary", "💼 Experience", "🚀 Projects", "🛠️ Skills", "🎓 Education"])
    
    with tab0:
        st.subheader("Contact Information")
        st.markdown("*Edit your contact details and professional title*")
        
        if 'contact' not in resume_data:
            resume_data['contact'] = {
                'name': '', 'email': '', 'phone': '', 'location': '', 
                'linkedin': '', 'github': '', 'website': '', 'title': ''
            }
        
        contact = resume_data['contact']
        
        col1, col2 = st.columns(2)
        with col1:
            contact['name'] = st.text_input("Full Name:", value=contact.get('name', ''), key="contact_name")
            contact['title'] = st.text_input("Professional Title/Designation:", value=contact.get('title', ''), 
                                           placeholder="e.g., AI & NLP Expert, Senior Software Engineer", key="contact_title")
            contact['email'] = st.text_input("Email:", value=contact.get('email', ''), key="contact_email")
            contact['phone'] = st.text_input("Phone:", value=contact.get('phone', ''), key="contact_phone")
        
        with col2:
            contact['location'] = st.text_input("Location:", value=contact.get('location', ''), 
                                              placeholder="City, State", key="contact_location")
            contact['linkedin'] = st.text_input("LinkedIn URL:", value=contact.get('linkedin', ''), 
                                              placeholder="https://linkedin.com/in/username", key="contact_linkedin")
            contact['github'] = st.text_input("GitHub URL:", value=contact.get('github', ''), 
                                            placeholder="https://github.com/username", key="contact_github")
            contact['website'] = st.text_input("Personal Website:", value=contact.get('website', ''), 
                                             placeholder="https://yourwebsite.com", key="contact_website")
    
    with tab1:
        st.subheader("Summary Sentences")
        st.markdown("*Each sentence can be mixed and matched for different jobs*")
        
        if 'summary' not in resume_data:
            resume_data['summary'] = {'sentences': []}
        
        sentences = st.session_state.resume_data['summary'].get('sentences', [])
        
        # Edit existing sentences - update session state directly
        for i, sentence in enumerate(sentences):
            col1, col2 = st.columns([5, 1])
            with col1:
                updated_sentence = st.text_area(
                    f"Sentence {i+1}:",
                    value=sentence,
                    height=60,
                    key=f"summary_sentence_{i}"
                )
                # Update session state immediately on change
                if updated_sentence != sentence:
                    st.session_state.resume_data['summary']['sentences'][i] = updated_sentence
            with col2:
                st.write("")  # spacer
                if st.button("🗑️", key=f"delete_summary_{i}", help="Delete this sentence"):
                    # Remove the sentence and refresh
                    st.session_state.resume_data['summary']['sentences'].pop(i)
                    st.rerun()
        
        # Add new sentence
        if st.button("➕ Add New Sentence", key="add_summary_btn"):
            st.session_state.resume_data['summary']['sentences'].append("")
            st.rerun()
    
    with tab2:
        st.subheader("Work Experience")
        
        if 'experience' not in resume_data:
            resume_data['experience'] = []
        
        experiences = st.session_state.resume_data['experience']
        
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
                for i, summary in enumerate(role_summaries):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        updated_summary = st.text_area(f"Role Summary {i+1}:", value=summary, height=50, key=f"exp_summary_{exp_idx}_{i}")
                        # Update session state immediately on change
                        if updated_summary != summary:
                            st.session_state.resume_data['experience'][exp_idx]['role_summaries'][i] = updated_summary
                    with col2:
                        st.write("")  # spacer
                        if st.button("🗑️", key=f"delete_role_summary_{exp_idx}_{i}", help="Delete this role summary"):
                            # Remove the role summary and refresh
                            st.session_state.resume_data['experience'][exp_idx]['role_summaries'].pop(i)
                            st.rerun()
                
                # Add new role summary
                if st.button("➕ Add Role Summary", key=f"add_role_summary_{exp_idx}"):
                    st.session_state.resume_data['experience'][exp_idx]['role_summaries'].append("")
                    st.rerun()
                
                st.markdown("**Accomplishments & Responsibilities:**")
                accomplishments = exp.get('accomplishments', [])
                for i, acc in enumerate(accomplishments):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        updated_acc = st.text_area(f"Accomplishment {i+1}:", value=acc, height=60, key=f"exp_acc_{exp_idx}_{i}")
                        # Update session state immediately on change
                        if updated_acc != acc:
                            st.session_state.resume_data['experience'][exp_idx]['accomplishments'][i] = updated_acc
                    with col2:
                        st.write("")  # spacer
                        if st.button("🗑️", key=f"delete_accomplishment_{exp_idx}_{i}", help="Delete this accomplishment"):
                            # Remove the accomplishment and refresh
                            st.session_state.resume_data['experience'][exp_idx]['accomplishments'].pop(i)
                            st.rerun()
                
                # Add new accomplishment
                if st.button("➕ Add Accomplishment", key=f"add_accomplishment_{exp_idx}"):
                    st.session_state.resume_data['experience'][exp_idx]['accomplishments'].append("")
                    st.rerun()
        
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
        
        projects = st.session_state.resume_data['projects']
        
        for proj_idx, proj in enumerate(projects):
            with st.expander(f"🚀 {proj.get('name', 'Project Name')}", expanded=True):
                
                col1, col2 = st.columns(2)
                with col1:
                    proj['name'] = st.text_input("Project Name:", value=proj.get('name', ''), key=f"proj_name_{proj_idx}")
                with col2:
                    proj['url'] = st.text_input("URL (optional):", value=proj.get('url', ''), key=f"proj_url_{proj_idx}")
                
                st.markdown("**Project Descriptions (different ways to describe it):**")
                descriptions = proj.get('descriptions', [])
                for i, desc in enumerate(descriptions):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        updated_desc = st.text_area(f"Description {i+1}:", value=desc, height=60, key=f"proj_desc_{proj_idx}_{i}")
                        # Update session state immediately on change
                        if updated_desc != desc:
                            st.session_state.resume_data['projects'][proj_idx]['descriptions'][i] = updated_desc
                    with col2:
                        st.write("")  # spacer
                        if st.button("🗑️", key=f"delete_project_desc_{proj_idx}_{i}", help="Delete this description"):
                            # Remove the project description and refresh
                            st.session_state.resume_data['projects'][proj_idx]['descriptions'].pop(i)
                            st.rerun()
                
                # Add new description
                if st.button("➕ Add Description", key=f"add_description_{proj_idx}"):
                    st.session_state.resume_data['projects'][proj_idx]['descriptions'].append("")
                    st.rerun()
                
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
                    edu['specialization'] = st.text_input("Specialization/Field of Study:", value=edu.get('specialization', ''), key=f"edu_spec_{edu_idx}")
                    edu['institution'] = st.text_input("Institution:", value=edu.get('institution', ''), key=f"edu_inst_{edu_idx}")
                with col2:
                    edu['graduation'] = st.text_input("Graduation:", value=edu.get('graduation', ''), key=f"edu_grad_{edu_idx}")
                    edu['location'] = st.text_input("Location:", value=edu.get('location', ''), key=f"edu_loc_{edu_idx}")
    
    # Save button
    if st.button("💾 Save Changes to DB", type="primary"):
        # st.session_state.resume_data = resume_data
        try:
            save_resume_to_db(st.session_state.resume_data)
            st.success("✅ All changes saved to session and database!")
        except Exception as e:
            st.error(f"Session saved, but database save failed: {str(e)}")
        st.rerun()
    
    st.info("👉 Next Steps: Go to 'Job Matching' → Complete company analysis → Use 'Edit Resume Sections' for AI suggestions")

def job_matching_page():
    st.header("🎯 Enhanced Job Matching")
    
    if not st.session_state.resume_data:
        st.warning("Please upload and parse a resume first!")
        return
    
    st.markdown("**New Enhanced Workflow:** AI Enhances → You Review → AI Selects Best Match")
    
    # Initialize workflow state
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'enhanced_content' not in st.session_state:
        st.session_state.enhanced_content = None
    
    # Progress indicator
    col1, col2, col3 = st.columns(3)
    with col1:
        status1 = "✅" if st.session_state.workflow_step > 1 else "🔄" if st.session_state.workflow_step == 1 else "⏳"
        st.write(f"{status1} **Step 1:** AI Enhance Content")
    with col2:
        status2 = "✅" if st.session_state.workflow_step > 2 else "🔄" if st.session_state.workflow_step == 2 else "⏳"
        st.write(f"{status2} **Step 2:** Review & Edit")
    with col3:
        status3 = "✅" if st.session_state.workflow_step > 3 else "🔄" if st.session_state.workflow_step == 3 else "⏳"
        st.write(f"{status3} **Step 3:** AI Select Best")
    
    st.divider()
    
    # Step-specific content
    if st.session_state.workflow_step == 1:
        _render_step1_enhance_content()
    elif st.session_state.workflow_step == 2:
        _render_step2_review_enhancements()
    elif st.session_state.workflow_step == 3:
        _render_step3_generate_matched_resume()
    

def edit_markdown_page():
    st.header("📝 Edit Resume Sections (AI-Enhanced)")
    
    if not st.session_state.resume_data:
        st.warning("Please upload and parse a resume first!")
        return
    
    st.markdown("*Edit each section with AI positioning suggestions - final resume updates automatically*")
    
    # Determine which data source to use for editing
    if st.session_state.selected_content:
        st.info("📊 **Editing Matched Resume Content** - AI-selected content for your target job")
        st.session_state.current_editing_data = st.session_state.selected_content
    else:
        st.info("📋 **Editing Original Resume Data** - Complete resume content")  
        st.session_state.current_editing_data = st.session_state.resume_data
    
    # Section-based editing
    _render_contact_section()
    _render_summary_section()
    _render_experience_section()
    _render_projects_section() 
    _render_skills_section()
    _render_education_section()
    
    # Auto-generate final markdown
    st.divider()
    st.subheader("📄 Live Resume Preview")
    
    # Generate markdown from current sections
    final_markdown = _generate_markdown_from_sections()
    st.session_state.final_markdown = final_markdown
    
    # Show preview
    with st.expander("👀 Preview Final Resume", expanded=True):
        st.markdown(final_markdown)
    

def _generate_custom_filename():
    """Generate custom PDF filename: {Name}_{Company}_{Role}.pdf"""
    import re
    
    # Get candidate name
    name = st.session_state.resume_data.get('contact', {}).get('name', 'Resume')
    
    # Get company and role from session state (if available from job matching)
    company = st.session_state.get('target_company', 'Company')
    role = st.session_state.get('target_job_title', 'Role')
    
    # Clean up the strings for filename (remove special characters)
    def clean_for_filename(text):
        # Replace spaces with underscores and remove special characters
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')
    
    clean_name = clean_for_filename(name)
    clean_company = clean_for_filename(company)
    clean_role = clean_for_filename(role)
    
    return f"{clean_name}_{clean_company}_{clean_role}.pdf"

def export_pdf_page():
    
    if not st.session_state.selected_content:
        st.warning("Please create a job matched resume first!")
        return
    

    if st.session_state.selected_content:
        st.info("📊 **Using Matched Resume Content** - AI-selected content for your pdf")
    else:
        st.info("📋 **Using Original Resume Data** - Complete parsed resume")
    
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

        # Generate PDF button
        if st.button("📄 Generate PDF", type="primary"):
            with st.spinner(f"Generating PDF with {selected_display}..."):
                try:
                    # # Use final markdown if available, otherwise selected content or resume data
                    # if st.session_state.final_markdown:
                    #     # Convert markdown back to resume data structure for theme export
                    #     resume_data = st.session_state.resume_data  # Use original structure
                    #     # Note: For now using resume data structure - could enhance to parse markdown
                    # else:
                    #     resume_data = st.session_state.selected_content or st.session_state.resume_data
                    resume_data = st.session_state.selected_content or st.session_state.resume_data
                    
                    pdf_bytes = theme_exporter.export_resume(
                        resume_data,
                        selected_engine,
                        selected_theme,
                        'pdf'
                    )
                    
                    # Generate custom filename
                    filename = _generate_custom_filename()
                    
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
    
    except Exception as e:
        st.error(f"Theme system error: {str(e)}")
        st.info("Falling back to basic export...")
        
        # Fallback message
        st.warning("Theme system is temporarily unavailable. Please check your resume data and try again.")

def _generate_initial_markdown_sections():
    """Generate initial markdown sections from resume data"""
    if not st.session_state.resume_data:
        return {}
    
    return {
        'contact': _generate_contact_markdown(),
        'summary': _generate_summary_markdown(), 
        'experience': _generate_experience_markdown(),
        'projects': _generate_projects_markdown(),
        'skills': _generate_skills_markdown(),
        'education': _generate_education_markdown()
    }

def _generate_contact_markdown():
    """Generate contact section markdown"""
    contact = st.session_state.current_editing_data.get('contact', {})
    
    markdown = ""
    if contact.get('name'):
        markdown += f"# {contact['name']}\n\n"
    
    if contact.get('title'):
        markdown += f"**{contact['title']}**\n\n"
    
    contact_info = []
    if contact.get('email'): contact_info.append(contact['email'])
    if contact.get('phone'): contact_info.append(contact['phone'])
    if contact.get('location'): contact_info.append(contact['location'])
    if contact.get('linkedin'): contact_info.append(contact['linkedin'])
    if contact.get('github'): contact_info.append(contact['github'])
    if contact.get('website'): contact_info.append(contact['website'])
    
    if contact_info:
        markdown += " | ".join(contact_info) + "\n\n"
    
    return markdown

def _generate_summary_markdown():
    """Generate summary section markdown"""
    summary = st.session_state.current_editing_data.get('summary', {})
    sentences = summary.get('sentences', [])
    
    if sentences:
        return "## Summary\n\n" + " ".join(sentences) + "\n\n"
    return ""

def _generate_experience_markdown():
    """Generate experience section markdown"""
    experiences = st.session_state.current_editing_data.get('experience', [])
    
    if not experiences:
        return ""
    
    markdown = "## Experience\n\n"
    
    for exp in experiences:
        # Title and company
        markdown += f"### {exp.get('position', 'Position')} - {exp.get('company', 'Company')}\n"
        if exp.get('duration'): 
            markdown += f"*{exp['duration']}*"
        if exp.get('location'):
            markdown += f" | {exp['location']}"
        markdown += "\n\n"
        
        # Role summary
        if exp.get('role_summaries') and exp['role_summaries']:
            markdown += exp['role_summaries'][0] + "\n\n"
        
        # Accomplishments
        if exp.get('accomplishments'):
            for acc in exp['accomplishments']:
                markdown += f"• {acc}\n\n"
            markdown += "\n\n"
    
    return markdown

def _generate_projects_markdown():
    """Generate projects section markdown"""
    projects = st.session_state.current_editing_data.get('projects', [])
    
    if not projects:
        return ""
    
    markdown = "## Projects\n\n"
    
    for proj in projects:
        project_header = proj.get('name', 'Project Name')
        if proj.get('url'):
            project_header = f"[{project_header}]({proj['url']})"
        markdown += f"### {project_header}\n"
        
        if proj.get('descriptions') and proj['descriptions']:
            markdown += proj['descriptions'][0] + "\n\n"
        
        if proj.get('technologies'):
            markdown += f"**Technologies:** {', '.join(proj['technologies'])}\n\n"
    
    return markdown

def _generate_skills_markdown():
    """Generate skills section markdown"""
    skills = st.session_state.current_editing_data.get('skills', {})
    
    if not skills:
        return ""
    
    markdown = "## Skills\n\n"
    
    for category, skill_list in skills.items():
        if skill_list:
            category_name = category.replace('_', ' ').title()
            markdown += f"**{category_name}:** {', '.join(skill_list)}\n\n"
    
    return markdown

def _generate_education_markdown():
    """Generate education section markdown"""
    education = st.session_state.current_editing_data.get('education', [])
    
    if not education:
        return ""
    
    markdown = "## Education\n\n"
    
    for edu in education:
        degree_text = edu.get('degree', 'Degree')
        if edu.get('specialization'):
            degree_text += f" in {edu['specialization']}"
        markdown += f"### {degree_text} - {edu.get('institution', 'Institution')}\n"
        if edu.get('graduation'):
            markdown += f"*{edu['graduation']}*"
        if edu.get('location'):
            markdown += f" | {edu['location']}"
        markdown += "\n\n"
    
    return markdown

def _render_contact_section():
    """Render contact section with suggestions"""
    with st.container():
        st.subheader("👤 Contact Information")
        
        contact = st.session_state.current_editing_data.get('contact', {})
        
        # Edit contact info
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name:", value=contact.get('name', ''), key="md_name")
            title = st.text_input("Title:", value=contact.get('title', ''), key="md_title")
            email = st.text_input("Email:", value=contact.get('email', ''), key="md_email")
            phone = st.text_input("Phone:", value=contact.get('phone', ''), key="md_phone")
        with col2:
            location = st.text_input("Location:", value=contact.get('location', ''), key="md_location")
            linkedin = st.text_input("LinkedIn:", value=contact.get('linkedin', ''), key="md_linkedin")
            github = st.text_input("GitHub:", value=contact.get('github', ''), key="md_github")
            website = st.text_input("Website:", value=contact.get('website', ''), key="md_website")
        
        # Update contact in editing data with ALL fields
        st.session_state.current_editing_data['contact'] = {
            'name': name, 'title': title, 'email': email, 'phone': phone, 
            'location': location, 'linkedin': linkedin, 'github': github, 'website': website
        }

def _render_summary_section():
    """Render summary section with AI suggestions"""
    
    # Check for suggestions
    has_suggestions = False
    summary_suggestions = []
    
    # Section header with indicator
    section_header = "📝 Summary"
    if has_suggestions:
        section_header += " ✨"
    
    with st.container():
        st.subheader(section_header)
        
        sentences = st.session_state.current_editing_data.get('summary', {}).get('sentences', [])
        
        # Show AI suggestions if available
        if has_suggestions:
            with st.expander("✨ AI Summary Suggestions", expanded=False):
                for i, suggestion in enumerate(summary_suggestions):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.text_area("Original:", suggestion['original'], height=60, disabled=True, key=f"md_sum_orig_{i}")
                    with col2:
                        st.text_area("AI Suggested:", suggestion['repositioned'], height=60, disabled=True, key=f"md_sum_sugg_{i}")
                    with col3:
                        st.write("")  # spacer
                        if st.button("✅ Use This", key=f"md_apply_sum_{i}"):
                            # Replace in sentences
                            for j, sentence in enumerate(sentences):
                                if sentence == suggestion['original']:
                                    st.session_state.current_editing_data['summary']['sentences'][j] = suggestion['repositioned']
                                    st.success(f"✅ Applied suggestion!")
                                    st.rerun()
                    st.caption(suggestion.get('reasoning', ''))
                    st.divider()
        
        # Edit current summary
        current_summary = " ".join(sentences) if sentences else ""
        edited_summary = st.text_area("Summary:", value=current_summary, height=100, key="md_summary_edit")
        
        # Update summary in editing data
        if edited_summary != current_summary:
            # Split back into sentences
            new_sentences = [s.strip() for s in edited_summary.split('.') if s.strip()]
            st.session_state.current_editing_data['summary'] = {'sentences': [s + '.' for s in new_sentences if s]}

def _render_experience_section():
    """Render experience section with AI suggestions"""
    
    # Check for suggestions
    has_suggestions = False
    exp_suggestions_map = {}
    
    section_header = "💼 Experience"
    if has_suggestions:
        section_header += " ✨"
    
    with st.container():
        st.subheader(section_header)
        
        experiences = st.session_state.current_editing_data.get('experience', [])
        
        for exp_idx, exp in enumerate(experiences):
            exp_has_suggestions = exp_idx in exp_suggestions_map
            exp_header = f"{exp.get('position', 'Position')} at {exp.get('company', 'Company')}"
            if exp_has_suggestions:
                exp_header += " ✨"
            
            with st.expander(exp_header, expanded=exp_has_suggestions):
                
                # Show suggestions for this experience
                if exp_has_suggestions:
                    st.info("💡 AI found positioning improvements for this role")
                    suggestions = exp_suggestions_map[exp_idx]
                    
                    for i, suggestion in enumerate(suggestions):
                        st.write(f"**Suggestion {i+1}:**")
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.text_area("Original:", suggestion['original'], height=80, disabled=True, key=f"md_exp_orig_{exp_idx}_{i}")
                        with col2:
                            st.text_area("AI Enhanced:", suggestion['repositioned'], height=80, disabled=True, key=f"md_exp_sugg_{exp_idx}_{i}")
                        with col3:
                            st.write("")  # spacer
                            if st.button("✅ Use This", key=f"md_apply_exp_{exp_idx}_{i}"):
                                # Apply suggestion
                                _apply_experience_suggestion(exp_idx, suggestion)
                                st.success("✅ Applied!")
                                st.rerun()
                        st.caption(suggestion.get('reasoning', ''))
                        st.divider()
                
                # Regular editing
                st.text_input("Position:", value=exp.get('position', ''), key=f"md_exp_pos_{exp_idx}")
                st.text_input("Company:", value=exp.get('company', ''), key=f"md_exp_comp_{exp_idx}")
                
                # Edit accomplishments
                accomplishments = exp.get('accomplishments', [])
                for acc_idx, acc in enumerate(accomplishments):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        new_acc = st.text_area(f"Accomplishment {acc_idx+1}:", value=acc, height=60, key=f"md_exp_acc_{exp_idx}_{acc_idx}")
                        if new_acc != acc:
                            st.session_state.current_editing_data['experience'][exp_idx]['accomplishments'][acc_idx] = new_acc
                    with col2:
                        st.write("")  # spacer
                        if st.button("🗑️", key=f"md_delete_accomplishment_{exp_idx}_{acc_idx}", help="Delete this accomplishment"):
                            # Remove the accomplishment and refresh
                            st.session_state.current_editing_data['experience'][exp_idx]['accomplishments'].pop(acc_idx)
                            st.rerun()

def _apply_experience_suggestion(exp_idx: int, suggestion: dict):
    """Apply an experience suggestion to the editing data"""
    exp = st.session_state.current_editing_data['experience'][exp_idx]
    
    # Find and replace in accomplishments
    if 'accomplishments' in exp:
        for i, acc in enumerate(exp['accomplishments']):
            if acc == suggestion['original']:
                st.session_state.current_editing_data['experience'][exp_idx]['accomplishments'][i] = suggestion['repositioned']
                return
    
    # Find and replace in role summaries
    if 'role_summaries' in exp:
        for i, role in enumerate(exp['role_summaries']):
            if role == suggestion['original']:
                st.session_state.current_editing_data['experience'][exp_idx]['role_summaries'][i] = suggestion['repositioned']
                return

def _render_projects_section():
    """Render projects section"""
    with st.container():
        st.subheader("🚀 Projects")
        
        projects = st.session_state.current_editing_data.get('projects', [])
        
        for proj_idx, proj in enumerate(projects):
            with st.expander(f"Project: {proj.get('name', 'Unnamed')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Project Name:", value=proj.get('name', ''), key=f"md_proj_name_{proj_idx}")
                with col2:
                    st.text_input("Project URL:", value=proj.get('url', ''), key=f"md_proj_url_{proj_idx}")
                
                descriptions = proj.get('descriptions', [])
                for desc_idx, desc in enumerate(descriptions):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        new_desc = st.text_area(f"Description {desc_idx+1}:", value=desc, height=60, key=f"md_proj_desc_{proj_idx}_{desc_idx}")
                        if new_desc != desc:
                            st.session_state.current_editing_data['projects'][proj_idx]['descriptions'][desc_idx] = new_desc
                    with col2:
                        st.write("")  # spacer
                        if st.button("🗑️", key=f"md_delete_proj_desc_{proj_idx}_{desc_idx}", help="Delete this description"):
                            # Remove the project description and refresh
                            st.session_state.current_editing_data['projects'][proj_idx]['descriptions'].pop(desc_idx)
                            st.rerun()

def _render_skills_section():
    """Render skills section"""
    with st.container():
        st.subheader("🛠️ Skills")
        
        skills = st.session_state.current_editing_data.get('skills', {})
        
        for category, skill_list in skills.items():
            if skill_list:
                category_name = category.replace('_', ' ').title()
                current_skills = ', '.join(skill_list)
                new_skills = st.text_input(f"{category_name}:", value=current_skills, key=f"md_skills_{category}")
                if new_skills != current_skills:
                    st.session_state.current_editing_data['skills'][category] = [s.strip() for s in new_skills.split(',') if s.strip()]

def _render_education_section():
    """Render education section"""
    with st.container():
        st.subheader("🎓 Education")
        
        education = st.session_state.current_editing_data.get('education', [])
        
        for edu_idx, edu in enumerate(education):
            with st.expander(f"Education: {edu.get('degree', 'Degree')}", expanded=False):
                st.text_input("Degree:", value=edu.get('degree', ''), key=f"md_edu_deg_{edu_idx}")
                st.text_input("Specialization:", value=edu.get('specialization', ''), key=f"md_edu_spec_{edu_idx}")
                st.text_input("Institution:", value=edu.get('institution', ''), key=f"md_edu_inst_{edu_idx}")

def _generate_markdown_from_sections():
    """Generate complete markdown from current editing data"""
    markdown = ""
    
    # Contact
    markdown += _generate_contact_markdown()
    
    # Summary  
    markdown += _generate_summary_markdown()
    
    # Experience
    markdown += _generate_experience_markdown()
    
    # Projects
    markdown += _generate_projects_markdown()
    
    # Skills
    markdown += _generate_skills_markdown()
    
    # Education
    markdown += _generate_education_markdown()
    
    return markdown

def _render_step1_enhance_content():
    """Step 1: AI enhances all resume content"""
    st.subheader("🔧 Step 1: AI Content Enhancement")
    st.markdown("*AI will improve the language and impact of all your resume content*")
    
    # Job info input for context
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name:", placeholder="e.g., Google, Stripe, Microsoft", key="step1_company")
    with col2:
        job_title = st.text_input("Job Title/Designation:", placeholder="e.g., Software Engineer, Data Scientist", key="step1_job_title")
    
    job_description = st.text_area("Job Description:", placeholder="Paste the job posting here...", height=150, key="step1_job_desc")
    
    if company_name.strip() and job_title.strip() and job_description.strip():
        if st.button("🚀 Enhance All Content", type="primary"):
            # Create progress tracking containers
            progress_container = st.container()
            progress_bar = progress_container.progress(0)
            status_text = progress_container.empty()
            logs_container = progress_container.empty()
            
            try:
                logs = []
                
                # Store job info for later steps
                st.session_state.target_company = company_name
                st.session_state.target_job_title = job_title
                st.session_state.target_job_description = job_description
                
                status_text.text("🏢 Analyzing company DNA...")
                progress_bar.progress(10)
                logs.append("🏢 Starting company analysis...")
                
                # Enhance all content using positioning coach
                positioning_coach = PositioningCoach()
                
                # Get company analysis
                company_analysis = positioning_coach.company_analyzer.analyze_company_dna(job_description, company_name)
                logs.append(f"✅ Company analysis complete: {company_analysis.get('company_type', 'Unknown')} company")
                
                progress_bar.progress(20)
                status_text.text("🔧 Starting content enhancement...")
                
                # Count total items to enhance for accurate progress
                resume_data = st.session_state.resume_data
                total_items = 0
                total_items += len(resume_data.get('summary', {}).get('sentences', []))
                for exp in resume_data.get('experience', []):
                    total_items += len(exp.get('role_summaries', []))
                    total_items += len(exp.get('accomplishments', []))
                for proj in resume_data.get('projects', []):
                    total_items += len(proj.get('descriptions', []))
                
                logs.append(f"📊 Total items to enhance: {total_items}")
                
                # Update logs display
                with logs_container.container():
                    for log in logs:
                        st.text(log)
                
                # Generate enhanced versions of all content
                enhanced_content = _generate_enhanced_content_for_all_sections(
                    st.session_state.resume_data, 
                    job_description, 
                    company_analysis,
                    progress_bar,
                    status_text,
                    logs_container,
                    total_items
                )
                
                # Store enhanced content
                st.session_state.enhanced_content = enhanced_content
                st.session_state.company_analysis = company_analysis
                
                # Move to next step
                st.session_state.workflow_step = 2
                
                progress_bar.progress(100)
                status_text.text("✅ AI enhancement complete!")
                st.success("✅ All content enhanced! Moving to review step...")
                st.rerun()
                    
            except Exception as e:
                st.error(f"Enhancement failed: {str(e)}")
                st.info("You can continue with original content")
    
    else:
        st.info("👆 Enter company name, job title, and job description to start AI enhancement")

def _generate_enhanced_content_for_all_sections(resume_data, job_description, company_analysis, 
                                               progress_bar=None, status_text=None, logs_container=None, total_items=0):
    """Generate enhanced versions of all resume sections with global verb tracking and logging"""
    
    # Global verb tracking across all content
    used_verbs = set()
    logs = []
    current_item = 0
    
    enhanced_content = {
        'summary': {'original': [], 'enhanced': []},
        'experience': [],
        'projects': [],
        'skills': resume_data.get('skills', {})  # Skills don't need enhancement
    }
    
    def update_progress(message, item_completed=False):
        nonlocal current_item
        if item_completed:
            current_item += 1
        
        if progress_bar and total_items > 0:
            progress = 20 + int((current_item / total_items) * 70)  # 20-90% range
            progress_bar.progress(min(progress, 90))
        
        if status_text:
            status_text.text(message)
        
        logs.append(f"{message} (API calls made: {current_item})")
        if logs_container:
            with logs_container.container():
                for log in logs[-10:]:  # Show last 10 logs
                    st.text(log)
    
    # Enhance summary sentences
    if resume_data.get('summary', {}).get('sentences'):
        sentences = resume_data['summary']['sentences']
        enhanced_content['summary']['original'] = sentences.copy()
        
        update_progress(f"🔤 Enhancing {len(sentences)} summary sentences...")
        
        # AI enhance each sentence with verb tracking
        enhanced_sentences = []
        for i, sentence in enumerate(sentences):
            update_progress(f"🔤 Enhancing summary sentence {i+1}/{len(sentences)}")
            enhanced_sentence = _enhance_content_with_verb_tracking(
                sentence, 
                job_description, 
                company_analysis, 
                "summary sentence",
                used_verbs
            )
            enhanced_sentences.append(enhanced_sentence)
            update_progress(f"✅ Summary sentence {i+1} enhanced", item_completed=True)
        
        enhanced_content['summary']['enhanced'] = enhanced_sentences
    
    # Enhance experience entries
    if resume_data.get('experience'):
        update_progress(f"💼 Processing {len(resume_data['experience'])} experience entries...")
        
        for exp_idx, exp in enumerate(resume_data['experience']):
            exp_name = f"{exp.get('position', 'Position')} at {exp.get('company', 'Company')}"
            update_progress(f"💼 Experience {exp_idx+1}: {exp_name}")
            
            enhanced_exp = {
                'experience_index': exp_idx,
                'position': exp.get('position', ''),
                'company': exp.get('company', ''),
                'duration': exp.get('duration', ''),
                'location': exp.get('location', ''),
                'role_summaries': {
                    'original': exp.get('role_summaries', []),
                    'enhanced': []
                },
                'accomplishments': {
                    'original': exp.get('accomplishments', []),
                    'enhanced': []
                }
            }
            
            # Enhance role summaries
            role_summaries = exp.get('role_summaries', [])
            if role_summaries:
                update_progress(f"🔤 Enhancing {len(role_summaries)} role summaries for {exp_name}")
                for i, role_summary in enumerate(role_summaries):
                    update_progress(f"🔤 Role summary {i+1}/{len(role_summaries)} for {exp_name}")
                    enhanced_role = _enhance_content_with_verb_tracking(
                        role_summary,
                        job_description,
                        company_analysis,
                        "role summary",
                        used_verbs
                    )
                    enhanced_exp['role_summaries']['enhanced'].append(enhanced_role)
                    update_progress(f"✅ Role summary {i+1} enhanced for {exp_name}", item_completed=True)
            
            # Enhance accomplishments
            accomplishments = exp.get('accomplishments', [])
            if accomplishments:
                update_progress(f"🎯 Enhancing {len(accomplishments)} accomplishments for {exp_name}")
                for i, accomplishment in enumerate(accomplishments):
                    update_progress(f"🎯 Accomplishment {i+1}/{len(accomplishments)} for {exp_name}")
                    enhanced_acc = _enhance_content_with_verb_tracking(
                        accomplishment,
                        job_description,
                        company_analysis,
                        "accomplishment",
                        used_verbs
                    )
                    enhanced_exp['accomplishments']['enhanced'].append(enhanced_acc)
                    update_progress(f"✅ Accomplishment {i+1} enhanced for {exp_name}", item_completed=True)
            
            if not role_summaries and not accomplishments:
                update_progress(f"⏭️ Skipping {exp_name} (no content to enhance)")
            
            enhanced_content['experience'].append(enhanced_exp)
    
    # Enhance projects
    if resume_data.get('projects'):
        update_progress(f"🚀 Processing {len(resume_data['projects'])} projects...")
        
        for proj_idx, proj in enumerate(resume_data['projects']):
            proj_name = proj.get('name', 'Unnamed Project')
            update_progress(f"🚀 Project {proj_idx+1}: {proj_name}")
            
            enhanced_proj = {
                'project_index': proj_idx,
                'name': proj.get('name', ''),
                'url': proj.get('url', ''),
                'technologies': proj.get('technologies', []),
                'descriptions': {
                    'original': proj.get('descriptions', []),
                    'enhanced': []
                }
            }
            
            # Enhance descriptions
            descriptions = proj.get('descriptions', [])
            if descriptions:
                update_progress(f"🔤 Enhancing {len(descriptions)} descriptions for {proj_name}")
                for i, description in enumerate(descriptions):
                    update_progress(f"🔤 Description {i+1}/{len(descriptions)} for {proj_name}")
                    enhanced_desc = _enhance_content_with_verb_tracking(
                        description,
                        job_description,
                        company_analysis,
                        "project description",
                        used_verbs
                    )
                    enhanced_proj['descriptions']['enhanced'].append(enhanced_desc)
                    update_progress(f"✅ Project description {i+1} enhanced for {proj_name}", item_completed=True)
            else:
                update_progress(f"⏭️ Skipping {proj_name} (no descriptions to enhance)")
            
            enhanced_content['projects'].append(enhanced_proj)
    
    update_progress("🎉 All content enhancement completed!")
    return enhanced_content

def _enhance_single_content(content, job_description, company_analysis, content_type):
    """Use AI to enhance a single piece of content (legacy function)"""
    
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        company_type = company_analysis.get('company_type', 'tech')
        top_values = company_analysis.get('top_values', [])
        
        prompt = f"""
        Enhance this resume {content_type} for a {company_type} company.
        
        Original: "{content}"
        
        Company values: {', '.join(top_values)}
        
        Instructions:
        - Keep the same core facts and achievements
        - Improve language for impact and clarity
        - Use terminology that resonates with {company_type} companies
        - Make it more compelling while staying truthful
        - Keep it concise but impactful
        
        Return only the enhanced version, no explanation.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Enhancement failed for {content_type}: {e}")
        return content  # Return original if enhancement fails

def _enhance_content_with_verb_tracking(content, job_description, company_analysis, content_type, used_verbs):
    """Use AI to enhance content while tracking and avoiding repeated action verbs"""
    
    try:
        import json
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        company_type = company_analysis.get('company_type', 'tech')
        top_values = company_analysis.get('top_values', [])
        
        # Convert set to list for JSON serialization
        used_verbs_list = list(used_verbs) if used_verbs else []
        
        prompt = f"""
        Enhance this resume {content_type} for a {company_type} company.
        
        Original: "{content}"
        
        Company values: {', '.join(top_values)}
        
        CRITICAL: Avoid starting with these already used action verbs: {', '.join(used_verbs_list)}
        
        Instructions:
        - Keep the same core facts and achievements
        - Use a DIFFERENT action verb than the ones listed above
        - Improve language for impact and clarity
        - Use terminology that resonates with {company_type} companies
        - Make it more compelling while staying truthful
        - Keep it concise but impactful
        
        Return a JSON response with this exact format:
        {{
            "enhanced_content": "your enhanced text here",
            "action_verb_used": "the main action verb you started with"
        }}
        
        Return only valid JSON, no explanation or markdown formatting.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,  # Slightly higher for more variety
            max_tokens=300
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up any markdown formatting
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        try:
            # Parse JSON response
            result = json.loads(response_text)
            enhanced_content = result.get('enhanced_content', content)
            action_verb = result.get('action_verb_used', '')
            
            # Add the verb to used_verbs set
            if action_verb:
                used_verbs.add(action_verb.lower())
                
            return enhanced_content
            
        except json.JSONDecodeError:
            print(f"JSON parsing failed for {content_type}. Response: {response_text[:100]}...")
            
            # Fallback: try to extract enhanced content from response
            # Look for quotes or return the whole response if it looks like enhanced content
            if '"' in response_text and 'enhanced_content' in response_text:
                # Try to extract from malformed JSON
                try:
                    start = response_text.find('"enhanced_content":') + len('"enhanced_content":')
                    content_part = response_text[start:].strip()
                    if content_part.startswith('"'):
                        end = content_part.find('",', 1)
                        if end == -1:
                            end = content_part.find('"', 1)
                        if end > 0:
                            fallback_content = content_part[1:end]
                            # Try to extract verb too
                            first_word = fallback_content.split()[0].rstrip('.,;:').lower()
                            used_verbs.add(first_word)
                            return fallback_content
                except:
                    pass
            
            # Final fallback: use original enhancement function
            print(f"Using fallback enhancement for {content_type}")
            enhanced = _enhance_single_content(content, job_description, company_analysis, content_type)
            
            # Try to extract first word as verb
            try:
                words = enhanced.split()
                if words:
                    first_word = words[0].rstrip('.,;:').lower()
                    used_verbs.add(first_word)
            except:
                pass
                
            return enhanced
        
    except Exception as e:
        print(f"Verb tracking enhancement failed for {content_type}: {e}")
        print(f"Content was: {content[:100]}...")  # Show first 100 chars for debugging
        
        # Try fallback enhancement
        try:
            fallback_result = _enhance_single_content(content, job_description, company_analysis, content_type)
            print(f"Fallback enhancement succeeded for {content_type}")
            return fallback_result
        except Exception as fallback_error:
            print(f"Fallback enhancement also failed for {content_type}: {fallback_error}")
            print(f"Returning original content for {content_type}")
            return content  # Return original if all fails


def _render_step2_review_enhancements():
    """Step 2: User reviews and edits enhanced content"""
    st.subheader("✂️ Step 2: Review & Edit Enhanced Content")
    st.markdown("*Review AI enhancements and edit them to your liking. Only approved content will be available for final selection.*")
    
    if not st.session_state.enhanced_content:
        st.error("No enhanced content available. Please complete Step 1 first.")
        if st.button("← Back to Step 1"):
            st.session_state.workflow_step = 1
            st.rerun()
        return
    
    enhanced_content = st.session_state.enhanced_content
    
    # Review Summary
    if enhanced_content.get('summary', {}).get('enhanced'):
        st.subheader("📝 Summary Sentences")
        
        original_sentences = enhanced_content['summary']['original']
        enhanced_sentences = enhanced_content['summary']['enhanced']
        
        approved_sentences = []
        
        for i, (original, enhanced) in enumerate(zip(original_sentences, enhanced_sentences)):
            with st.expander(f"Summary Sentence {i+1}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.text_area("Original:", original, height=60, disabled=True, key=f"review_sum_orig_{i}")
                
                with col2:
                    edited_enhanced = st.text_area("Enhanced (Editable):", enhanced, height=60, key=f"review_sum_enh_{i}")
                
                with col3:
                    use_original = st.checkbox("Use Original", key=f"review_sum_use_orig_{i}")
                    use_enhanced = st.checkbox("Use Enhanced", value=True, key=f"review_sum_use_enh_{i}")
                
                # Collect approved content
                if use_original:
                    approved_sentences.append(original)
                if use_enhanced:
                    approved_sentences.append(edited_enhanced)
        
        # Store approved sentences
        if 'approved_content' not in st.session_state:
            st.session_state.approved_content = {}
        st.session_state.approved_content['summary_sentences'] = approved_sentences
    
    # Review Experience
    if enhanced_content.get('experience'):
        st.subheader("💼 Experience")
        
        for exp_idx, enhanced_exp in enumerate(enhanced_content['experience']):
            with st.expander(f"{enhanced_exp['position']} at {enhanced_exp['company']}", expanded=False):
                
                # Initialize arrays for this specific experience entry
                approved_role_summaries = []
                approved_accomplishments = []
                
                # Role summaries
                if enhanced_exp['role_summaries']['enhanced']:
                    st.write("**Role Summaries:**")
                    
                    for i, (original, enhanced) in enumerate(zip(
                        enhanced_exp['role_summaries']['original'],
                        enhanced_exp['role_summaries']['enhanced']
                    )):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.text_area("Original:", original, height=50, disabled=True, key=f"review_role_orig_{exp_idx}_{i}")
                        
                        with col2:
                            edited_role = st.text_area("Enhanced:", enhanced, height=50, key=f"review_role_enh_{exp_idx}_{i}")
                        
                        with col3:
                            use_orig_role = st.checkbox("Use Orig", key=f"review_role_use_orig_{exp_idx}_{i}")
                            use_enh_role = st.checkbox("Use Enh", value=True, key=f"review_role_use_enh_{exp_idx}_{i}")
                        
                        if use_orig_role:
                            approved_role_summaries.append(original)
                        if use_enh_role:
                            approved_role_summaries.append(edited_role)
                
                # Accomplishments
                if enhanced_exp['accomplishments']['enhanced']:
                    st.write("**Accomplishments:**")
                    
                    for i, (original, enhanced) in enumerate(zip(
                        enhanced_exp['accomplishments']['original'],
                        enhanced_exp['accomplishments']['enhanced']
                    )):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.text_area("Original:", original, height=60, disabled=True, key=f"review_acc_orig_{exp_idx}_{i}")
                        
                        with col2:
                            edited_acc = st.text_area("Enhanced:", enhanced, height=60, key=f"review_acc_enh_{exp_idx}_{i}")
                        
                        with col3:
                            use_orig_acc = st.checkbox("Use Orig", key=f"review_acc_use_orig_{exp_idx}_{i}")
                            use_enh_acc = st.checkbox("Use Enh", value=True, key=f"review_acc_use_enh_{exp_idx}_{i}")
                        
                        if use_orig_acc:
                            approved_accomplishments.append(original)
                        if use_enh_acc:
                            approved_accomplishments.append(edited_acc)
                
                # Store approved experience content for this specific experience entry
                if 'approved_content' not in st.session_state:
                    st.session_state.approved_content = {}
                if 'experience' not in st.session_state.approved_content:
                    st.session_state.approved_content['experience'] = {}
                
                # Always use the properly scoped variables (no more locals() check needed)
                st.session_state.approved_content['experience'][exp_idx] = {
                    'role_summaries': approved_role_summaries,
                    'accomplishments': approved_accomplishments
                }
    
    # Review Projects
    if enhanced_content.get('projects'):
        st.subheader("🚀 Projects")
        
        for proj_idx, enhanced_proj in enumerate(enhanced_content['projects']):
            with st.expander(f"Project: {enhanced_proj['name']}", expanded=False):
                
                # Initialize array for this specific project entry
                approved_project_descriptions = []
                
                if enhanced_proj['descriptions']['enhanced']:
                    st.write("**Project Descriptions:**")
                    
                    for i, (original, enhanced) in enumerate(zip(
                        enhanced_proj['descriptions']['original'],
                        enhanced_proj['descriptions']['enhanced']
                    )):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.text_area("Original:", original, height=60, disabled=True, key=f"review_proj_orig_{proj_idx}_{i}")
                        
                        with col2:
                            edited_proj = st.text_area("Enhanced:", enhanced, height=60, key=f"review_proj_enh_{proj_idx}_{i}")
                        
                        with col3:
                            use_orig_proj = st.checkbox("Use Orig", key=f"review_proj_use_orig_{proj_idx}_{i}")
                            use_enh_proj = st.checkbox("Use Enh", value=True, key=f"review_proj_use_enh_{proj_idx}_{i}")
                        
                        if use_orig_proj:
                            approved_project_descriptions.append(original)
                        if use_enh_proj:
                            approved_project_descriptions.append(edited_proj)
                
                # Store approved project content for this specific project entry
                if 'projects' not in st.session_state.approved_content:
                    st.session_state.approved_content['projects'] = {}
                
                # Always use the properly scoped variable (no more locals() check needed)
                st.session_state.approved_content['projects'][proj_idx] = {
                    'name': enhanced_proj['name'],
                    'descriptions': approved_project_descriptions
                }
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Step 1"):
            st.session_state.workflow_step = 1
            st.rerun()
    
    with col2:
        if st.button("Continue to Step 3 →", type="primary"):
            st.session_state.workflow_step = 3
            st.success("✅ Enhanced content approved! Moving to AI selection...")
            st.rerun()

def _render_step3_generate_matched_resume():
    """Step 3: AI selects best content mix for target job"""
    st.subheader("🎯 Step 3: AI Selection from Enhanced Content")
    st.markdown("*AI will now select the best combination of your approved enhanced content for this specific job.*")
    
    if not st.session_state.get('approved_content'):
        st.error("No approved content available. Please complete Step 2 first.")
        if st.button("← Back to Step 2"):
            st.session_state.workflow_step = 2
            st.rerun()
        return
    
    # Show what's being selected from
    approved = st.session_state.approved_content
    
    st.info(f"**Selection Pool:** {len(approved.get('summary_sentences', []))} summary sentences, "
           f"{sum(len(exp.get('accomplishments', [])) for exp in approved.get('experience', {}).values())} accomplishments, "
           f"{sum(len(proj.get('descriptions', [])) for proj in approved.get('projects', {}).values())} project descriptions")
    
    if st.button("🎯 Generate Best Match Resume", type="primary"):
        with st.spinner("AI is selecting the optimal content mix..."):
            try:
                # Use the original matcher but with enhanced content pool
                matcher = JobMatcher()
                
                # Create a temporary resume data structure with approved enhanced content
                enhanced_resume_data = _create_enhanced_resume_data_structure()
                
                # Generate matched content
                selected_content = matcher.match_resume_to_job(
                    enhanced_resume_data,
                    st.session_state.target_job_description
                )
                
                st.session_state.selected_content = selected_content
                
                # Generate markdown
                final_markdown = matcher.generate_markdown(selected_content)
                st.session_state.final_markdown = final_markdown
                
                st.success("✅ Best match resume generated!")
                
                # Show results
                with st.expander("🎯 AI Selected Content", expanded=True):
                    # Display selected content
                    if selected_content.get('summary'):
                        st.write("**Selected Summary Sentences:**")
                        for sentence in selected_content['summary'].get('sentences', []):
                            st.write(f"• {sentence}")
                    
                    if selected_content.get('experience'):
                        st.write("**Selected Experience:**")
                        for exp in selected_content['experience']:
                            st.write(f"**{exp.get('position')} at {exp.get('company')}**")
                            if exp.get('accomplishments'):
                                for acc in exp['accomplishments']:  # Show first 3
                                    st.write(f"  • {acc}")
                    
                    if selected_content.get('projects'):
                        st.write("**Selected Projects:**")
                        for proj in selected_content['projects']:
                            st.write(f"**{proj.get('name')}**")
                            if proj.get('descriptions'):
                                for desc in proj['descriptions']:  # Show first 2
                                    st.write(f"  • {desc}")
                
                # Reset workflow for next use
                if st.button("🔄 Start New Matching Process"):
                    st.session_state.workflow_step = 1
                    st.session_state.enhanced_content = None
                    st.session_state.approved_content = None
                    st.rerun()
                
            except Exception as e:
                st.error(f"Content selection failed: {str(e)}")
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Step 2"):
            st.session_state.workflow_step = 2
            st.rerun()
    
    with col2:
        st.info("👉 Go to 'Edit Resume Sections' to make final adjustments")

def _create_enhanced_resume_data_structure():
    """Create resume data structure from approved enhanced content while preserving manual edits"""
    
    # CRITICAL: Use the latest manually edited data, not the original parsed data
    enhanced_data = st.session_state.resume_data.copy()  # This includes manual edits like GitHub, website
    approved = st.session_state.approved_content
    
    # Only replace AI-enhanced sections, preserve everything else (contact, skills, education, etc.)
    if approved.get('summary_sentences'):
        # Preserve existing summary structure, only replace sentences
        if 'summary' not in enhanced_data:
            enhanced_data['summary'] = {}
        enhanced_data['summary']['sentences'] = approved['summary_sentences']
    
    if approved.get('experience'):
        for exp_idx, approved_exp in approved['experience'].items():
            if exp_idx < len(enhanced_data.get('experience', [])):
                # Only replace AI-enhanced fields, preserve company, position, dates, etc.
                if approved_exp.get('role_summaries'):
                    enhanced_data['experience'][exp_idx]['role_summaries'] = approved_exp['role_summaries']
                if approved_exp.get('accomplishments'):
                    enhanced_data['experience'][exp_idx]['accomplishments'] = approved_exp['accomplishments']
    
    if approved.get('projects'):
        for proj_idx, approved_proj in approved['projects'].items():
            if proj_idx < len(enhanced_data.get('projects', [])):
                # Only replace AI-enhanced descriptions, preserve name, url, technologies
                if approved_proj.get('descriptions'):
                    enhanced_data['projects'][proj_idx]['descriptions'] = approved_proj['descriptions']
    
    # Ensure contact info is preserved (this is the key fix!)
    # The copy() should already include this, but let's be explicit for debugging
    contact_fields = ['contact', 'skills', 'education', 'certifications']
    for field in contact_fields:
        if field in st.session_state.resume_data:
            enhanced_data[field] = st.session_state.resume_data[field]
    
    return enhanced_data

if __name__ == "__main__":
    main()