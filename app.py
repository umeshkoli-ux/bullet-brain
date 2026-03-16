"""
Bullet Brain - Brain Wellness Web Application
Flask backend with SQLite user authentication and audio session management.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import os
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bullet-brain-secret-key-2024')

# ─── Database Configuration ────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), 'bullet_brain.db')

def get_db():
    """Open a SQLite connection with row-factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables on first run."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    print("Database ready:", DB_PATH)

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Audio Session Data ─────────────────────────────────────────────────────────
SESSIONS = {
    'focus': [
        {'title': 'Deep Focus Flow',     'description': 'Binaural beats for laser-sharp concentration', 'file': 'focus_binaural.mp3',    'duration': '30 min'},
        {'title': 'Alpha Wave Study',    'description': 'Alpha frequency waves to enhance learning',    'file': 'focus_alpha.mp3',        'duration': '20 min'},
        {'title': 'Brown Noise Clarity', 'description': 'Smooth brown noise for distraction-free work', 'file': 'focus_brownnoise.mp3',   'duration': '60 min'},
        {'title': 'Focus Flow Beats',    'description': 'Rhythmic beats to keep your mind engaged',     'file': 'focus_beats.mp3',        'duration': '45 min'},
    ],
    'relax': [
        {'title': 'Ocean Calm',          'description': 'Gentle ocean waves for total relaxation',      'file': 'relax_ocean.mp3',        'duration': '30 min'},
        {'title': 'Forest Serenity',     'description': 'Birds and rustling leaves in a calm forest',  'file': 'relax_forest.mp3',       'duration': '25 min'},
        {'title': 'Rain Therapy',        'description': 'Soft rain sounds to ease tension',             'file': 'relax_rain.mp3',         'duration': '40 min'},
        {'title': 'Theta Relaxation',    'description': 'Theta waves to melt away stress',             'file': 'relax_theta.mp3',        'duration': '35 min'},
    ],
    'sleep': [
        {'title': 'Delta Deep Sleep',    'description': 'Delta waves to guide you into deep sleep',     'file': 'sleep_delta.mp3',        'duration': '8 hr'},
        {'title': 'White Noise Cradle',  'description': 'Pure white noise for uninterrupted sleep',     'file': 'sleep_whitenoise.mp3',   'duration': '8 hr'},
        {'title': 'Night Forest Lullaby','description': 'Crickets and wind for peaceful nights',        'file': 'sleep_forest.mp3',       'duration': '6 hr'},
        {'title': 'Hypnotic Rain',       'description': 'Steady rain to ease you into slumber',         'file': 'sleep_rain.mp3',         'duration': '7 hr'},
    ],
    'meditation': [
        {'title': 'Mindful Breath',      'description': 'Guided breathing meditation for beginners',    'file': 'med_breath.mp3',         'duration': '10 min'},
        {'title': 'Body Scan Journey',   'description': 'Full-body awareness and release session',      'file': 'med_bodyscan.mp3',       'duration': '20 min'},
        {'title': 'Loving Kindness',     'description': 'Metta meditation for compassion & peace',      'file': 'med_lovingkindness.mp3', 'duration': '15 min'},
        {'title': 'Visualization Oasis', 'description': 'Guided imagery to find your inner calm',       'file': 'med_visualization.mp3',  'duration': '25 min'},
    ],
}

# ─── Auth Routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND password_hash = ?",
                (email, hash_password(password))
            ).fetchone()

        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['email']    = user['email']
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not all([username, email, password, confirm]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, hash_password(password))
                )
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
            return render_template('register.html')

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Main App Routes ─────────────────────────────────────────────────────────────

@app.route('/home')
@login_required
def home():
    return render_template('home.html', username=session.get('username'))

@app.route('/enter')
@login_required
def enter():
    return render_template('enter.html', username=session.get('username'))

@app.route('/focus')
@login_required
def focus():
    return render_template('focus.html', sessions=SESSIONS['focus'], username=session.get('username'))

@app.route('/relax')
@login_required
def relax():
    return render_template('relax.html', sessions=SESSIONS['relax'], username=session.get('username'))

@app.route('/sleep')
@login_required
def sleep():
    return render_template('sleep.html', sessions=SESSIONS['sleep'], username=session.get('username'))

@app.route('/meditation')
@login_required
def meditation():
    return render_template('meditation.html', sessions=SESSIONS['meditation'], username=session.get('username'))

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html', username=session.get('username'))

# ─── Chatbot API ─────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """Rule-based chatbot — detects mood keywords and recommends a session."""
    data    = request.get_json()
    message = data.get('message', '').lower().strip()
    step    = data.get('step', 0)

    focus_kw      = ['distracted', 'focus', 'concentrate', 'study', 'work', 'productive', 'scattered', 'mind wander']
    relax_kw      = ['stressed', 'stress', 'anxious', 'anxiety', 'tense', 'worried', 'overwhelmed', 'nervous', 'relax']
    sleep_kw      = ['tired', 'sleepy', 'exhausted', 'insomnia', 'sleep', "can't sleep", 'fatigue', 'drowsy']
    meditation_kw = ['empty', 'lost', 'sad', 'disconnected', 'meditate', 'mindful', 'peaceful', 'calm', 'inner peace']

    def detect_mood(text):
        for kw in sleep_kw:
            if kw in text: return 'sleep'
        for kw in relax_kw:
            if kw in text: return 'relax'
        for kw in focus_kw:
            if kw in text: return 'focus'
        for kw in meditation_kw:
            if kw in text: return 'meditation'
        return None

    mood_msgs = {
        'focus':     "It sounds like you need to sharpen your focus. Let me guide you to our Focus sessions!",
        'relax':     "I hear you — let's help you unwind. Our Relax sessions will melt that stress away.",
        'sleep':     "You deserve some rest. Our Sleep sessions will have you drifting off in no time.",
        'meditation':"A little mindfulness can do wonders. Let me take you to our Meditation sessions.",
    }

    if step == 0:
        return jsonify({
            'reply':    "Hi there! I'm Brain Bot 🧠 I'm here to help you find the perfect session.\n\nHow are you feeling right now?",
            'step':     1,
            'mood':     None,
            'redirect': None,
        })

    mood = detect_mood(message)

    if mood:
        return jsonify({
            'reply':    mood_msgs[mood],
            'step':     step + 1,
            'mood':     mood,
            'redirect': url_for(mood),
        })
    else:
        return jsonify({
            'reply':    "I want to find the right session for you. Are you feeling stressed, distracted, tired, or looking for inner peace?",
            'step':     step,
            'mood':     None,
            'redirect': None,
        })

# ─── Run ─────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
