"""
Bullet Brain - Brain Wellness Web Application
Flask backend with MySQL user authentication and audio session management.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
import hashlib
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bullet-brain-secret-key-2024')

# ─── Database Configuration ────────────────────────────────────────────────────
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'bullet_brain')
}

def get_db_connection():
    """Create and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        # Connect without specifying database first to create it
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(256) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
    except Error as e:
        print(f"Database initialization error: {e}")

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def login_required(f):
    """Decorator to protect routes that require authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ─── Audio Session Data ─────────────────────────────────────────────────────────
# Audio session definitions — filenames must exist in static/audio/
SESSIONS = {
    'focus': [
        {'title': 'Deep Focus Flow',       'description': 'Binaural beats for laser-sharp concentration', 'file': 'focus_binaural.mp3',    'duration': '30 min'},
        {'title': 'Alpha Wave Study',       'description': 'Alpha frequency waves to enhance learning',   'file': 'focus_alpha.mp3',        'duration': '20 min'},
        {'title': 'Brown Noise Clarity',    'description': 'Smooth brown noise for distraction-free work', 'file': 'focus_brownnoise.mp3',  'duration': '60 min'},
        {'title': 'Focus Flow Beats',       'description': 'Rhythmic beats to keep your mind engaged',    'file': 'focus_beats.mp3',        'duration': '45 min'},
    ],
    'relax': [
        {'title': 'Ocean Calm',             'description': 'Gentle ocean waves for total relaxation',     'file': 'relax_ocean.mp3',        'duration': '30 min'},
        {'title': 'Forest Serenity',        'description': 'Birds and rustling leaves in a calm forest',  'file': 'relax_forest.mp3',       'duration': '25 min'},
        {'title': 'Rain Therapy',           'description': 'Soft rain sounds to ease tension',            'file': 'relax_rain.mp3',         'duration': '40 min'},
        {'title': 'Theta Relaxation',       'description': 'Theta waves to melt away stress',            'file': 'relax_theta.mp3',        'duration': '35 min'},
    ],
    'sleep': [
        {'title': 'Delta Deep Sleep',       'description': 'Delta waves to guide you into deep sleep',    'file': 'sleep_delta.mp3',        'duration': '8 hr'},
        {'title': 'White Noise Cradle',     'description': 'Pure white noise for uninterrupted sleep',    'file': 'sleep_whitenoise.mp3',   'duration': '8 hr'},
        {'title': 'Night Forest Lullaby',   'description': 'Crickets and wind for peaceful nights',       'file': 'sleep_forest.mp3',       'duration': '6 hr'},
        {'title': 'Hypnotic Rain',          'description': 'Steady rain to ease you into slumber',        'file': 'sleep_rain.mp3',         'duration': '7 hr'},
    ],
    'meditation': [
        {'title': 'Mindful Breath',         'description': 'Guided breathing meditation for beginners',   'file': 'med_breath.mp3',         'duration': '10 min'},
        {'title': 'Body Scan Journey',      'description': 'Full-body awareness and release session',     'file': 'med_bodyscan.mp3',       'duration': '20 min'},
        {'title': 'Loving Kindness',        'description': 'Metta meditation for compassion & peace',     'file': 'med_lovingkindness.mp3', 'duration': '15 min'},
        {'title': 'Visualization Oasis',    'description': 'Guided imagery to find your inner calm',      'file': 'med_visualization.mp3',  'duration': '25 min'},
    ],
}

# ─── Auth Routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Redirect root to login or home based on session."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again.', 'error')
            return render_template('login.html')

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE email = %s AND password_hash = %s",
                (email, hash_password(password))
            )
            user = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

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
    """Handle new user registration."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Basic validation
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

        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again.', 'error')
            return render_template('register.html')

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hash_password(password))
            )
            conn.commit()
        except mysql.connector.IntegrityError:
            flash('Username or email already exists.', 'error')
            return render_template('register.html')
        finally:
            cursor.close()
            conn.close()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Log the user out and clear session."""
    session.clear()
    return redirect(url_for('login'))

# ─── Main App Routes ─────────────────────────────────────────────────────────────

@app.route('/home')
@login_required
def home():
    """Home page — choose Enter or Ask."""
    return render_template('home.html', username=session.get('username'))

@app.route('/enter')
@login_required
def enter():
    """Mood selection page."""
    return render_template('enter.html', username=session.get('username'))

@app.route('/focus')
@login_required
def focus():
    """Focus audio sessions page."""
    return render_template('focus.html', sessions=SESSIONS['focus'], username=session.get('username'))

@app.route('/relax')
@login_required
def relax():
    """Relax audio sessions page."""
    return render_template('relax.html', sessions=SESSIONS['relax'], username=session.get('username'))

@app.route('/sleep')
@login_required
def sleep():
    """Sleep audio sessions page."""
    return render_template('sleep.html', sessions=SESSIONS['sleep'], username=session.get('username'))

@app.route('/meditation')
@login_required
def meditation():
    """Meditation audio sessions page."""
    return render_template('meditation.html', sessions=SESSIONS['meditation'], username=session.get('username'))

@app.route('/chatbot')
@login_required
def chatbot():
    """AI chatbot page for mood recommendation."""
    return render_template('chatbot.html', username=session.get('username'))

# ─── Chatbot API ─────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """
    Simple rule-based chatbot that recommends a mood session
    based on keywords in the user's message.
    """
    data    = request.get_json()
    message = data.get('message', '').lower().strip()
    step    = data.get('step', 0)

    # Keyword → mood mapping
    focus_keywords     = ['distracted', 'focus', 'concentrate', 'study', 'work', 'productive', 'mind wandering', 'scattered']
    relax_keywords     = ['stressed', 'stress', 'anxious', 'anxiety', 'tense', 'worried', 'overwhelmed', 'nervous', 'relax']
    sleep_keywords     = ['tired', 'sleepy', 'exhausted', 'insomnia', 'sleep', 'can\'t sleep', 'fatigue', 'drowsy']
    meditation_keywords = ['empty', 'lost', 'sad', 'disconnected', 'meditate', 'mindful', 'peaceful', 'calm', 'inner peace']

    # Detect mood from message
    def detect_mood(text):
        for kw in sleep_keywords:
            if kw in text:
                return 'sleep'
        for kw in relax_keywords:
            if kw in text:
                return 'relax'
        for kw in focus_keywords:
            if kw in text:
                return 'focus'
        for kw in meditation_keywords:
            if kw in text:
                return 'meditation'
        return None

    # Conversation flow
    if step == 0:
        response = {
            'reply': "Hi there! I'm Brain Bot 🧠 I'm here to help you find the perfect session. How are you feeling right now?",
            'step': 1,
            'mood': None,
            'redirect': None
        }
    elif step == 1:
        mood = detect_mood(message)
        if mood:
            mood_messages = {
                'focus':     "It sounds like you need to sharpen your focus. Let me guide you to our Focus sessions!",
                'relax':     "I hear you — let's help you unwind. Our Relax sessions will melt that stress away.",
                'sleep':     "You deserve some rest. Our Sleep sessions will have you drifting off in no time.",
                'meditation':'A little mindfulness can do wonders. Let me take you to our Meditation sessions.'
            }
            response = {
                'reply':    mood_messages[mood],
                'step':     2,
                'mood':     mood,
                'redirect': url_for(mood)
            }
        else:
            response = {
                'reply': "I want to make sure I recommend the right session. Are you feeling stressed, distracted, tired, or are you looking for inner peace?",
                'step': 1,
                'mood': None,
                'redirect': None
            }
    elif step == 2:
        mood = detect_mood(message)
        if mood:
            mood_messages = {
                'focus':     "Great! Redirecting you to Focus sessions now.",
                'relax':     "Perfect. Taking you to Relax sessions.",
                'sleep':     "Got it. Sending you to Sleep sessions.",
                'meditation':'Wonderful. Opening your Meditation sessions.'
            }
            response = {
                'reply':    mood_messages[mood],
                'step':     3,
                'mood':     mood,
                'redirect': url_for(mood)
            }
        else:
            response = {
                'reply': "No worries! You can choose manually by going back to the Enter page. Which would you prefer: Focus, Relax, Sleep, or Meditation?",
                'step': 2,
                'mood': None,
                'redirect': None
            }
    else:
        mood = detect_mood(message)
        redirect_url = url_for(mood) if mood else None
        response = {
            'reply':    f"Redirecting you to your {'selected' if mood else 'recommended'} session now!",
            'step':     step + 1,
            'mood':     mood,
            'redirect': redirect_url
        }

    return jsonify(response)

# ─── Run ─────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
