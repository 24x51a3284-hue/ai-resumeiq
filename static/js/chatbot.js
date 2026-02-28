// ============================================================
// chatbot.js — AI Assistant Chatbot
// Works on all pages of the project
// ============================================================

// ---- Inject chatbot CSS ----
const chatStyle = document.createElement('style');
chatStyle.textContent = `
#chatbot-container { position: fixed; bottom: 30px; right: 30px; z-index: 9999; }
#chat-toggle {
    width: 60px; height: 60px; border-radius: 50%;
    background: linear-gradient(135deg, #6c63ff, #3b82f6);
    border: none; color: white; font-size: 1.5rem;
    cursor: pointer; box-shadow: 0 8px 25px rgba(108,99,255,0.5);
    transition: transform 0.2s;
    display: flex; align-items: center; justify-content: center;
}
#chat-toggle:hover { transform: scale(1.1); }
#chat-window {
    position: absolute; bottom: 75px; right: 0;
    width: 320px; height: 440px;
    background: #131428; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px; overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    display: flex; flex-direction: column;
    animation: chatSlideIn 0.3s ease;
}
@keyframes chatSlideIn {
    from { opacity:0; transform: translateY(20px) scale(0.95); }
    to   { opacity:1; transform: translateY(0) scale(1); }
}
#chat-header {
    padding: 14px 16px;
    background: rgba(108,99,255,0.15);
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex; justify-content: space-between; align-items: center;
    color: white;
}
#chat-messages {
    flex: 1; overflow-y: auto; padding: 16px;
    display: flex; flex-direction: column; gap: 10px;
}
#chat-messages::-webkit-scrollbar { width: 4px; }
#chat-messages::-webkit-scrollbar-thumb { background: rgba(108,99,255,0.4); border-radius: 2px; }
.bot-msg {
    background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.2);
    color: #e2e8f0; padding: 10px 14px;
    border-radius: 14px 14px 14px 4px;
    font-size: 0.85rem; line-height: 1.5;
    max-width: 85%; align-self: flex-start;
}
.user-msg {
    background: linear-gradient(135deg, #6c63ff, #3b82f6);
    color: white; padding: 10px 14px;
    border-radius: 14px 14px 4px 14px;
    font-size: 0.85rem; line-height: 1.5;
    max-width: 85%; align-self: flex-end;
}
.typing-msg {
    background: rgba(108,99,255,0.1);
    border: 1px solid rgba(108,99,255,0.15);
    color: #a0aec0; padding: 10px 14px;
    border-radius: 14px 14px 14px 4px;
    font-size: 0.85rem; align-self: flex-start;
}
#chat-input-area {
    padding: 12px; border-top: 1px solid rgba(255,255,255,0.08);
    display: flex; gap: 8px; background: #131428;
}
#chat-input {
    flex: 1; background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 8px 12px;
    color: white; font-size: 0.85rem; outline: none;
}
#chat-input:focus { border-color: #6c63ff; }
#chat-input::placeholder { color: #4a5568; }
#chat-input-area button {
    background: linear-gradient(135deg, #6c63ff, #3b82f6);
    border: none; border-radius: 10px;
    width: 36px; height: 36px; color: white;
    cursor: pointer; transition: transform 0.2s;
    display: flex; align-items: center; justify-content: center;
}
#chat-input-area button:hover { transform: scale(1.1); }
`;
document.head.appendChild(chatStyle);

// ---- Toggle chatbot open/close ----
function toggleChat() {
    const win  = document.getElementById('chat-window');
    const icon = document.getElementById('chat-icon');
    if (!win) return;
    const open = win.style.display === 'none' || win.style.display === '';
    win.style.display = open ? 'flex' : 'none';
    if (open) win.style.flexDirection = 'column';
    icon.className = open ? 'fas fa-times' : 'fas fa-robot';
}

function handleChatKey(e) {
    if (e.key === 'Enter') sendMessage();
}

// ---- FAQ Knowledge Base ----
const faqs = [
    { keys: ['ats','score','mean','what is ats'],
      ans: '🎯 <b>ATS Score</b> shows how well your resume matches a job.<br><br>• <b>75-100%</b> = Excellent 🟢<br>• <b>50-74%</b> = Good 🟡<br>• <b>25-49%</b> = Average 🟠<br>• <b>0-24%</b> = Low 🔴<br><br>Formula: (TF-IDF × 60%) + (Skill Match × 40%)' },
    { keys: ['upload','resume','how','pdf','docx'],
      ans: '📄 <b>How to upload:</b><br><br>1. Click "Analyze Resume" in sidebar<br>2. Drag & drop your PDF or DOCX<br>3. Paste the job description<br>4. Click "Analyze with AI" 🚀' },
    { keys: ['skill gap','missing','skill'],
      ans: '🔍 <b>Skill Gap Analysis:</b><br><br>✅ <b>Matched</b> = Skills you have<br>❌ <b>Missing</b> = Skills you need<br><br>Learn missing skills on Coursera, Udemy, or YouTube!' },
    { keys: ['tfidf','tf-idf','cosine','similarity','algorithm'],
      ans: '🧠 <b>How AI works:</b><br><br><b>TF-IDF</b> converts text to numbers<br><b>Cosine Similarity</b> compares resume vs job description<br><br>Score 1.0 = perfect match, 0.0 = no match!' },
    { keys: ['improve','tip','better','resume'],
      ans: '💡 <b>Resume Tips:</b><br><br>1. Add keywords from job description<br>2. Quantify achievements (e.g. "improved by 30%")<br>3. Keep it 1-2 pages<br>4. Use action verbs (Built, Designed, Led)<br>5. Add GitHub/LinkedIn links<br>6. No graphics or tables!' },
    { keys: ['career','suggest','path','job','recommend'],
      ans: '🚀 <b>Career Paths:</b><br><br>🤖 Python + ML → ML Engineer<br>📊 SQL + Pandas → Data Analyst<br>🌐 React + Node → Full Stack Dev<br>☁️ AWS + Docker → DevOps Engineer<br>🧠 BERT + NLP → AI Engineer' },
    { keys: ['rank','multiple','compare'],
      ans: '🏆 <b>Resume Ranking:</b><br><br>1. Click "Rank Multiple Resumes" tab<br>2. Upload 2+ resumes<br>3. Paste job description<br>4. Click "Rank Resumes"<br><br>See all resumes ranked with scores!' },
    { keys: ['pdf','report','download'],
      ans: '📥 <b>Download Report:</b><br><br>After analyzing:<br>1. Scroll down in results<br>2. Click "Download PDF Report"<br>3. Professional PDF downloads automatically!' },
    { keys: ['login','signup','account','register','password'],
      ans: '🔑 <b>Account Help:</b><br><br>• Sign Up → Click "Get Started Free"<br>• Login → Use your email & password<br>• All analysis history is saved automatically!' },
    { keys: ['hello','hi','hey','hii','namaste','good morning','good evening'],
      ans: '👋 Hello! I\'m your AI Assistant!<br><br>I can help with:<br>• Using the analyzer<br>• Understanding ATS score<br>• Resume tips<br>• Career guidance<br><br>What would you like to know?' },
    { keys: ['who made','creator','developer','built','created','fawaz','nmd'],
      ans: '👨‍💻 <b>Project Details:</b><br><br>Developed by <b>NMD FAWAZ</b><br>B.Tech CSE (Data Science) — SREC<br><br>Guided by:<br><b>Mrs. K. Salama Khatoon, M.Tech</b><br>Asst. Professor, Dept. CSE(DS), SREC 🎓' },
    { keys: ['admin','dashboard','panel'],
      ans: '⚙️ <b>Admin Panel:</b><br><br>Shows all users, analyses, scores & charts.<br><br>Login with admin credentials to access it.' },
    { keys: ['thank','thanks','bye','goodbye','ok'],
      ans: '😊 You\'re welcome! Best of luck with your job search! 🎯<br><br>Remember: Right skills + Great resume = Dream Job! 🚀' },
    { keys: ['history','previous','saved','past'],
      ans: '📋 <b>View History:</b><br><br>1. Go to Dashboard<br>2. Scroll down to "Recent Analyses"<br>3. See all your past analyses<br>4. Download any report as PDF!' },
];

function getBotResponse(msg) {
    const lower = msg.toLowerCase();
    for (const faq of faqs) {
        if (faq.keys.some(k => lower.includes(k))) {
            return faq.ans;
        }
    }
    return `🤔 I'm not sure about that.<br><br>Try asking:<br>• "What is ATS score?"<br>• "How to upload resume?"<br>• "How to improve my resume?"<br>• "What is skill gap analysis?"`;
}

async function sendMessage() {
    const input    = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    const text     = input.value.trim();
    if (!text) return;

    // User message
    const userDiv = document.createElement('div');
    userDiv.className = 'user-msg';
    userDiv.textContent = text;
    messages.appendChild(userDiv);
    input.value = '';

    // Typing indicator
    const typing = document.createElement('div');
    typing.className = 'typing-msg';
    typing.innerHTML = '<i class="fas fa-ellipsis-h"></i> Thinking...';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    // Delay for realistic feel
    await new Promise(r => setTimeout(r, 700));

    typing.remove();
    const botDiv = document.createElement('div');
    botDiv.className = 'bot-msg';
    botDiv.innerHTML = getBotResponse(text);
    messages.appendChild(botDiv);
    messages.scrollTop = messages.scrollHeight;
}
