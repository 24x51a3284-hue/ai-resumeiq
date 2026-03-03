# app.py — Updated with Gmail Email Verification
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import threading
from datetime import datetime, timedelta
import json
import secrets
import urllib.request

from modules.nlp_processor import extract_text_from_file, extract_skills, calculate_similarity
from modules.database import init_db, get_db, close_db
from modules.report_generator import generate_pdf_report

# ============================================================
# APP SETUP
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'resume_matcher_secret_key_2024')

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/reports', exist_ok=True)

# ============================================================
# EMAIL CONFIGURATION
# ============================================================

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', 're_gWZyYWDq_7wCuEy724RRjApofsrKBd9SB')
APP_URL        = os.environ.get('APP_URL', 'https://ai-resumeiq.onrender.com')

with app.app_context():
    init_db()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_verification_email(to_email, username, token):
    """Send a verification email via Resend API (HTTPS — works on Render free plan)."""
    verify_url = f"{APP_URL}/verify-email/{token}"

    html = f"""
    <html>
    <body style="font-family:Inter,Arial,sans-serif; background:#0f0f1a; color:#e2e8f0; padding:40px;">
        <div style="max-width:520px; margin:0 auto; background:#1a1a2e; border-radius:16px;
                    border:1px solid rgba(108,99,255,0.3); padding:40px;">
            <div style="text-align:center; margin-bottom:30px;">
                <h2 style="background:linear-gradient(135deg,#6c63ff,#3b82f6);
                           -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                           font-size:1.8rem; margin:0;">🧠 AI ResumeIQ</h2>
                <p style="color:#a0aec0; margin-top:8px;">Email Verification</p>
            </div>
            <p style="color:#e2e8f0;">Hi <strong style="color:#a78bfa;">{username}</strong>,</p>
            <p style="color:#a0aec0;">Thanks for signing up! Please verify your email address to activate your account.</p>
            <div style="text-align:center; margin:30px 0;">
                <a href="{verify_url}"
                   style="background:linear-gradient(135deg,#6c63ff,#3b82f6);
                          color:white; padding:14px 36px; border-radius:12px;
                          text-decoration:none; font-weight:600; font-size:1rem;
                          display:inline-block;">
                    ✅ Verify My Email
                </a>
            </div>
            <p style="color:#475569; font-size:0.85rem;">
                This link expires in <strong>24 hours</strong>.<br>
                If you didn't create an account, ignore this email.
            </p>
            <hr style="border-color:rgba(255,255,255,0.08); margin:24px 0;">
            <p style="color:#475569; font-size:0.75rem; text-align:center;">
                Developed by Naik Mohammed Fawaz | B.Tech CSE-DS, SREC Nandyal
            </p>
        </div>
    </body>
    </html>
    """

    payload = json.dumps({
        'from': 'AI ResumeIQ <onboarding@resend.dev>',
        'to': [to_email],
        'subject': '✅ Verify your AI ResumeIQ Account',
        'html': html
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"✅ Verification email sent to {to_email}")
            return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_email_async(to_email, username, token):
    """Send email in a background thread so it doesn't block the request."""
    thread = threading.Thread(target=send_verification_email, args=(to_email, username, token))
    thread.daemon = True
    thread.start()


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})

        conn = get_db()
        cur  = conn.cursor()

        # Check if email already exists
        cur.execute('SELECT id, is_verified FROM users WHERE email = %s', (email,))
        existing = cur.fetchone()

        if existing:
            if existing['is_verified']:
                cur.close(); conn.close()
                return jsonify({'success': False, 'message': 'Email already registered. Please login.'})
            else:
                # Resend verification email
                token = secrets.token_urlsafe(32)
                expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
                cur.execute(
                    'UPDATE users SET verify_token=%s, token_expires=%s WHERE email=%s',
                    (token, expires_at, email)
                )
                conn.commit()
                cur.close(); conn.close()
                send_email_async(email, username, token)   # ✅ background
                return jsonify({'success': True, 'message': 'Verification email resent! Please check your inbox.'})

        # Generate verification token
        token      = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()

        cur.execute(
            '''INSERT INTO users (username, email, password, is_verified, verify_token, token_expires, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
            (username, email, password, False, token, expires_at, datetime.now().isoformat())
        )
        conn.commit()
        cur.close(); conn.close()

        # Send verification email in background — won't block/timeout
        send_email_async(email, username, token)   # ✅ background

        return jsonify({'success': True,
                        'message': f'Account created! A verification email has been sent to {email}. Please check your inbox.'})

    return render_template('signup.html')


@app.route('/verify-email/<token>')
def verify_email(token):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute('SELECT * FROM users WHERE verify_token = %s', (token,))
    user = cur.fetchone()

    if not user:
        cur.close(); conn.close()
        return render_template('verify_result.html',
                               success=False,
                               message='Invalid or expired verification link.')

    # Check if token is expired
    if datetime.now() > datetime.fromisoformat(user['token_expires']):
        cur.close(); conn.close()
        return render_template('verify_result.html',
                               success=False,
                               message='Verification link has expired. Please signup again.')

    # Mark as verified
    cur.execute(
        'UPDATE users SET is_verified=%s, verify_token=%s WHERE id=%s',
        (True, None, user['id'])
    )
    conn.commit()
    cur.close(); conn.close()

    return render_template('verify_result.html',
                           success=True,
                           message=f'Email verified successfully! Welcome, {user["username"]}!')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        cur  = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cur.fetchone()
        cur.close(); conn.close()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'})

        # Check if email is verified
        if not user['is_verified']:
            return jsonify({'success': False,
                            'message': '⚠️ Please verify your email first. Check your inbox for the verification link.'})

        session['user_id']  = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'redirect': '/dashboard'})

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        'SELECT * FROM analyses WHERE user_id = %s ORDER BY created_at DESC LIMIT 5',
        (session['user_id'],)
    )
    analyses = cur.fetchall()
    cur.close(); conn.close()

    return render_template('dashboard.html', username=session['username'], analyses=analyses)


@app.route('/analyzer')
def analyzer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analyzer.html', username=session['username'])


@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401

    job_description = request.form.get('job_description', '').strip()
    if not job_description:
        return jsonify({'error': 'Please enter a job description'}), 400

    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400

    file = request.files['resume']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF and DOCX files are allowed'}), 400

    filename  = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = f"{timestamp}_{filename}"
    filepath  = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    resume_text = extract_text_from_file(filepath)
    if not resume_text:
        return jsonify({'error': 'Could not read the resume file'}), 400

    resume_skills = extract_skills(resume_text)
    jd_skills     = extract_skills(job_description)

    matched_skills = list(set([s.lower() for s in resume_skills]).intersection(
                     set([s.lower() for s in jd_skills])))
    missing_skills = list(set([s.lower() for s in jd_skills]) -
                     set([s.lower() for s in resume_skills]))

    similarity  = calculate_similarity(resume_text, job_description)
    skill_ratio = (len(matched_skills) / max(len(jd_skills), 1)) * 100
    ats_score   = round((similarity * 0.6) + (skill_ratio * 0.4), 2)

    career_suggestions = get_career_suggestions(matched_skills, missing_skills)
    resume_tips        = get_resume_tips(ats_score, missing_skills)

    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        '''INSERT INTO analyses
           (user_id, resume_filename, ats_score, matched_skills, missing_skills,
            career_suggestions, resume_tips, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
        (session['user_id'], filename, ats_score,
         json.dumps(matched_skills), json.dumps(missing_skills),
         json.dumps(career_suggestions), json.dumps(resume_tips),
         datetime.now().isoformat())
    )
    analysis_id = cur.fetchone()['id']
    conn.commit()
    cur.close(); conn.close()

    return jsonify({
        'success':             True,
        'analysis_id':         analysis_id,
        'ats_score':           ats_score,
        'matched_skills':      matched_skills,
        'missing_skills':      missing_skills,
        'career_suggestions':  career_suggestions,
        'resume_tips':         resume_tips,
        'similarity_score':    round(similarity, 2),
        'skill_match_percent': round(skill_ratio, 2)
    })


@app.route('/api/rank-resumes', methods=['POST'])
def rank_resumes():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401

    job_description = request.form.get('job_description', '').strip()
    files = request.files.getlist('resumes')

    if len(files) < 2:
        return jsonify({'error': 'Please upload at least 2 resumes'}), 400

    results = []
    for file in files:
        if file and allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath  = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
            file.save(filepath)

            resume_text = extract_text_from_file(filepath)
            if resume_text:
                score       = calculate_similarity(resume_text, job_description)
                res_skills  = extract_skills(resume_text)
                jd_skills   = extract_skills(job_description)
                matched     = set([s.lower() for s in res_skills]).intersection(
                              set([s.lower() for s in jd_skills]))
                skill_ratio = (len(matched) / max(len(jd_skills), 1)) * 100
                final       = round((score * 0.6) + (skill_ratio * 0.4), 2)
                results.append({
                    'name':           file.filename,
                    'score':          final,
                    'matched_skills': list(matched),
                    'skill_percent':  round(skill_ratio, 2)
                })

    results.sort(key=lambda x: x['score'], reverse=True)
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return jsonify({'success': True, 'rankings': results})


@app.route('/admin')
def admin():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))

    conn = get_db()
    cur  = conn.cursor()
    cur.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cur.fetchall()
    cur.execute(
        'SELECT a.*, u.username FROM analyses a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC'
    )
    analyses = cur.fetchall()
    cur.close(); conn.close()

    total_users    = len(users)
    total_analyses = len(analyses)
    avg_score      = round(sum(a['ats_score'] for a in analyses) / len(analyses), 1) if analyses else 0

    return render_template('admin.html', users=users, analyses=analyses,
                           total_users=total_users, total_analyses=total_analyses,
                           avg_score=avg_score)


@app.route('/api/download-report/<int:analysis_id>')
def download_report(analysis_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur  = conn.cursor()
    cur.execute('SELECT * FROM analyses WHERE id = %s AND user_id = %s',
                (analysis_id, session['user_id']))
    analysis = cur.fetchone()
    cur.close(); conn.close()

    if not analysis:
        return 'Analysis not found', 404

    pdf_path = generate_pdf_report(analysis, session['username'])
    return send_file(pdf_path, as_attachment=True,
                     download_name=f'resume_report_{analysis_id}.pdf')


@app.route('/api/history')
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        'SELECT * FROM analyses WHERE user_id = %s ORDER BY created_at DESC',
        (session['user_id'],)
    )
    analyses = cur.fetchall()
    cur.close(); conn.close()

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
# CAREER & TIPS HELPERS
# ============================================================

def get_career_suggestions(matched_skills, missing_skills):
    all_skills = set(matched_skills + missing_skills)
    careers = []

    if any(s in all_skills for s in ['python', 'machine learning', 'tensorflow', 'pytorch', 'data science']):
        careers.append({'title': '🤖 Machine Learning Engineer', 'match': 'High',
            'description': 'Build AI/ML models for real-world applications',
            'next_steps': 'Learn Deep Learning, Computer Vision, NLP'})

    if any(s in all_skills for s in ['sql', 'pandas', 'numpy', 'tableau', 'power bi', 'statistics']):
        careers.append({'title': '📊 Data Analyst / Data Scientist', 'match': 'High',
            'description': 'Analyze data and create business insights',
            'next_steps': 'Learn Advanced Statistics, A/B Testing, Storytelling'})

    if any(s in all_skills for s in ['javascript', 'react', 'html', 'css', 'node']):
        careers.append({'title': '🌐 Full Stack Web Developer', 'match': 'High',
            'description': 'Build complete web applications',
            'next_steps': 'Learn TypeScript, Cloud Deployment, Docker'})

    if any(s in all_skills for s in ['aws', 'docker', 'kubernetes', 'devops', 'linux']):
        careers.append({'title': '☁️ DevOps / Cloud Engineer', 'match': 'Medium',
            'description': 'Manage cloud infrastructure and CI/CD pipelines',
            'next_steps': 'Get AWS/Azure certifications'})

    if any(s in all_skills for s in ['nlp', 'bert', 'transformers', 'llm', 'gpt']):
        careers.append({'title': '🧠 NLP / AI Research Engineer', 'match': 'High',
            'description': 'Work on language models and AI research',
            'next_steps': 'Read research papers, contribute to Hugging Face'})

    if not careers:
        careers.append({'title': '💻 Software Developer', 'match': 'Medium',
            'description': 'Build software applications across various domains',
            'next_steps': 'Strengthen core programming skills and pick a specialization'})

    return careers[:3]


def get_resume_tips(score, missing_skills):
    tips = []
    if score < 30:
        tips.extend([
            '🔴 Your resume needs significant improvement. Focus on adding relevant keywords.',
            '📝 Rewrite your resume to match the job description more closely.',
            '🎯 Add a strong summary section targeting this specific role.'])
    elif score < 60:
        tips.extend([
            '🟡 Your resume is a partial match. Add more relevant skills.',
            '📊 Use numbers to quantify achievements (e.g., "Improved performance by 30%").',
            '🔑 Include action verbs like: Developed, Implemented, Designed, Led.'])
    else:
        tips.extend([
            '🟢 Great resume! A few tweaks will make it perfect.',
            '✨ Make sure your LinkedIn profile matches your resume.',
            '🌟 Add links to GitHub projects or portfolio.'])

    if missing_skills:
        tips.append(f'📚 Learn these in-demand skills: {", ".join(missing_skills[:3])}')
        tips.append('🏆 Add relevant certifications (Coursera, Udemy, Google) to fill skill gaps.')

    tips.append('📄 Keep your resume to 1-2 pages maximum.')
    tips.append('🎨 Use a clean, ATS-friendly format with no graphics or tables.')
    return tips


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)