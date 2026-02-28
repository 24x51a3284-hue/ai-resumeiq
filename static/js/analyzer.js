// ============================================================
// analyzer.js — All JavaScript for the Resume Analyzer page
// Handles: file upload, drag & drop, API calls, chart drawing
// ============================================================

// Track the last analysis ID (for PDF download)
let lastAnalysisId = null;
// Track selected file
let selectedFile = null;
// Reference to Chart.js charts so we can destroy and recreate them
let skillPieChartObj = null;
let simChartObj      = null;
let scoreGaugeObj    = null;
let rankBarChartObj  = null;


// ============================================================
// DRAG & DROP FUNCTIONALITY
// ============================================================

const uploadZone = document.getElementById('uploadZone');
const fileInput  = document.getElementById('resumeFile');

if (uploadZone) {
    // When user drags a file over the zone — add highlight
    uploadZone.addEventListener('dragover', function (e) {
        e.preventDefault();  // Must prevent default to allow drop
        uploadZone.classList.add('drag-over');
    });

    // When user leaves without dropping — remove highlight
    uploadZone.addEventListener('dragleave', function () {
        uploadZone.classList.remove('drag-over');
    });

    // When user drops the file
    uploadZone.addEventListener('drop', function (e) {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');

        // Get the dropped files
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
}

// When user clicks to pick a file
if (fileInput) {
    fileInput.addEventListener('change', function () {
        if (this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    });
}

// Process a selected file
function handleFileSelect(file) {
    // Check file type
    const allowed = ['application/pdf',
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'application/msword'];
    const ext     = file.name.split('.').pop().toLowerCase();

    if (!['pdf', 'docx', 'doc'].includes(ext)) {
        showNotification('❌ Only PDF and DOCX files are allowed', 'danger');
        return;
    }

    // Store file reference
    selectedFile = file;

    // Show the "file selected" bar
    document.getElementById('file-selected').classList.remove('d-none');
    document.getElementById('file-name').textContent = file.name;

    // Visual feedback on upload zone
    uploadZone.style.borderColor     = '#22c55e';
    uploadZone.style.backgroundColor = 'rgba(34,197,94,0.05)';
}

// Remove the selected file
function removeFile() {
    selectedFile = null;
    document.getElementById('file-selected').classList.add('d-none');
    if (fileInput) fileInput.value = '';
    uploadZone.style.borderColor     = '';
    uploadZone.style.backgroundColor = '';
}


// ============================================================
// MAIN ANALYZE FUNCTION
// Called when user clicks "Analyze with AI"
// ============================================================

async function analyzeResume() {
    const jobDesc = document.getElementById('jobDescription').value.trim();

    // ---- Validation ----
    if (!selectedFile) {
        showNotification('❌ Please upload your resume first', 'danger');
        return;
    }
    if (!jobDesc) {
        showNotification('❌ Please paste a job description', 'danger');
        return;
    }
    if (jobDesc.length < 50) {
        showNotification('⚠️ Job description is too short. Add more details for better results.', 'warning');
        return;
    }

    // ---- Show loading state ----
    const btn       = document.getElementById('analyzeBtn');
    const loading   = document.getElementById('loading-state');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    loading.classList.remove('d-none');

    // Cycle through loading messages to look impressive
    const messages = [
        'Extracting text from resume...',
        'Running NLP skill extraction...',
        'Calculating TF-IDF vectors...',
        'Computing cosine similarity...',
        'Generating AI recommendations...'
    ];
    let msgIndex = 0;
    const msgInterval = setInterval(function () {
        document.getElementById('loading-text').textContent = messages[msgIndex % messages.length];
        msgIndex++;
    }, 1000);

    try {
        // ---- Build the form data to send ----
        // FormData is like a bag that holds files and text
        const formData = new FormData();
        formData.append('resume', selectedFile);         // The file
        formData.append('job_description', jobDesc);     // The text

        // ---- Send to Flask backend ----
        // fetch() sends an HTTP request (like submitting a form)
        const response = await fetch('/api/analyze', {
            method: 'POST',    // POST = sending data
            body: formData     // The data to send
        });

        // Parse the JSON response from Flask
        const data = await response.json();

        if (data.error) {
            showNotification('❌ ' + data.error, 'danger');
        } else if (data.success) {
            // Show results
            displayResults(data);
            // Save the analysis ID for the download button
            lastAnalysisId = data.analysis_id;
        }

    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Connection error. Make sure the server is running.', 'danger');
    } finally {
        // Always restore button state (even if there's an error)
        clearInterval(msgInterval);
        loading.classList.add('d-none');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-brain me-2"></i>Analyze with AI';
    }
}


// ============================================================
// DISPLAY RESULTS
// Takes the API response and shows it on the page
// ============================================================

function displayResults(data) {
    // Show the results panel
    const resultsPanel = document.getElementById('results-panel');
    resultsPanel.style.display = 'block';

    // Smooth scroll to results
    resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // ---- 1. Update ATS Score Bar ----
    const score = data.ats_score;
    document.getElementById('score-display').textContent = Math.round(score);

    // Animate the progress bar
    setTimeout(function () {
        document.getElementById('ats-bar').style.width = score + '%';
    }, 200);

    // Change bar color based on score
    const bar = document.getElementById('ats-bar');
    if (score >= 60)      bar.style.background = 'linear-gradient(90deg, #22c55e, #16a34a)';
    else if (score >= 30) bar.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
    else                  bar.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';

    // Score message
    let msg = '';
    if (score >= 75) msg = '🌟 Excellent! Your resume is a strong match.';
    else if (score >= 60) msg = '✅ Good match! A few improvements can make it perfect.';
    else if (score >= 40) msg = '⚠️ Moderate match. Consider adding missing skills.';
    else if (score >= 20) msg = '🔶 Weak match. Significant improvements needed.';
    else                  msg = '🔴 Very low match. Rewrite to match the job description.';
    document.getElementById('score-message').textContent = msg;

    // ---- 2. Score Gauge (Donut Chart) ----
    if (scoreGaugeObj) scoreGaugeObj.destroy();  // Remove old chart first
    const gaugeColor = score >= 60 ? '#22c55e' : score >= 30 ? '#f59e0b' : '#ef4444';
    scoreGaugeObj = new Chart(document.getElementById('scoreGauge'), {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [gaugeColor, 'rgba(255,255,255,0.05)'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '78%',
            responsive: false,
            animation: { animateRotate: true, duration: 1500 },
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });

    // ---- 3. Skill Match Pie Chart ----
    const matchedCount = data.matched_skills.length;
    const missingCount = data.missing_skills.length;
    const totalJDSkills = matchedCount + missingCount;

    if (skillPieChartObj) skillPieChartObj.destroy();
    skillPieChartObj = new Chart(document.getElementById('skillPieChart'), {
        type: 'doughnut',
        data: {
            labels: ['Matched', 'Missing'],
            datasets: [{
                data: [matchedCount, missingCount],
                backgroundColor: ['rgba(34,197,94,0.8)', 'rgba(239,68,68,0.8)'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '65%',
            responsive: false,
            animation: { duration: 1500 },
            plugins: {
                legend: { labels: { color: '#a0aec0', font: { size: 11 } } }
            }
        }
    });

    // Pie chart legend
    document.getElementById('skill-pie-legend').innerHTML =
        `<small class="text-success me-2">✔ ${matchedCount} matched</small>
         <small class="text-danger">✘ ${missingCount} missing</small>`;

    // ---- 4. Similarity Score Chart ----
    if (simChartObj) simChartObj.destroy();
    simChartObj = new Chart(document.getElementById('simChart'), {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [data.similarity_score, 100 - data.similarity_score],
                backgroundColor: ['rgba(59,130,246,0.8)', 'rgba(255,255,255,0.05)'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            responsive: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
    document.getElementById('sim-text').textContent =
        `TF-IDF Cosine Similarity: ${data.similarity_score.toFixed(1)}%`;

    // ---- 5. Matched Skills Tags ----
    const matchedContainer = document.getElementById('matched-skills-container');
    matchedContainer.innerHTML = '';
    if (data.matched_skills.length === 0) {
        matchedContainer.innerHTML = '<p class="text-muted small">No matching skills found. Try adding more relevant keywords.</p>';
    } else {
        data.matched_skills.forEach(function (skill, i) {
            const tag = document.createElement('span');
            tag.className = 'skill-tag skill-tag-matched';
            tag.style.animationDelay = (i * 0.05) + 's';
            tag.textContent = skill;
            matchedContainer.appendChild(tag);
        });
    }

    // ---- 6. Missing Skills Tags (Skill Gap) ----
    const missingContainer = document.getElementById('missing-skills-container');
    missingContainer.innerHTML = '';
    if (data.missing_skills.length === 0) {
        missingContainer.innerHTML = '<p class="text-success small">🎉 No missing skills! Your resume matches all requirements.</p>';
    } else {
        data.missing_skills.forEach(function (skill, i) {
            const tag = document.createElement('span');
            tag.className = 'skill-tag skill-tag-missing';
            tag.style.animationDelay = (i * 0.05) + 's';
            tag.innerHTML = `<i class="fas fa-times me-1" style="font-size:0.7rem"></i>${skill}`;
            missingContainer.appendChild(tag);
        });
    }

    // ---- 7. Career Recommendations ----
    const careerContainer = document.getElementById('career-container');
    careerContainer.innerHTML = '';
    data.career_suggestions.forEach(function (career) {
        const matchColor = career.match === 'High' ? '#22c55e' :
                           career.match === 'Medium' ? '#f59e0b' : '#94a3b8';
        careerContainer.innerHTML += `
            <div class="career-card">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="career-card-title">${career.title}</div>
                    <span style="font-size:0.75rem; color:${matchColor}; font-weight:600;">
                        ${career.match} Match
                    </span>
                </div>
                <div class="career-card-desc">${career.description}</div>
                <div class="career-card-next">
                    <i class="fas fa-arrow-right me-1"></i>Next: ${career.next_steps}
                </div>
            </div>`;
    });

    // ---- 8. Resume Tips ----
    const tipsContainer = document.getElementById('tips-container');
    tipsContainer.innerHTML = '';
    data.tips.forEach(function (tip) {
        tipsContainer.innerHTML += `<div class="tip-item">${tip}</div>`;
    });

    showNotification('✅ Analysis complete!', 'success');
}


// ============================================================
// DOWNLOAD PDF REPORT
// ============================================================

function downloadReport() {
    if (!lastAnalysisId) {
        // Get most recent from URL or local storage
        showNotification('⚠️ Please analyze a resume first', 'warning');
        return;
    }
    window.location.href = `/api/download-report/${lastAnalysisId}`;
}


// ============================================================
// RANK MULTIPLE RESUMES
// ============================================================

function showSelectedFiles() {
    const files    = document.getElementById('multipleFiles').files;
    const listDiv  = document.getElementById('selected-files-list');
    listDiv.innerHTML = '';

    if (files.length < 2) {
        listDiv.innerHTML = '<p class="text-warning small">Please select at least 2 files to rank.</p>';
        return;
    }

    Array.from(files).forEach(function (file, i) {
        listDiv.innerHTML += `
            <div class="file-selected-bar mb-2">
                <i class="fas fa-file-pdf text-danger me-2"></i>
                <span class="small">${i+1}. ${file.name}</span>
            </div>`;
    });
}

async function rankResumes() {
    const files   = document.getElementById('multipleFiles').files;
    const jobDesc = document.getElementById('rankJobDesc').value.trim();

    if (files.length < 2) {
        showNotification('❌ Please select at least 2 resume files', 'danger'); return;
    }
    if (!jobDesc) {
        showNotification('❌ Please paste a job description', 'danger'); return;
    }

    showNotification('⏳ Ranking resumes...', 'info');

    const formData = new FormData();
    Array.from(files).forEach(function (file) {
        formData.append('resumes', file);
    });
    formData.append('job_description', jobDesc);

    try {
        const response = await fetch('/api/rank-resumes', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            displayRankings(data.rankings);
        } else {
            showNotification('❌ ' + (data.error || 'Ranking failed'), 'danger');
        }
    } catch (err) {
        showNotification('❌ Connection error', 'danger');
    }
}

function displayRankings(rankings) {
    // Show the results panel
    document.getElementById('rank-results').style.display = 'block';

    const content = document.getElementById('rank-results-content');
    content.innerHTML = '';

    const medals    = ['🥇', '🥈', '🥉'];
    const rankClass = ['rank-1', 'rank-2', 'rank-3', 'rank-other'];

    rankings.forEach(function (r, i) {
        const cls  = rankClass[Math.min(i, 3)];
        const medal = medals[i] || `#${r.rank}`;
        content.innerHTML += `
            <div class="rank-card">
                <div class="rank-badge ${cls}">${medal}</div>
                <div class="flex-grow-1">
                    <div class="fw-semibold text-white">${r.name}</div>
                    <div class="text-muted small">
                        ${r.matched_skills.slice(0,4).join(', ')}${r.matched_skills.length > 4 ? '...' : ''}
                    </div>
                </div>
                <div class="text-end">
                    <div class="fw-bold" style="color:${r.score >= 60 ? '#22c55e' : r.score >= 30 ? '#f59e0b' : '#ef4444'}">
                        ${r.score.toFixed(1)}%
                    </div>
                    <div class="text-muted" style="font-size:11px">ATS Score</div>
                </div>
            </div>`;
    });

    // Bar chart for comparison
    if (rankBarChartObj) rankBarChartObj.destroy();
    const colors = rankings.map(function (_, i) {
        return i === 0 ? '#fbbf24' : i === 1 ? '#9ca3af' : i === 2 ? '#92400e' : '#6c63ff';
    });

    rankBarChartObj = new Chart(document.getElementById('rankBarChart'), {
        type: 'bar',
        data: {
            labels: rankings.map(r => r.name.substring(0, 20)),
            datasets: [{
                label: 'ATS Score (%)',
                data: rankings.map(r => r.score),
                backgroundColor: colors,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#a0aec0' } }
            },
            scales: {
                y: {
                    min: 0, max: 100,
                    ticks: { color: '#a0aec0' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                x: {
                    ticks: { color: '#a0aec0', maxRotation: 30 },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });
}


// ============================================================
// NOTIFICATION HELPER
// Shows a toast-like notification
// ============================================================

function showNotification(message, type) {
    // Remove old notification if any
    const existing = document.getElementById('notification-toast');
    if (existing) existing.remove();

    // Create notification element
    const toast = document.createElement('div');
    toast.id    = 'notification-toast';

    // Map type to bootstrap colors
    const bgMap = {
        success: 'rgba(34,197,94,0.15)',
        danger:  'rgba(239,68,68,0.15)',
        warning: 'rgba(245,158,11,0.15)',
        info:    'rgba(59,130,246,0.15)'
    };
    const borderMap = {
        success: 'rgba(34,197,94,0.4)',
        danger:  'rgba(239,68,68,0.4)',
        warning: 'rgba(245,158,11,0.4)',
        info:    'rgba(59,130,246,0.4)'
    };
    const textMap = {
        success: '#4ade80',
        danger:  '#f87171',
        warning: '#fbbf24',
        info:    '#60a5fa'
    };

    toast.style.cssText = `
        position: fixed;
        top: 80px; right: 20px;
        z-index: 9999;
        background: ${bgMap[type] || bgMap.info};
        border: 1px solid ${borderMap[type] || borderMap.info};
        color: ${textMap[type] || textMap.info};
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 500;
        backdrop-filter: blur(20px);
        animation: slideInRight 0.3s ease;
        max-width: 350px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    `;
    toast.textContent = message;

    // Add animation style
    if (!document.getElementById('toast-style')) {
        const style = document.createElement('style');
        style.id    = 'toast-style';
        style.textContent = `
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(100px); }
                to   { opacity: 1; transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(function () {
        toast.style.opacity   = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s';
        setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
}
