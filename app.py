# ============================================================
# app.py — The BRAIN of your project (Flask Backend)
# ============================================================

from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

from modules.nlp_processor import extract_text_from_file, extract_skills, calculate_similarity
from modules.database import init_db, get_db
from modules.report_generator import generate_pdf_report

# ============================================================
# APP SETUP
# ============================================================

app = Flask(__name__)
app.secret_key = 'resume_matcher_secret_key_2024'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ IMPORTANT FIX FOR RENDER (create folder automatically)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

with app.app_context():
    init_db()

# ============================================================
# HELPER FUNCTION
# ============================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyzer')
def analyzer():
    return render_template('analyzer.html')


# ============================================================
# PROCESS RESUME (MAIN API)
# ============================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_resume():

    job_description = request.form.get('job_description', '').strip()
    if not job_description:
        return jsonify({'error': 'Please enter a job description'}), 400

    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF and DOCX files are allowed'}), 400

    # Save file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract text
    resume_text = extract_text_from_file(filepath)
    if not resume_text:
        return jsonify({'error': 'Could not read the resume file'}), 400

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)

    similarity_score = calculate_similarity(resume_text, job_description)

    resume_skills_set = set([s.lower() for s in resume_skills])
    jd_skills_set = set([s.lower() for s in jd_skills])

    matched_skills = list(resume_skills_set.intersection(jd_skills_set))
    missing_skills = list(jd_skills_set.difference(resume_skills_set))

    if len(jd_skills_set) > 0:
        skill_match_ratio = len(matched_skills) / len(jd_skills_set) * 100
    else:
        skill_match_ratio = 0

    final_score = round((similarity_score * 0.6) + (skill_match_ratio * 0.4), 2)
    final_score = min(final_score, 100)

    db = get_db()
    db.execute(
        '''INSERT INTO analyses
           (resume_filename, ats_score, matched_skills, missing_skills,
            job_description, created_at)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (
            filename,
            final_score,
            json.dumps(matched_skills),
            json.dumps(missing_skills),
            job_description[:500],
            datetime.now().isoformat()
        )
    )
    db.commit()

    return jsonify({
        'success': True,
        'ats_score': final_score,
        'similarity_score': round(similarity_score, 2),
        'skill_match_percent': round(skill_match_ratio, 2),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'resume_filename': filename
    })


# ============================================================
# RUN APP
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)