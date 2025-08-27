# Resume Matcher MVP

A Streamlit-based tool that intelligently matches your resume content to job descriptions using AI.

## Features

- 📤 **Resume Upload**: Parse PDF and DOCX resumes
- ✏️ **Content Management**: Add multiple variations of bullet points
- 🎯 **AI Job Matching**: Automatically select best content for each job
- 📝 **Markdown Editor**: Edit the generated resume
- 📄 **PDF Export**: Generate ATS-friendly PDFs

## Quick Setup (2 minutes)

1. **Clone/Download** this folder
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up OpenAI API**:
   - Copy `.env.sample` to `.env`
   - Add your OpenAI API key
4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

## Usage Flow

1. **Upload Resume** → Parse your existing resume
2. **Edit Sections** → Add multiple bullet point variations  
3. **Job Matching** → Paste job description, let AI select best content
4. **Edit Markdown** → Fine-tune the generated resume
5. **Export PDF** → Download ATS-friendly PDF

## Key Benefits

- **Multiple Variations**: Store different ways to describe the same achievement
- **AI Selection**: Automatically picks the best content for each job
- **ATS-Friendly**: Professional formatting that passes applicant tracking systems
- **Quick Iterations**: Easily create customized resumes for different positions

## Technical Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-3.5-turbo
- **Parsing**: python-docx, PyPDF2
- **PDF Generation**: WeasyPrint
- **Storage**: SQLite

## File Structure

```
resume-matcher-mvp/
├── app.py              # Main Streamlit application
├── parser.py           # Resume parsing logic
├── matcher.py          # AI job matching system
├── exporter.py         # PDF generation
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Troubleshooting

**PDF Generation Issues**: If WeasyPrint fails, install system dependencies:
- **Mac**: `brew install cairo pango gdk-pixbuf libffi`
- **Ubuntu**: `apt-get install libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev`

**OpenAI API Errors**: Ensure your API key is valid and has sufficient credits.

## Future Enhancements

- Multiple resume templates
- Batch job application processing
- LinkedIn integration
- Resume scoring and feedback
- Cover letter generation

---

**Built in 2 days** for rapid resume customization! 🚀