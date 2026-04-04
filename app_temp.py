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
if 'current_profile_id' not in st.session_state:
    st.session_state.current_profile_id = None
if 'current_profile_name' not in st.session_state:
    st.session_state.current_profile_name = None

def main():
    st.set_page_config(
        page_title="Resume Matcher MVP",
        page_icon="📄",
        layout="wide"
    )
    
    # Initialize database
    init_database()
    
    # Sidebar navigation with title and status indicators
    st.sidebar.title("📄 AI Resume Builder")
    st.sidebar.markdown("**Upload → Edit → AI Enhance → Export PDF**")

    # Add workflow overview for new users in sidebar
    _show_workflow_overview()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Quick Start")

    # Get completion status for each step
    status = _get_workflow_status()

    pages = [
        f"{'✅' if status['uploaded'] else '📤'} 1. Upload Resume",
        f"{'✅' if status['edited'] else '✏️'} 2. Edit Sections",
        f"{'✅' if status['enhanced'] else '🤖'} 3. AI Enhancement",
        f"{'✅' if status['reviewed'] else '📝'} 4. Review & Finalize",
        f"📄 Export PDF"
    ]

    # Add cover letter option if profile is loaded
    if st.session_state.resume_data:
        pages.append("💌 Cover Letter")

    page = st.sidebar.radio(
        "Choose a step:",
        pages,
        help="Follow the steps in order for best results, or jump to any step"
    )

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ Missing OpenAI API Key")
        st.info("Please add `OPENAI_API_KEY=your_key_here` to a .env file in the project root")
        st.stop()

    # Page routing
    if "1. Upload Resume" in page:
        upload_resume_page()
    elif "2. Edit Sections" in page:
        edit_sections_page()
    elif "3. AI Enhancement" in page:
        job_matching_page()
    elif "4. Review & Finalize" in page:
        edit_markdown_page()
    elif "Export PDF" in page:
        export_pdf_page()
    elif "Cover Letter" in page:
        cover_letter_page()

def upload_resume_page():
    st.header("📤 Step 1: Upload Resume")
    st.markdown("**Upload your resume (PDF/DOCX) - AI will extract all sections automatically**")
    
    # # Clear explanation of what this page does
    # st.info("""
    # **What you'll do here:**
    
    # 📄 **Upload your resume** - Support for PDF and DOCX formats
    
    # 🤖 **AI parsing** - Automatically extract contact, summary, experience, projects, skills, and education
    
    # 👀 **Or Load a saved profile** - Load a saved profile.

    # """)

    st.markdown("---")
    
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
                    # Clear current profile tracking since this is a new parse
                    st.session_state.current_profile_id = None
                    st.session_state.current_profile_name = None
                    # Reset job matching data since this is a new resume
                    st.session_state.selected_content = None
                    st.session_state.final_markdown = ""
                    
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

    # Load from DB option
    profiles = load_resume_profiles()

    if profiles:
        profile_options = {f"{name} (ID: {pid})": pid for pid, name in profiles}
        selected_profile = st.selectbox("Or load a saved profile:", ["Dont want to load a saved profile"] + list(profile_options.keys()))
        if selected_profile != "Dont want to load a saved profile":
            profile_id = profile_options[selected_profile]
            resume_data = get_resume_by_id(profile_id)
            st.session_state.resume_data = resume_data
            # Track the currently loaded profile
            st.session_state.current_profile_id = profile_id
            st.session_state.current_profile_name = selected_profile
            # Reset job matching data since this is a different profile
            st.session_state.selected_content = None
            st.session_state.final_markdown = ""
            st.success(f"Loaded profile: {selected_profile}")
            st.stop()

def edit_sections_page():
    st.header("✏️ Step 2: Edit Sections")
    st.markdown("**Review and edit your resume content - add details and make corrections**")
    
    if not st.session_state.resume_data:
        _show_prerequisite_warning("Step 1: Upload & Parse Resume", "You need to upload and parse your resume before adding variations")
        return
    
    resume_data = st.session_state.resume_data
    
    # Clear explanation of what to do on this page
    # st.info("""
    # **What you'll do here:**
    
    # ✍️ **Add multiple variations** of your accomplishments, role summaries, and project descriptions
    
    # 📝 **Expand your content** so the AI has more options to choose from when matching to specific jobs
    
    # 💡 **Why?** Different jobs value different aspects of your experience. Having variations lets the AI pick the most relevant ones!
    # """)
    
    st.markdown("---")
    
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
    
    # Save buttons
    col1, col2 = st.columns(2)

    with col1:
        # Determine button text based on whether a profile is loaded
        if st.session_state.current_profile_id:
            button_text = f"💾 Save to '{st.session_state.current_profile_name}'"
            help_text = "Update the currently loaded profile"
        else:
            button_text = "💾 Save Changes to DB"
            help_text = "Save as new profile using contact name"

        if st.button(button_text, type="primary", help=help_text):
            try:
                if st.session_state.current_profile_id:
                    # Save to current profile by ID
                    success = save_resume_to_db(
                        st.session_state.resume_data,
                        profile_id=st.session_state.current_profile_id
                    )
                    if success:
                        st.success(f"✅ Profile '{st.session_state.current_profile_name}' updated!")
                    else:
                        st.error("❌ Failed to update profile. Profile may not exist.")
                else:
                    # Save as new profile using name
                    save_resume_to_db(st.session_state.resume_data)
                    st.success("✅ Changes saved to database!")
            except Exception as e:
                st.error(f"Save failed: {str(e)}")
            st.rerun()

    with col2:
        with st.popover("💾 Save As New Profile", use_container_width=True):
            st.write("**Save as a new profile version**")
            new_profile_name = st.text_input(
                "Profile name:",
                placeholder="e.g., John Doe - Software Engineer v2",
                help="Enter a unique name for this profile version"
            )

            if st.button("Save As New Profile", type="secondary"):
                if new_profile_name.strip():
                    success, result = save_resume_as_new_profile(st.session_state.resume_data, new_profile_name.strip())
                    if success:
                        st.success(f"✅ Profile saved as: {new_profile_name}")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result}")
                else:
                    st.error("Please enter a profile name")
    
    st.info("👉 Next Steps: Go to 'Job Matching' → Complete company analysis → Use 'Edit Resume Sections' for AI suggestions")

def job_matching_page():
    st.header("🤖 Step 3: AI Enhancement")
    st.markdown("**Optimize your resume for a specific job with AI-powered content improvement**")
    
    if not st.session_state.resume_data:
        _show_prerequisite_warning("Step 1: Upload Resume", "You need to upload your resume first")
        return

    st.info("💡 **How it works:** Paste a job description → AI analyzes company culture → AI optimizes your resume content")

    st.markdown("---")

    # Job Context Input
    st.subheader("📋 Job Information")
    st.markdown("*Provide details about the job you're applying for*")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input(
            "Company Name:",
            value=st.session_state.get('target_company_name', ''),
            placeholder="e.g., Google, Stripe, Microsoft",
            help="AI will analyze company culture and optimize your resume accordingly"
        )
        job_title = st.text_input(
            "Job Title:",
            value=st.session_state.get('target_job_title', ''),
            placeholder="e.g., Software Engineer, Data Scientist",
            help="The specific role you're applying for"
        )
    with col2:
        job_description = st.text_area(
            "Job Description:",
            value=st.session_state.get('target_job_description', ''),
            height=150,
            placeholder="Paste the full job description here...",
            help="Include requirements, qualifications, and responsibilities for best AI optimization"
        )

    # Store job context in session state
    if company_name or job_title or job_description:
        st.session_state.target_company_name = company_name
        st.session_state.target_job_title = job_title
        st.session_state.target_job_description = job_description

    st.divider()

    # AI Enhancement Section
    st.subheader("🤖 AI Enhancement")
    st.markdown("*AI will improve your resume content based on the job description above*")

    _render_ai_enhancement_section()


def _render_ai_enhancement_section():
    """Simplified AI enhancement that directly applies changes to resume data"""

    # Use job context from Step 0
    company_name = st.session_state.get('target_company_name', '')
    job_title = st.session_state.get('target_job_title', '')
    job_description = st.session_state.get('target_job_description', '')

    if not (company_name.strip() and job_title.strip() and job_description.strip()):
        st.warning("⚠️ Please provide company name, job title, and job description above first.")
        return

    st.info(f"🎯 **Target:** {job_title} at {company_name}")

    # Show if already enhanced
    if st.session_state.get('content_enhanced'):
        st.success("✅ Content already enhanced for this job!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Re-enhance with Different Settings"):
                st.session_state.content_enhanced = False
                st.rerun()
        with col2:
            if st.button("👀 Preview Enhanced Resume"):
                st.session_state.show_preview = True

        if st.session_state.get('show_preview'):
            with st.expander("📄 Enhanced Resume Preview", expanded=True):
                # Show enhanced summary
                if st.session_state.resume_data.get('summary', {}).get('sentences'):
                    st.write("**Summary:**")
                    st.write(" ".join(st.session_state.resume_data['summary']['sentences']))

                # Show enhanced experience
                if st.session_state.resume_data.get('experience'):
                    st.write("\n**Experience:**")
                    for exp in st.session_state.resume_data['experience'][:2]:
                        st.write(f"**{exp.get('position')} at {exp.get('company')}**")
                        for acc in exp.get('accomplishments', [])[:3]:
                            st.write(f"• {acc}")
        return

    if st.button("🚀 Enhance Resume for This Job", type="primary"):
        # Create progress tracking
        progress_container = st.container()
        progress_bar = progress_container.progress(0)
        status_text = progress_container.empty()

        try:
            # Store job info
            st.session_state.target_company = company_name
            st.session_state.target_job_title = job_title
            st.session_state.target_job_description = job_description

            status_text.text("🏢 Analyzing company DNA...")
            progress_bar.progress(10)

            # Get company analysis
            from positioning_coach import PositioningCoach
            positioning_coach = PositioningCoach()
            company_analysis = positioning_coach.company_analyzer.analyze_company_dna(job_description, company_name)

            progress_bar.progress(20)
            status_text.text("🔧 Enhancing content...")

            # Directly enhance resume_data in place
            _apply_ai_enhancements_directly(
                st.session_state.resume_data,
                job_description,
                company_analysis,
                progress_bar,
                status_text
            )

            progress_bar.progress(100)
            status_text.text("✅ Enhancement complete!")

            st.session_state.content_enhanced = True
            st.session_state.company_analysis = company_analysis
            st.success("✅ Resume enhanced! Go to 'Review & Finalize' to edit or 'Export Resume PDF' to download.")
            st.balloons()

        except Exception as e:
            st.error(f"Enhancement failed: {str(e)}")
            st.info("You can continue with original content")

    else:
        st.info("👆 Click the button above to enhance your resume with AI")


def _apply_ai_enhancements_directly(resume_data, job_description, company_analysis, progress_bar, status_text):
    """Apply AI enhancements directly to resume_data (modifies in place)"""

    # Global verb tracking
    used_verbs = set()

    # Extract keywords
    job_keywords, tech_keywords = _extract_job_keywords_and_tech_terms(job_description)

    # Count items for progress
    total_items = 0
    total_items += len(resume_data.get('summary', {}).get('sentences', []))
    for exp in resume_data.get('experience', []):
        total_items += len(exp.get('role_summaries', []))
        total_items += len(exp.get('accomplishments', []))
    for proj in resume_data.get('projects', []):
        total_items += len(proj.get('descriptions', []))

    current_item = 0

    def update_progress(msg):
        nonlocal current_item
        current_item += 1
        if progress_bar and total_items > 0:
            progress = 20 + int((current_item / total_items) * 70)
            progress_bar.progress(min(progress, 90))
        if status_text:
            status_text.text(msg)

    # Enhance summary
    if resume_data.get('summary', {}).get('sentences'):
        update_progress("🔤 Enhancing summary...")
        sentences = resume_data['summary']['sentences']
        enhanced_sentences, used_verbs = _enhance_content_with_targeted_strategy(
            sentences, job_description, company_analysis, "summary sentence", used_verbs, job_keywords, tech_keywords
        )
        resume_data['summary']['sentences'] = enhanced_sentences

    # Enhance experience
    all_role_summaries = {}
    if resume_data.get('experience'):
        for exp_idx, exp in enumerate(resume_data['experience']):
            # Enhance accomplishments
            if exp.get('accomplishments'):
                update_progress(f"💼 Enhancing {exp.get('position', 'role')}...")
                enhanced_acc, used_verbs = _enhance_content_with_targeted_strategy(
                    exp['accomplishments'], job_description, company_analysis, "accomplishment",
                    used_verbs, job_keywords, tech_keywords
                )
                resume_data['experience'][exp_idx]['accomplishments'] = enhanced_acc

            # Collect role summaries
            if exp.get('role_summaries'):
                all_role_summaries[exp_idx] = exp['role_summaries']

        # Enhance all role summaries together
        if all_role_summaries:
            update_progress("🔤 Enhancing role summaries...")
            enhanced_role_summaries, used_verbs = _enhance_content_with_targeted_strategy(
                all_role_summaries, job_description, company_analysis, "role summary",
                used_verbs, job_keywords, tech_keywords
            )
            # Apply back
            for exp_idx, enhanced_summary in enhanced_role_summaries.items():
                resume_data['experience'][int(exp_idx)]['role_summaries'] = [enhanced_summary]

    # Enhance projects
    if resume_data.get('projects'):
        for proj_idx, proj in enumerate(resume_data['projects']):
            if proj.get('descriptions') and proj['descriptions']:
                update_progress(f"🚀 Enhancing {proj.get('name', 'project')}...")
                enhanced_desc, used_verbs = _enhance_content_with_targeted_strategy(
                    proj['descriptions'][0], job_description, company_analysis, "project description",
                    used_verbs, job_keywords, tech_keywords
                )
                resume_data['projects'][proj_idx]['descriptions'] = [enhanced_desc]


def edit_markdown_page():
    st.header("📝 Step 4: Review & Finalize")
    st.markdown("**Make final edits to your resume sections and preview before export**")
    
    if not st.session_state.resume_data:
        _show_prerequisite_warning("Step 1: Upload & Parse Resume", "You need to upload your resume before reviewing")
        return
    
    # # Clear explanation of what this page does
    # st.info("""
    # **What you'll do here:**
    
    # ✏️ **Review your content** - See either AI-selected content (if you completed job matching) or your full resume
    
    # 🎯 **Get AI suggestions** - Each section shows smart positioning advice for your target job
    
    # 👀 **Live preview** - See exactly how your resume will look as you make changes
    
    # ✅ **Final polish** - Make last-minute adjustments before export
    # """)
    
    st.markdown("---")

    # Show enhancement status
    if st.session_state.get('content_enhanced'):
        st.info("✨ **Editing AI-Enhanced Resume** - Content optimized for your target job")
    else:
        st.info("📋 **Editing Resume Content** - Make changes before or after AI enhancement")

    # Always use resume_data as the single source of truth
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
    st.header("📄 Export Resume PDF")
    st.markdown("**Choose a professional theme and download your resume as PDF**")
    
    if not st.session_state.resume_data:
        _show_prerequisite_warning("Step 1: Upload & Parse Resume", "You need to upload your resume before exporting")
        return
    
    # # Clear explanation of what this page does
    # st.info("""
    # **What you'll do here:**
    
    # 🎨 **Choose a theme** - Select from professional resume templates
    
    # 📄 **Generate PDF** - Create a polished, formatted resume ready for applications
    
    # 💾 **Custom filename** - Downloads as `YourName_Company_Role.pdf` (if job matching was completed)
    
    # ✅ **Ready to apply** - Professional PDF optimized for ATS systems
    # """)
    
    st.markdown("---")

    # Show enhancement status
    if st.session_state.get('content_enhanced'):
        st.success("✨ **Exporting AI-Enhanced Resume** - Optimized for your target job")
    else:
        st.info("📋 **Exporting Resume** - Consider using AI Enhancement for better results")

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
                    # Always use resume_data as single source of truth
                    resume_data = st.session_state.resume_data
                    
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
        
        # Role summaries (all of them, not just the first one)
        if exp.get('role_summaries') and exp['role_summaries']:
            for role_summary in exp['role_summaries']:
                markdown += role_summary + "\n\n"
        
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

                # Edit role summaries
                role_summaries = exp.get('role_summaries', [])
                if role_summaries:
                    st.write("**Role Summaries:**")
                    for rs_idx, role_summary in enumerate(role_summaries):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            new_summary = st.text_area(f"Role Summary {rs_idx+1}:", value=role_summary, height=80, key=f"md_exp_rs_{exp_idx}_{rs_idx}")
                            if new_summary != role_summary:
                                st.session_state.current_editing_data['experience'][exp_idx]['role_summaries'][rs_idx] = new_summary
                        with col2:
                            st.write("")  # spacer
                            if st.button("🗑️", key=f"md_delete_role_summary_{exp_idx}_{rs_idx}", help="Delete this role summary"):
                                # Remove the role summary and refresh
                                st.session_state.current_editing_data['experience'][exp_idx]['role_summaries'].pop(rs_idx)
                                st.rerun()

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

def _enhance_content_with_targeted_strategy(content, job_description, company_analysis, content_type, used_verbs, job_keywords, tech_keywords):
    """Use content-type-specific enhancement strategies for nuanced improvements"""

    # Route to specialized enhancement based on content type
    if content_type == "summary sentence":
        return _enhance_profile_summary(content, job_description, company_analysis, used_verbs)
    elif content_type == "accomplishment":
        return _enhance_role_accomplishment(content, job_description, company_analysis, used_verbs, job_keywords, tech_keywords)
    elif content_type == "role summary":
        return _enhance_role_summary(content, job_description, company_analysis, used_verbs)
    elif content_type == "project description":
        return _enhance_project_description(content, job_description, company_analysis, used_verbs, job_keywords, tech_keywords)
    else:
        # Fallback to general enhancement
        return _enhance_general_content(content, job_description, company_analysis, content_type, used_verbs)

def _enhance_profile_summary(content, job_description, company_analysis, used_verbs):
    """Enhance profile summary focusing on top_values and hidden_preferences"""

    try:
        import json
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        company_type = company_analysis.get('company_type', 'tech')
        top_values = company_analysis.get('top_values', [])
        used_verbs_list = list(used_verbs) if used_verbs else []

        prompt = f"""
        Enhance this profile summary to align with company values and hidden preferences.
        You are given a total of {len(content)} sentences of the original summary. Your job is to create a new summary 
        sentences that better fit with the company culture and hidden preferences.

        Original: "{content}"

        TARGET COMPANY: {company_type}
        KEY VALUES: {', '.join(top_values)}

        VERB TRACKING: Avoid these used verbs: {', '.join(used_verbs_list)}

        PROFILE SUMMARY RULES:
        1. Focus on CULTURAL FIT and VALUES alignment
        2. Highlight personality traits that match company values
        3. Mention years of experience if relevant to company expectations
        4. Keep it conversational and authentic
        5. Avoid technical jargon - focus on mindset and approach
        6. Use diverse, non-repetitive language
        7. Return as many sentences are there are in the orignal summary.
        8. Return a list of action verb you used in the enhancement.

        Return JSON: {{"enhanced_content": ["enhanced sentence 1", "enhanced sentence 2"...], "action_verbs_used": ["verb 1", "verb 2"...]}}
        """

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_tokens=200
        )

        return _parse_enhancement_response(response, content, used_verbs, "list")

    except Exception as e:
        print(f"Profile summary enhancement failed: {e}")
        return content

def _enhance_role_accomplishment(content, job_description, company_analysis, used_verbs, job_keywords, tech_keywords):
    """Enhance role accomplishments focusing on job_keywords and required skills"""

    try:
        import json
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        company_type = company_analysis.get('company_type', 'tech')
        golden_signals = company_analysis.get('golden_signals', [])
        used_verbs_list = list(used_verbs) if used_verbs else []

        prompt = f"""
        You will be a list of accomplishments of a candidate in a role they had.
        Each item in the list is work that they did or thing that they want to highlight about their role.
        They want to leverage your expertise to enhance these accomplishments to better align with the job they are applying for.
        You will be give information about the type of company. What skills and qualities the company values as their golden signals. 

        Your job is to enhance all the accomplishments in one go to avoid same enhancemnents across all accomplishments.
        You have to enhance the accomplishments in such a way that as a whole they are holistic, shows the candidate in best light and reflect the required skills in the accomplishments.

        You are given a total of {len(content)} role summaries to enhance.
        You should not create new role summaries, only enhance the ones given to you with the original key mapping.

        Original: "{content}"

        TARGET ROLE GOLDEN SIGNALS: {golden_signals}
        COMPANY TYPE: {company_type}
        USED VERBS: {', '.join(used_verbs_list)}

        ACCOMPLISHMENT RULES:
        1. QUANTIFY impact with specific metrics where possible
        2. Highlight TECHNICAL SKILLS that match job requirements
        3. Emphasize RESULTS and measurable outcomes
        4. Only use action verbs that haven't been used before to avoid verb repition across sections
        5. Keep focus on what YOU achieved specifically
        6. Match terminology to job posting language
        7. Maximum 1 sentence, powerful and CONCISE! Dont use 1 sentence as an execuse to have long sentences.

        Return JSON: {{"enhanced_content": ["enhanced accomplishment 1", "enhanced accomplishment 2"...], "action_verbs_used": ["verb 1", "verb 2"...]}}
        """

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_tokens=2500
        )

        return _parse_enhancement_response(response, content, used_verbs, type= "list")

    except Exception as e:
        print(f"Accomplishment enhancement failed: {e}, Input = {input}")
        return content

def _enhance_role_summary(content, job_description, company_analysis, used_verbs):
    """Enhance role summaries focusing on golden_signals and positioning_advice"""

    try:
        import json
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        company_type = company_analysis.get('company_type', 'tech')
        # golden_signals = company_analysis.get('golden_signals', [])
        # positioning_advice = company_analysis.get('positioning_advice', {})
        emphasize_points = company_analysis.get('emphasize', [])
        used_verbs_list = list(used_verbs) if used_verbs else []

        expected_output = '{"enhanced_content": {"0": "enhanced summary 1", "1": "enhanced summary 2", ..}, "action_verbs_used": ["verb 1", "verb 2"...]}'

        prompt = f"""
        You will be given a dictionary of role summaries to enhance. 
        Each key in the dictionary corresponds to an experience in the resume and the value is the role summary for that experience.
        You will be given information about the company and the role the candidate is applying for using his resume.

        Your job is to enhance each role summary to better align with the company's golden signals and positioning advice.
        We are doing enhancement of all role summaries in one go to avoid same enhancemnents across all role summaries.
        You have to enhance the summaries in such a way that as a whole they are holistic and shows the candidate in best light.
        Enhance recent roles with more emphasis on golden signals and positioning advice. The recent roles will be the ones with smaller key values.

        You are given a total of {len(content)} role summaries to enhance.
        You should not create new role summaries, only enhance the ones given to you with the original key mapping.

        Original: "{content}"

        EMPHASIZE: {', '.join(emphasize_points)}
        COMPANY TYPE: {company_type}
        USED VERBS: {', '.join(used_verbs_list)}

        ROLE SUMMARY RULES:
        1. Position your RESPONSIBILITIES around what company values
        3. Show SCOPE of work (team size, budget, scale)
        4. Mention METHODOLOGY and APPROACH that aligns with golden signals
        5. Each enhanced role summary should be 1-2 sentences max. 
        6. Focus on HOW you worked, not just what you did
        7. You have to very precise and concise because people have very short attention spans these days.
        8. Use diverse, non-repetitive language

        Return JSON: {expected_output}
        """

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_tokens=500,

        )

        return _parse_enhancement_response(response, content, used_verbs, type= "dict")

    except Exception as e:
        print(f"Role summary enhancement failed: {e}")
        return content

def _enhance_project_description(content, job_description, company_analysis, used_verbs, job_keywords, tech_keywords):
    """Enhance project descriptions focusing on tech_stack alignment (max 2 sentences)"""

    try:
        import json
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        company_type = company_analysis.get('company_type', 'tech')
        golden_signals = company_analysis.get('golden_signals', [])
        used_verbs_list = list(used_verbs) if used_verbs else []

        prompt = f"""
        Enhance this personal project description so that it is intriguing to reader.
        The final description should not be more than one sentence.
        And within one sentence you have to highlight what the project is about and highlight any scale data or technological information if available.
        If possible try to nudge the description to align with the tech stack used by the company.
        Avoid the verbs that have been used already to give a diverse language.

        Original: "{content}"

        TARGET TECH STACK: {', '.join(tech_keywords)}
        SIGNALS SOUGHT BY COMPANY: {golden_signals}
        COMPANY TYPE: {company_type}
        USED VERBS: {', '.join(used_verbs_list)}

        Return JSON: {{"enhanced_content": "concise tech-focused description", "action_verb_used": "verb"}}
        """

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_tokens=200
        )

        return _parse_enhancement_response(response, content, used_verbs)

    except Exception as e:
        print(f"Project description enhancement failed: {e}")
        return content

def _enhance_general_content(content, job_description, company_analysis, content_type, used_verbs):
    """Fallback general enhancement for unknown content types"""

    try:
        import json
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        company_type = company_analysis.get('company_type', 'tech')
        top_values = company_analysis.get('top_values', [])
        used_verbs_list = list(used_verbs) if used_verbs else []

        prompt = f"""
        Enhance this {content_type} for a {company_type} company.

        Original: "{content}"
        Company values: {', '.join(top_values)}
        Used verbs: {', '.join(used_verbs_list)}

        Keep the same core facts, improve language for impact, use different action verbs.
        Return JSON: {{"enhanced_content": "enhanced text", "action_verb_used": "verb"}}
        """

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )

        return _parse_enhancement_response(response, content, used_verbs)

    except Exception as e:
        print(f"General enhancement failed: {e}")
        return content

def _parse_enhancement_response(response, original_content, used_verbs, type = None):
    """Parse AI response and handle JSON parsing with fallbacks"""

    try:
        response_text = response.choices[0].message.content.strip()

        # Clean up markdown formatting
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()

        result = json.loads(response_text)
        if type == None:
            
            enhanced_content = result.get('enhanced_content', original_content)
            action_verb = result.get('action_verb_used', '')

            # Add verb to tracking set
            if action_verb:
                used_verbs.add(action_verb.lower())
        elif type == "list":
            print(f'Original content: {original_content}')
            enhanced_content = result.get('enhanced_content', []) 
            print(f'Enhanced content: {enhanced_content}')
            assert len(enhanced_content) == len(original_content), "Enhanced content length mismatch"

            action_verbs = result.get('action_verbs_used', '')
            assert len(action_verbs) != 0
            for verb in action_verbs:
                used_verbs.add(verb.lower())
        elif type == "dict":
            print(f'Original content: {original_content}')
            enhanced_content = result.get('enhanced_content', {}) 
            print(f'Enhanced content: {enhanced_content}')
            assert len(enhanced_content) == len(original_content), "Enhanced content length mismatch"

            # check each key in original content is present in enhanced content
            for key in original_content.keys():
                assert str(key) in enhanced_content, f"Key {key} missing in enhanced content"

            action_verbs = result.get('action_verbs_used', '')
            assert len(action_verbs) != 0
            for verb in action_verbs:
                used_verbs.add(verb.lower())


        return enhanced_content, used_verbs

    except json.JSONDecodeError:
        # Try to extract content from malformed JSON
        print(f"JSON parsing failed for!, {response_text}")
        if '"enhanced_content":' in response_text:
            try:
                start = response_text.find('"enhanced_content":') + len('"enhanced_content":')
                content_part = response_text[start:].strip()
                if content_part.startswith('"'):
                    end = content_part.find('",', 1)
                    if end == -1:
                        end = content_part.find('"', 1)
                    if end > 0:
                        extracted_content = content_part[1:end]
                        # Try to extract verb
                        first_word = extracted_content.split()[0].rstrip('.,;:').lower()
                        used_verbs.add(first_word)
                        return extracted_content
            except:
                pass

        return original_content
    except Exception as e:
        print(f"Response parsing failed: {e}, {original_content}")
        return original_content

def _extract_job_keywords_and_tech_terms(job_description):
    """Extract both job keywords and technical terms from job description using AI and patterns"""
    try:
        import re
        from openai import OpenAI
        import os

        # Basic pattern-based extraction for immediate use
        job_lower = job_description.lower()

        # Dynamic tech pattern detection
        tech_patterns = [
            r'\b(python|java|javascript|typescript|react|node\.?js|angular|vue)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|terraform|ansible)\b',
            r'\b(sql|mongodb|postgresql|redis|elasticsearch|mysql)\b',
            r'\b(machine learning|ml|ai|data science|analytics)\b',
            r'\b(rest|api|microservices|graphql)\b',
            r'\b(git|ci/cd|devops|jenkins|github)\b',
            r'\b(agile|scrum|kanban)\b'
        ]

        tech_keywords = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, job_lower)
            tech_keywords.extend(matches)
        tech_keywords = list(set(tech_keywords))  # Deduplicate
        print(f'Tech keywords: {tech_keywords}')

        # Extract general job keywords using AI
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

            prompt = f"""
            Extract key technical skills and requirements from this job description.
            Return as comma-separated list of 10-15 most important keywords.
            Focus on: skills, technologies, methodologies, tools, frameworks.

            Job Description: {job_description[:1000]}

            Return only the comma-separated list, no other text.
            """

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )

            ai_keywords = [kw.strip() for kw in response.choices[0].message.content.split(',')]
            job_keywords = ai_keywords[:15]

        except Exception as e:
            print(f"AI keyword extraction failed: {e}")
            # Fallback to basic pattern extraction
            job_keywords = list(set(tech_keywords))[:10]

        # Combine and deduplicate
        all_tech_keywords = list(set(tech_keywords + job_keywords))[:15]
        print(f'All tech keywords: {all_tech_keywords}')

        return job_keywords, all_tech_keywords

    except Exception as e:
        print(f"Keyword extraction failed: {e}")
        return [], []


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
    
    # Info about next steps
    st.info("💡 **Next Steps:** You can now proceed to the 'AI Job Matching' tab to select the best content, or go directly to 'Review & Finalize' to edit your resume.")

def _render_step3_generate_matched_resume():
    """Step 3: AI selects best content mix for target job"""
    st.markdown("*AI will select the best combination of your content for this specific job.*")

    # Check if we have job context
    if not st.session_state.get('target_job_description'):
        st.warning("⚠️ Please complete Step 0 (Job Context) first to provide job description for matching.")
        return

    # Determine data source
    if st.session_state.get('approved_content'):
        st.info("📊 **Using Enhanced Content** - AI will select from your reviewed enhanced content")
        data_source = "enhanced"
    else:
        st.info("📋 **Using Original Content** - AI will select from your original resume content")
        data_source = "original"
    
    if st.button("🎯 Generate Best Match Resume", type="primary"):
        with st.spinner("AI is selecting the optimal content mix..."):
            try:
                # Use the original matcher with appropriate data source
                matcher = JobMatcher()

                # Determine which data to use for matching
                if data_source == "enhanced":
                    # Create a temporary resume data structure with approved enhanced content
                    resume_data_for_matching = _create_enhanced_resume_data_structure()
                else:
                    # Use original resume data
                    resume_data_for_matching = st.session_state.resume_data

                # Generate matched content
                selected_content = matcher.match_resume_to_job(
                    resume_data_for_matching,
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
                if st.button("🔄 Clear All AI Data & Start Over"):
                    st.session_state.enhanced_content = None
                    st.session_state.approved_content = None
                    st.session_state.selected_content = None
                    st.session_state.final_markdown = ""
                    st.success("Cleared! You can now start the AI process again.")
                    st.rerun()

            except Exception as e:
                st.error(f"Content selection failed: {str(e)}")

    # Info about next steps
    st.info("💡 **Next Steps:** Go to 'Review & Finalize' to edit your matched resume or 'Export Resume PDF' to download it.")

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

def _show_workflow_overview():
    """Display workflow overview for new users"""
    with st.sidebar.expander("💡 **How It Works**", expanded=False):
        st.markdown("""
        **AI-powered resume builder that creates job-specific PDFs in minutes**

        #### 📋 Simple 4-Step Process:

        **1. 📤 Upload** → Upload your existing resume (PDF/DOCX)

        **2. ✏️ Edit** → Review and edit extracted content

        **3. 🤖 AI Enhance** → Paste a job description, AI optimizes your content

        **4. 📄 Export** → Download professional PDF resume

        ---

        💡 **Why use this?**
        - AI tailors your resume for each job
        - No manual copy-pasting between tools
        - Professional PDF export included
        - Free with your OpenAI API key

        ⚠️ **Setup:** Add `OPENAI_API_KEY=sk-...` to `.env` file
        """)

def _get_workflow_status():
    """Get completion status for each workflow step"""
    return {
        'uploaded': st.session_state.resume_data is not None,
        'edited': st.session_state.resume_data is not None and _has_content(),
        'enhanced': st.session_state.get('content_enhanced', False),
        'reviewed': st.session_state.resume_data is not None
    }

def _has_content():
    """Check if resume has basic content"""
    if not st.session_state.resume_data:
        return False

    resume_data = st.session_state.resume_data

    # Check if has any meaningful content
    has_summary = bool(resume_data.get('summary', {}).get('sentences'))
    has_experience = bool(resume_data.get('experience'))
    has_skills = bool(resume_data.get('skills'))

    return has_summary or has_experience or has_skills

def _show_prerequisite_warning(required_step, message):
    """Show warning when prerequisite step is not completed"""
    st.warning(f"⚠️ **{message}**")
    st.info(f"👈 Please complete **{required_step}** first in the sidebar")
    return True

def cover_letter_page():
    """Generate cover letter using profile data and job information"""
    st.header("📝 Generate Cover Letter")
    st.markdown("**Create a personalized cover letter for your target job**")

    # Initialize session state for cover letter
    if 'cover_letter_job_info' not in st.session_state:
        st.session_state.cover_letter_job_info = {}
    if 'generated_cover_letter' not in st.session_state:
        st.session_state.generated_cover_letter = ""
    if 'cover_letter_inputs' not in st.session_state:
        st.session_state.cover_letter_inputs = {}

    # Job Information Section
    st.subheader("🏢 Job Information")

    col1, col2 = st.columns(2)

    with col1:
        # Check if job info exists from job matching page
        existing_company = st.session_state.get('target_company_name', '')
        existing_title = st.session_state.get('target_job_title', '')

        company_name = st.text_input(
            "Company Name",
            value=existing_company,
            placeholder="e.g., Google, Microsoft, Startup Inc."
        )

        job_title = st.text_input(
            "Job Title",
            value=existing_title,
            placeholder="e.g., Senior Software Engineer, Product Manager"
        )

    with col2:
        # Auto-populate from existing job description if available
        existing_job_desc = st.session_state.get('target_job_description', '')

        st.markdown("**Job Description**")
        job_description = st.text_area(
            "Paste the job description here:",
            value=existing_job_desc,
            height=120,
            placeholder="Paste the full job description or key requirements here..."
        )

        st.markdown("**More Information About Company (Optional)**")
        company_info = st.text_area(
            "Additional company context:",
            height=100,
            placeholder="Company culture, recent news, mission, values, or any other relevant information..."
        )

    st.divider()

    # Cover Letter Customization Section
    st.subheader("✍️ Customization")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Key Points to Include**")
        key_points = st.text_area(
            "List specific points you want to address:",
            height=120,
            placeholder="Examples:\n• Why not having an MS degree isn't a blocker\n• Passion for the company's mission\n• Relevant project experience\n• Career transition reasoning"
        )

        additional_instructions = st.text_area(
            "Additional Instructions (optional):",
            height=80,
            placeholder="Any specific tone, length, or style preferences..."
        )

    with col2:
        st.markdown("**Style**")
        cover_letter_style = st.radio(
            "Choose style:",
            ["Professional", "Personal", "Balanced"],
            help="Professional: Formal, business-focused\nPersonal: Warm, story-driven\nBalanced: Mix of both"
        )

    # Generate Button
    st.divider()

    # Validation before generation
    can_generate = bool(company_name and job_title and job_description and st.session_state.resume_data)

    if not can_generate:
        missing_items = []
        if not company_name: missing_items.append("Company Name")
        if not job_title: missing_items.append("Job Title")
        if not job_description: missing_items.append("Job Description")
        if not st.session_state.resume_data: missing_items.append("Resume Profile")

        st.warning(f"⚠️ Please provide: {', '.join(missing_items)}")

    if st.button("🎯 Generate Cover Letter", type="primary", disabled=not can_generate):
        # Store inputs for potential regeneration
        st.session_state.cover_letter_inputs = {
            'company_name': company_name,
            'job_title': job_title,
            'job_description': job_description,
            'key_points': key_points,
            'style': cover_letter_style,
            'additional_instructions': additional_instructions
        }

        with st.spinner("Generating your personalized cover letter..."):
            try:
                generated_letter = _generate_cover_letter(
                    st.session_state.resume_data,
                    company_name,
                    job_title,
                    job_description,
                    company_info,
                    key_points,
                    cover_letter_style,
                    additional_instructions
                )
                st.session_state.generated_cover_letter = generated_letter
                st.success("✅ Cover letter generated successfully!")

            except Exception as e:
                st.error(f"❌ Cover letter generation failed: {str(e)}")

    # Preview and Edit Section
    if st.session_state.generated_cover_letter:
        st.divider()
        st.subheader("📄 Cover Letter Preview & Edit")

        # Editable preview
        edited_letter = st.text_area(
            "Edit your cover letter:",
            value=st.session_state.generated_cover_letter,
            height=400,
            help="Make any changes you'd like to the generated cover letter"
        )

        # Update stored version if edited
        if edited_letter != st.session_state.generated_cover_letter:
            st.session_state.generated_cover_letter = edited_letter

        # Regenerate option
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔄 Regenerate", help="Generate a new version with the same inputs"):
                if st.session_state.cover_letter_inputs:
                    with st.spinner("Regenerating cover letter..."):
                        try:
                            inputs = st.session_state.cover_letter_inputs
                            new_letter = _generate_cover_letter(
                                st.session_state.resume_data,
                                inputs['company_name'],
                                inputs['job_title'],
                                inputs['job_description'],
                                inputs.get('company_info', ''),
                                inputs['key_points'],
                                inputs['style'],
                                inputs['additional_instructions']
                            )
                            st.session_state.generated_cover_letter = new_letter
                            st.success("✅ New cover letter generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Regeneration failed: {str(e)}")

        with col2:
            # Copy to clipboard functionality (placeholder)
            st.button("📋 Copy to Clipboard", help="Copy cover letter text (implementation needed)")

    # Answer a Question Section
    st.divider()
    st.header("❓ Answer a Question")
    st.markdown("**Answer specific questions that companies ask during application process**")

    # Initialize session state for question answering
    if 'generated_answer' not in st.session_state:
        st.session_state.generated_answer = ""
    if 'answer_inputs' not in st.session_state:
        st.session_state.answer_inputs = {}

    # Question input
    st.subheader("📝 Question & Customization")

    col1, col2 = st.columns([2, 1])

    with col1:
        question_text = st.text_area(
            "Question to Answer:",
            height=100,
            placeholder="Example: Why are you interested in this role? Tell us about a time you overcame a challenge. Why do you want to work at our company?"
        )

        answer_key_points = st.text_area(
            "Key Points to Include:",
            height=100,
            placeholder="Examples:\n• Specific experience that relates to the question\n• Personal motivation or passion\n• Concrete examples or metrics\n• Connection to company values"
        )

        answer_additional_instructions = st.text_area(
            "Additional Instructions (optional):",
            height=80,
            placeholder="Tone preferences, specific examples to mention, length requirements..."
        )

    with col2:
        st.markdown("**Style**")
        answer_style = st.radio(
            "Choose answer style:",
            ["Professional", "Personal", "Balanced"],
            key="answer_style",
            help="Professional: Formal, achievement-focused\nPersonal: Story-driven, authentic\nBalanced: Mix of both"
        )

    # Validation for answer generation
    can_generate_answer = bool(question_text and company_name and job_description and st.session_state.resume_data)

    if not can_generate_answer:
        missing_items = []
        if not question_text: missing_items.append("Question")
        if not company_name: missing_items.append("Company Name")
        if not job_description: missing_items.append("Job Description")
        if not st.session_state.resume_data: missing_items.append("Resume Profile")

        st.warning(f"⚠️ Please provide: {', '.join(missing_items)}")

    # Generate Answer Button
    if st.button("🎯 Generate Answer", type="primary", disabled=not can_generate_answer):
        # Store inputs for potential regeneration
        st.session_state.answer_inputs = {
            'question_text': question_text,
            'company_name': company_name,
            'job_title': job_title,
            'job_description': job_description,
            'company_info': company_info,
            'key_points': answer_key_points,
            'style': answer_style,
            'additional_instructions': answer_additional_instructions
        }

        with st.spinner("Generating your answer..."):
            try:
                generated_answer = _generate_question_answer(
                    st.session_state.resume_data,
                    question_text,
                    company_name,
                    job_title,
                    job_description,
                    company_info,
                    answer_key_points,
                    answer_style,
                    answer_additional_instructions
                )
                st.session_state.generated_answer = generated_answer
                st.success("✅ Answer generated successfully!")

            except Exception as e:
                st.error(f"❌ Answer generation failed: {str(e)}")

    # Answer Preview and Edit Section
    if st.session_state.generated_answer:
        st.divider()
        st.subheader("📄 Answer Preview & Edit")

        # Editable preview
        edited_answer = st.text_area(
            "Edit your answer:",
            value=st.session_state.generated_answer,
            height=300,
            help="Make any changes you'd like to the generated answer"
        )

        # Update stored version if edited
        if edited_answer != st.session_state.generated_answer:
            st.session_state.generated_answer = edited_answer

        # Regenerate option for answer
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔄 Regenerate Answer", help="Generate a new version with the same inputs"):
                if st.session_state.answer_inputs:
                    with st.spinner("Regenerating answer..."):
                        try:
                            inputs = st.session_state.answer_inputs
                            new_answer = _generate_question_answer(
                                st.session_state.resume_data,
                                inputs['question_text'],
                                inputs['company_name'],
                                inputs['job_title'],
                                inputs['job_description'],
                                inputs['company_info'],
                                inputs['key_points'],
                                inputs['style'],
                                inputs['additional_instructions']
                            )
                            st.session_state.generated_answer = new_answer
                            st.success("✅ New answer generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Answer regeneration failed: {str(e)}")

        with col2:
            # Copy to clipboard functionality (placeholder)
            st.button("📋 Copy Answer", help="Copy answer text (implementation needed)")

def _generate_cover_letter(resume_data, company_name, job_title, job_description, company_info, key_points, style, additional_instructions):
    """Generate cover letter using AI based on resume data and job requirements"""
    import json
    from openai import OpenAI
    import os

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Extract key info from resume
    contact_info = resume_data.get('contact', {})
    name = contact_info.get('name', 'Your Name')
    experience = resume_data.get('experience', [])
    skills = resume_data.get('skills', {})
    projects = resume_data.get('projects', [])

    # Build context about the candidate
    experience_summary = []
    for exp in experience[:3]:  # Top 3 experiences
        role = exp.get('position', 'Role')
        company = exp.get('company', 'Company')
        accomplishments = exp.get('accomplishments', [])[:2]  # Top 2 accomplishments
        experience_summary.append(f"{role} at {company}: {'; '.join(accomplishments)}")

    project_summary = [f"{proj.get('name', 'Project')}: {'; '.join(proj.get('descriptions', [])[:1])}" for proj in projects[:2]]

    # Style-specific instructions
    style_instructions = {
        'Professional': "Use formal business language, focus on qualifications and achievements. Be concise and direct.",
        'Personal': "Use a warm, conversational tone. Include personal motivations and passion. Tell a story.",
        'Balanced': "Mix professional achievements with personal motivation. Be approachable yet competent."
    }

    # Include company info in context if provided
    company_context = f"\nCompany Context: {company_info}" if company_info.strip() else ""

    prompt = f"""
    Write a compelling cover letter for this job application.

    CANDIDATE INFO:
    Name: {name}
    Top Experience: {' | '.join(experience_summary[:2])}
    Key Projects: {' | '.join(project_summary)}
    Skills: {', '.join(list(skills.get('technical', []))[:8])}

    JOB DETAILS:
    Company: {company_name}
    Position: {job_title}
    Job Description: {job_description[:1000]}{company_context}

    SPECIFIC POINTS TO ADDRESS:
    {key_points}

    STYLE: {style} - {style_instructions.get(style, '')}

    ADDITIONAL INSTRUCTIONS:
    {additional_instructions}

    REQUIREMENTS:
    - Write 3-4 paragraphs
    - Start with engaging opening that shows knowledge of company
    - Address specific job requirements with concrete examples
    - Include the key points naturally
    - End with strong closing and call to action
    - Use plain text format (NO MARKDOWN)
    - Keep professional yet engaging tone
    - Maximum 400 words

    Return only the cover letter text, no extra formatting or labels.
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Higher for more creativity
            max_tokens=600
        )

        cover_letter = response.choices[0].message.content.strip()

        # Clean up any unwanted formatting
        cover_letter = cover_letter.replace('```', '').replace('**', '').replace('*', '')

        return cover_letter

    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")

def _generate_question_answer(resume_data, question_text, company_name, job_title, job_description, company_info, key_points, style, additional_instructions):
    """Generate answer to a specific question using AI based on resume data and job context"""
    from openai import OpenAI
    import os

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Extract key info from resume
    contact_info = resume_data.get('contact', {})
    name = contact_info.get('name', 'Your Name')
    experience = resume_data.get('experience', [])
    skills = resume_data.get('skills', {})
    projects = resume_data.get('projects', [])

    # Build context about the candidate
    experience_summary = []
    for exp in experience[:3]:  # Top 3 experiences
        role = exp.get('position', 'Role')
        company = exp.get('company', 'Company')
        accomplishments = exp.get('accomplishments', [])[:2]  # Top 2 accomplishments
        experience_summary.append(f"{role} at {company}: {'; '.join(accomplishments)}")

    project_summary = [f"{proj.get('name', 'Project')}: {'; '.join(proj.get('descriptions', [])[:1])}" for proj in projects[:2]]

    # Style-specific instructions for answers
    style_instructions = {
        'Professional': "Use formal language, focus on concrete achievements and qualifications. Be results-oriented.",
        'Personal': "Use authentic, story-driven language. Share personal insights and motivations. Be relatable.",
        'Balanced': "Mix professional achievements with personal perspective. Be both competent and approachable."
    }

    # Include company info in context if provided
    company_context = f"\nCompany Context: {company_info}" if company_info.strip() else ""

    prompt = f"""
    Answer this specific question for a job application.

    QUESTION TO ANSWER:
    {question_text}

    CANDIDATE INFO:
    Name: {name}
    Top Experience: {' | '.join(experience_summary[:2])}
    Key Projects: {' | '.join(project_summary)}
    Skills: {', '.join(list(skills.get('technical', []))[:8])}

    JOB CONTEXT:
    Company: {company_name}
    Position: {job_title}
    Job Description: {job_description[:800]}{company_context}

    SPECIFIC POINTS TO INCLUDE:
    {key_points}

    STYLE: {style} - {style_instructions.get(style, '')}

    ADDITIONAL INSTRUCTIONS:
    {additional_instructions}

    REQUIREMENTS:
    - Write 2 small paragraphs maximum
    - Directly answer the question asked
    - Use specific examples from candidate's experience
    - Connect answer to the job/company context
    - Include the key points naturally
    - Use plain text format (NO MARKDOWN)
    - Be concise but impactful
    - Maximum 200 words

    Return only the answer text, no extra formatting or labels.
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Higher for more creativity
            max_tokens=400
        )

        answer = response.choices[0].message.content.strip()

        # Clean up any unwanted formatting
        answer = answer.replace('```', '').replace('**', '').replace('*', '')

        return answer

    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")

if __name__ == "__main__":
    main()