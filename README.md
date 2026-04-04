# Smart Resume Builder

> Upload your resume, paste a job description, get an optimized PDF in minutes.

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/Powered%20by-OpenAI-412991?logo=openai)](https://openai.com)

## What It Does

1. **Upload** your resume (PDF/DOCX)
2. **AI Enhancement** - Paste job description → AI optimizes your content
3. **Export** professional PDF with your choice of themes

## Quick Start

```bash
# Clone and install
git clone https://github.com/akashe/smart-resume-builder.git
cd smart-resume-builder
pip install -r requirements.txt

# Add your OpenAI API key
cp .env.sample .env
# Edit .env: OPENAI_API_KEY=your_key_here

# Run
streamlit run app.py
```

## Features

- ✅ Smart AI parsing (handles experience, education, projects, skills, custom sections)
- ✅ Job-specific optimization (matches keywords, adjusts tone)
- ✅ Professional PDF themes (powered by RenderCV)
- ✅ Cover letter generator
- ✅ Company culture analysis
- ✅ Free to use (bring your own OpenAI API key)

## Cost

~$0.01-0.05 per resume (OpenAI API usage). The app is free.

## License

MIT
