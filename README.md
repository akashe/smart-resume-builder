# Resume Matcher MVP

An end-to-end AI-powered resume optimization platform that **automatically parses your resume, enhances content based on specific job descriptions and target companies, then directly exports professional PDFs** - eliminating manual formatting work. Unlike other tools that only provide enhanced text content, this application delivers a complete workflow from upload to final PDF, saving hours of manual editing and formatting.


## 🚦 Quick Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd resume-matcher-mvp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.sample .env
   # Add your OpenAI API key to .env
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## 📋 Usage Workflow

### **Step 1: Resume Upload & Parsing**
- Upload PDF/DOCX resume files
- Automatic content extraction and structuring
- Validation and error handling

### **Step 2: Edit & Add Information**
- Review and edit all parsed sections
- Add multiple variations of accomplishments
- Manage contact information and skills

### **Step 3: AI Enhancement** 
- **Enhance**: AI generates improved content variations
- **Review**: Select which suggestions to approve
- **Apply**: Chosen enhancements are integrated
- Global verb tracking ensures diverse language

### **Step 4: Job Matching & Analysis**
- Paste target job description
- AI analyzes company culture and requirements
- Intelligent content selection for optimal fit
- Positioning recommendations provided

### **Step 5: Final Review & Export**
- Markdown editor for final content refinement
- Choose export format and theme
- Generate professional PDF output


## ⚙️ Advanced Features

### **Company Intelligence**
- Startup vs Enterprise vs Big Tech detection
- Cultural values analysis and scoring
- Hidden hiring preferences identification
- Industry-specific positioning advice

### **AI Content Enhancement**
- Context-aware content generation
- Impact-focused accomplishment writing
- Technical skill positioning
- Global language diversity tracking

### **Auto generate PDF for the enhanced resume**
- Professional PDF template generation using RenderCV
- Advanced typesetting with Typst
- Theme-based styling system

## 🔧 Configuration Options

### **Environment Variables**
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
```

---

**Built for modern job seekers** who need intelligent, data-driven resume optimization! 🎯