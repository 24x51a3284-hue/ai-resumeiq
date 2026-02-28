# ============================================================
# app.py — The BRAIN of your project (Flask Backend)
# This file runs the server and handles all requests from
# the frontend (HTML pages).
# ============================================================

# --- Import Libraries ---
# Flask is the web framework (like a waiter between frontend and backend)
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file

# werkzeug helps us save uploaded files safely
from werkzeug.utils import secure_filename

# os lets us work with files and folders
import os

# datetime gives us the current date and time
from datetime import datetime

# json helps convert Python objects to JSON (for sending to frontend)
import json

# Import our custom modules (files we'll create)
from modules.nlp_processor import extract_text_from_file, extract_skills, calculate_similarity
from modules.database import init_db, get_db, close_db
from modules.report_generator import generate_pdf_report

# ============================================================
# APP SETUP
# ============================================================

# Create the Flask app — this is like starting the engine
app = Flask(__name__)

# Secret key is needed for login sessions (like a password for cookies)
# CHANGE THIS to any random string in a real project
app.secret_key = 'resume_matcher_secret_key_2024'

# Folder where uploaded resumes will be saved
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Only allow PDF and DOCX files to be uploaded
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Initialize the database when app starts
with app.app_context():
    init_db()

# ============================================================
# HELPER FUNCTION
# ============================================================

def allowed_file(filename):
    """Check if the uploaded file is PDF or DOCX"""
    # Split filename at the dot, get the extension, check if it's allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# ROUTES — Each route is a "page" or "action"
# ============================================================

# --- HOME PAGE ---
@app.route('/')
def index():
    """Show the main landing page"""
    # If user is logged in, go to dashboard; else show landing page
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# --- SIGNUP PAGE ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    GET  = Show the signup form
    POST = Process the form data (create account)
    """
    if request.method == 'POST':
        # Get data from the form
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # Basic validation
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})

        db = get_db()
        # Check if email already exists
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'Email already registered'})

        # Save the new user (in real apps, hash the password!)
        db.execute(
            'INSERT INTO users (username, email, password, created_at) VALUES (?, ?, ?, ?)',
            (username, email, password, datetime.now().isoformat())
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Account created! Please login.'})

    return render_template('signup.html')


# --- LOGIN PAGE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  = Show the login form
    POST = Check credentials and log in
    """
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        db = get_db()
        # Look for user in database
        user = db.execute(
            'SELECT * FROM users WHERE email = ? AND password = ?',
            (email, password)
        ).fetchone()

        if user:
            # Save user info in session (like a login cookie)
            session['user_id']  = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'redirect': '/dashboard'})
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'})

    return render_template('login.html')


# --- LOGOUT ---
@app.route('/logout')
def logout():
    """Clear the session and go back to login"""
    session.clear()
    return redirect(url_for('login'))


# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    """Show the main dashboard — requires login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    # Get last 5 analyses done by this user
    analyses = db.execute(
        'SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()

    return render_template('dashboard.html',
                           username=session['username'],
                           analyses=analyses)


# --- ANALYZER PAGE ---
@app.route('/analyzer')
def analyzer():
    """Show the resume analysis page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analyzer.html', username=session['username'])


# --- PROCESS RESUME (Main API endpoint) ---
@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    """
    This is the most important function.
    It:
    1. Receives the uploaded resume and job description
    2. Extracts text from the resume
    3. Runs NLP analysis
    4. Calculates similarity score
    5. Returns results as JSON
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401

    # Get job description from form
    job_description = request.form.get('job_description', '').strip()
    if not job_description:
        return jsonify({'error': 'Please enter a job description'}), 400

    # Check if file was uploaded
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF and DOCX files are allowed'}), 400

    # Save the file safely
    filename = secure_filename(file.filename)
    # Add timestamp to avoid name conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = f"{timestamp}_{filename}"
    filepath  = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # ---- STEP 1: Extract text from resume ----
    resume_text = extract_text_from_file(filepath)
    if not resume_text:
        return jsonify({'error': 'Could not read the resume file'}), 400

    # ---- STEP 2: Extract skills from both texts ----
    resume_skills    = extract_skills(resume_text)
    jd_skills        = extract_skills(job_description)

    # ---- STEP 3: Calculate similarity score ----
    similarity_score = calculate_similarity(resume_text, job_description)

    # ---- STEP 4: Find missing and matching skills ----
    resume_skills_set = set([s.lower() for s in resume_skills])
    jd_skills_set     = set([s.lower() for s in jd_skills])

    matched_skills = list(resume_skills_set.intersection(jd_skills_set))
    missing_skills = list(jd_skills_set.difference(resume_skills_set))

    # ---- STEP 5: Calculate final ATS score (0-100) ----
    # Combine similarity score + skill match ratio
    if len(jd_skills) > 0:
        skill_match_ratio = len(matched_skills) / len(jd_skills_set) * 100
    else:
        skill_match_ratio = 0

    # Final score: 60% similarity + 40% skill match
    final_score = round((similarity_score * 0.6) + (skill_match_ratio * 0.4), 2)
    final_score = min(final_score, 100)  # Cap at 100

    # ---- STEP 6: Career Recommendations ----
    career_suggestions = get_career_suggestions(matched_skills, missing_skills)

    # ---- STEP 7: Resume Tips ----
    tips = get_resume_tips(final_score, missing_skills)

    # ---- STEP 8: Save to database ----
    db = get_db()
    db.execute(
        '''INSERT INTO analyses
           (user_id, resume_filename, ats_score, matched_skills, missing_skills,
            job_description, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (
            session['user_id'],
            filename,
            final_score,
            json.dumps(matched_skills),
            json.dumps(missing_skills),
            job_description[:500],  # Store first 500 chars
            datetime.now().isoformat()
        )
    )
    db.commit()

    # ---- STEP 9: Return results to frontend ----
    return jsonify({
        'success': True,
        'ats_score': final_score,
        'similarity_score': round(similarity_score, 2),
        'skill_match_percent': round(skill_match_ratio, 2),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'resume_skills': list(resume_skills_set),
        'jd_skills': list(jd_skills_set),
        'career_suggestions': career_suggestions,
        'tips': tips,
        'resume_filename': filename
    })


# --- MULTIPLE RESUME RANKING ---
@app.route('/api/rank-resumes', methods=['POST'])
def rank_resumes():
    """
    Rank multiple resumes against one job description.
    Returns them sorted from best to worst match.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401

    job_description = request.form.get('job_description', '').strip()
    if not job_description:
        return jsonify({'error': 'Please enter a job description'}), 400

    files = request.files.getlist('resumes')
    if len(files) < 2:
        return jsonify({'error': 'Please upload at least 2 resumes to rank'}), 400

    results = []
    for file in files:
        if file and allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath  = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
            file.save(filepath)

            resume_text  = extract_text_from_file(filepath)
            if resume_text:
                score        = calculate_similarity(resume_text, job_description)
                res_skills   = extract_skills(resume_text)
                jd_skills    = extract_skills(job_description)
                matched      = set([s.lower() for s in res_skills]).intersection(
                               set([s.lower() for s in jd_skills]))
                skill_ratio  = (len(matched) / max(len(jd_skills), 1)) * 100
                final        = round((score * 0.6) + (skill_ratio * 0.4), 2)

                results.append({
                    'name':           file.filename,
                    'score':          final,
                    'matched_skills': list(matched),
                    'skill_percent':  round(skill_ratio, 2)
                })

    # Sort by score, highest first
    results.sort(key=lambda x: x['score'], reverse=True)
    # Add rank numbers
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return jsonify({'success': True, 'rankings': results})


# --- ADMIN DASHBOARD ---
@app.route('/admin')
def admin():
    """Admin page — shows all users and analyses"""
    # Simple admin check (in real app use proper auth)
    if session.get('username') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    users    = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    analyses = db.execute(
        'SELECT a.*, u.username FROM analyses a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC'
    ).fetchall()

    # Stats for charts
    total_users    = len(users)
    total_analyses = len(analyses)
    avg_score      = 0
    if analyses:
        avg_score = round(sum(a['ats_score'] for a in analyses) / len(analyses), 1)

    return render_template('admin.html',
                           users=users,
                           analyses=analyses,
                           total_users=total_users,
                           total_analyses=total_analyses,
                           avg_score=avg_score)


# --- DOWNLOAD PDF REPORT ---
@app.route('/api/download-report/<int:analysis_id>')
def download_report(analysis_id):
    """Generate and download a PDF report for an analysis"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    analysis = db.execute(
        'SELECT * FROM analyses WHERE id = ? AND user_id = ?',
        (analysis_id, session['user_id'])
    ).fetchone()

    if not analysis:
        return 'Analysis not found', 404

    # Generate PDF and get the file path
    pdf_path = generate_pdf_report(analysis, session['username'])
    return send_file(pdf_path, as_attachment=True,
                     download_name=f'resume_report_{analysis_id}.pdf')


# --- GET PREVIOUS RESULTS ---
@app.route('/api/history')
def get_history():
    """Return all past analyses for the logged-in user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    analyses = db.execute(
        'SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()

    results = []
    for a in analyses:
        results.append({
            'id':              a['id'],
            'resume_filename': a['resume_filename'],
            'ats_score':       a['ats_score'],
            'created_at':      a['created_at'],
            'matched_skills':  json.loads(a['matched_skills']) if a['matched_skills'] else [],
            'missing_skills':  json.loads(a['missing_skills']) if a['missing_skills'] else []
        })

    return jsonify({'success': True, 'history': results})


# ============================================================
# HELPER FUNCTIONS FOR SUGGESTIONS
# ============================================================

def get_career_suggestions(matched_skills, missing_skills):
    """
    Based on the skills found, suggest career paths.
    This is a rule-based AI suggestion system.
    """
    all_skills = set(matched_skills + missing_skills)

    careers = []

    # Check which domain the skills belong to
    if any(s in all_skills for s in ['python', 'machine learning', 'tensorflow', 'pytorch', 'data science']):
        careers.append({
            'title': '🤖 Machine Learning Engineer',
            'match': 'High',
            'description': 'Build AI/ML models for real-world applications',
            'next_steps': 'Learn Deep Learning, Computer Vision, NLP'
        })

    if any(s in all_skills for s in ['sql', 'pandas', 'numpy', 'tableau', 'power bi', 'statistics']):
        careers.append({
            'title': '📊 Data Analyst / Data Scientist',
            'match': 'High',
            'description': 'Analyze data and create business insights',
            'next_steps': 'Learn Advanced Statistics, A/B Testing, Storytelling'
        })

    if any(s in all_skills for s in ['javascript', 'react', 'html', 'css', 'node']):
        careers.append({
            'title': '🌐 Full Stack Web Developer',
            'match': 'High',
            'description': 'Build complete web applications',
            'next_steps': 'Learn TypeScript, Cloud Deployment, Docker'
        })

    if any(s in all_skills for s in ['aws', 'docker', 'kubernetes', 'devops', 'linux']):
        careers.append({
            'title': '☁️ DevOps / Cloud Engineer',
            'match': 'Medium',
            'description': 'Manage cloud infrastructure and CI/CD pipelines',
            'next_steps': 'Get AWS/Azure certifications'
        })

    if any(s in all_skills for s in ['nlp', 'bert', 'transformers', 'llm', 'gpt']):
        careers.append({
            'title': '🧠 NLP / AI Research Engineer',
            'match': 'High',
            'description': 'Work on language models and AI research',
            'next_steps': 'Read research papers, contribute to Hugging Face'
        })

    # Default suggestion if nothing matches
    if not careers:
        careers.append({
            'title': '💻 Software Developer',
            'match': 'Medium',
            'description': 'Build software applications across various domains',
            'next_steps': 'Strengthen core programming skills and pick a specialization'
        })

    return careers[:3]  # Return top 3


def get_resume_tips(score, missing_skills):
    """Return personalized resume improvement tips based on score"""
    tips = []

    if score < 30:
        tips.append('🔴 Your resume needs significant improvement. Focus on adding relevant keywords.')
        tips.append('📝 Rewrite your resume to match the job description more closely.')
        tips.append('🎯 Add a strong summary section targeting this specific role.')
    elif score < 60:
        tips.append('🟡 Your resume is a partial match. Add more relevant skills.')
        tips.append('📊 Use numbers to quantify achievements (e.g., "Improved performance by 30%").')
        tips.append('🔑 Include action verbs like: Developed, Implemented, Designed, Led.')
    else:
        tips.append('🟢 Great resume! A few tweaks will make it perfect.')
        tips.append('✨ Make sure your LinkedIn profile matches your resume.')
        tips.append('🌟 Add links to GitHub projects or portfolio.')

    # Tips for missing skills
    if missing_skills:
        top_missing = missing_skills[:3]
        tips.append(f'📚 Learn these in-demand skills: {", ".join(top_missing)}')
        tips.append('🏆 Add relevant certifications (Coursera, Udemy, Google) to fill skill gaps.')

    # General tips
    tips.append('📄 Keep your resume to 1-2 pages maximum.')
    tips.append('🎨 Use a clean, ATS-friendly format with no graphics or tables.')

    return tips


# ============================================================
# RUN THE APP
# ============================================================

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)