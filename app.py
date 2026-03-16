"""
Bullet Brain - Brain Wellness Web Application
Flask backend with audio session management (no login required).
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os

app = Flask(__name__)

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

# ─── Routes ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/enter')
def enter():
    return render_template('enter.html')

@app.route('/focus')
def focus():
    return render_template('focus.html', sessions=SESSIONS['focus'])

@app.route('/relax')
def relax():
    return render_template('relax.html', sessions=SESSIONS['relax'])

@app.route('/sleep')
def sleep():
    return render_template('sleep.html', sessions=SESSIONS['sleep'])

@app.route('/meditation')
def meditation():
    return render_template('meditation.html', sessions=SESSIONS['meditation'])

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# ─── Chatbot API ─────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
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
    app.run(debug=True, host='0.0.0.0', port=5000)
