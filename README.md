# 🎯 AI Resume Skill Matcher — Complete Setup Guide
## B.Tech CSE (Data Science) Minor Project

---

## 📁 FOLDER STRUCTURE

```
resume_matcher/          ← Your main project folder
│
├── app.py               ← Flask backend (the brain)
├── requirements.txt     ← List of Python packages
│
├── modules/             ← Python helper files
│   ├── __init__.py      ← Makes it a Python package
│   ├── nlp_processor.py ← NLP: text extraction & skill matching
│   ├── database.py      ← SQLite database operations
│   └── report_generator.py  ← PDF report creator
│
├── templates/           ← HTML pages (Flask looks here)
│   ├── index.html       ← Landing page
│   ├── login.html       ← Login page
│   ├── signup.html      ← Signup page
│   ├── dashboard.html   ← User dashboard
│   ├── analyzer.html    ← Resume analyzer page
│   └── admin.html       ← Admin panel
│
└── static/              ← CSS, JS, uploaded files
    ├── css/
    │   └── style.css    ← All styles (dark theme)
    ├── js/
    │   ├── main.js      ← General JavaScript
    │   └── analyzer.js  ← Analyzer page JavaScript
    └── uploads/         ← Where resumes are saved
```

---

## 🛠️ INSTALLATION GUIDE (Step by Step)

### STEP 1: Install Python
- Go to https://python.org/downloads
- Download Python 3.10 or higher
- During install, CHECK ☑️ "Add Python to PATH"
- Verify: Open CMD and type `python --version`

### STEP 2: Install VS Code
- Go to https://code.visualstudio.com
- Download and install
- Install extension: Python (by Microsoft)

### STEP 3: Open Your Project in VS Code
- Open VS Code
- File → Open Folder → select the `resume_matcher` folder

### STEP 4: Create Virtual Environment
A virtual environment is like a clean box for your project's packages.

Open VS Code Terminal (Ctrl + ` backtick) and type:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows):
venv\Scripts\activate

# Activate it (Mac/Linux):
source venv/bin/activate

# You should see (venv) before your prompt
```

### STEP 5: Install All Packages
```bash
pip install -r requirements.txt
```

Wait for all packages to download. This may take 2-5 minutes.

### STEP 6: Download NLTK Data
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"
```

### STEP 7: Run the Application
```bash
python app.py
```

You should see:
```
✅ Database initialized successfully
✅ Default admin created: admin@resumematcher.com / admin123
 * Running on http://127.0.0.1:5000
```

### STEP 8: Open in Browser
Go to: http://localhost:5000

---

## 🔑 LOGIN CREDENTIALS

| Account | Email | Password |
|---------|-------|----------|
| Admin   | admin@resumematcher.com | admin123 |
| Create your own via signup | | |

---

## 🧪 HOW TO TEST

1. Open http://localhost:5000
2. Click "Get Started Free" → Create an account
3. Login
4. Click "Analyze Resume"
5. Upload a PDF resume (or create a simple one)
6. Paste a job description from LinkedIn/Naukri
7. Click "Analyze with AI"
8. See your results!

---

## 🐛 COMMON ERRORS & FIXES

### Error: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask
```

### Error: "NLTK punkt not found"
```bash
python -c "import nltk; nltk.download('all')"
```

### Error: Port 5000 already in use
```bash
# Change port in app.py (last line):
app.run(debug=True, port=5001)
# Then go to http://localhost:5001
```

### Error: "No such file or directory: uploads"
```bash
mkdir static/uploads
mkdir static/reports
```

### Error: PyPDF2 can't read PDF
- Make sure PDF is not password protected
- Try a different PDF
- DOCX format works more reliably

---

## 🎤 VIVA EXPLANATION

### Q: What is TF-IDF?
**A:** TF-IDF stands for Term Frequency-Inverse Document Frequency.
- **TF**: How often a word appears in a document
- **IDF**: How rare the word is across all documents
- Together, they convert text into numerical vectors that represent importance of each word.

### Q: What is Cosine Similarity?
**A:** Cosine Similarity measures the angle between two text vectors.
- If two documents are identical → similarity = 1.0 (100%)
- If completely different → similarity = 0.0 (0%)
- We use it to compare the resume vector and job description vector.

### Q: How does Skill Extraction work?
**A:** We maintain a database of 500+ technical skills. We use Regular Expressions (regex) to scan the text and check if any skill from our database appears in the resume or job description. We use word boundary matching to avoid false positives.

### Q: What is the ATS Score formula?
**A:** Final Score = (Cosine Similarity × 60%) + (Skill Match Ratio × 40%)
- 60% weight on TF-IDF similarity (considers all words)
- 40% weight on specific skill matches

### Q: What is Flask?
**A:** Flask is a micro web framework in Python. It acts as a web server that receives requests from the browser (frontend) and processes them using Python (backend). It returns HTML pages or JSON data as responses.

### Q: What is SQLite?
**A:** SQLite is a lightweight file-based database. All data is stored in a single file (resume_matcher.db). No separate database server needed. Perfect for small projects.

### Q: How does the Login system work?
**A:** When a user logs in:
1. We check their email/password against the database
2. If match found, we create a Flask "session" (like a login cookie)
3. The session stores the user_id so Flask knows they're logged in
4. When they logout, we clear the session

---

## 📊 PROJECT FEATURES CHECKLIST

- [x] Resume Upload (PDF/DOCX) with drag & drop
- [x] Job Description Input
- [x] Skill Extraction using NLP (regex + skills database)
- [x] TF-IDF + Cosine Similarity Score
- [x] Resume Score (0–100%)
- [x] Skill Gap Analysis (matched vs missing skills)
- [x] Missing Skills Suggestion
- [x] Career Recommendation (rule-based AI)
- [x] Resume Ranking (multiple resumes)
- [x] Admin Dashboard
- [x] Charts using Chart.js (pie, doughnut, bar, line)
- [x] Downloadable PDF Report
- [x] Login & Signup system
- [x] Save previous results in SQLite database
- [x] Dark theme with gradients and animations
- [x] Drag & drop upload zone
- [x] Password strength indicator
- [x] Loading animation with status messages
- [x] Mobile responsive design
