"""
EmoFusion - Mental Health Suggestion Service
Provides emotion-specific wellness tips, helplines, and affirmations.
"""

SUGGESTIONS = {
    "sad": {
        "title": "You seem to be feeling sad 💙",
        "message": "It's okay to feel sad. You are not alone.",
        "tips": [
            "Take 5 deep breaths slowly — inhale 4 counts, exhale 6 counts",
            "Talk to a friend or family member you trust",
            "Write down 3 things you are grateful for today",
            "Go for a short 10 minute walk outside",
            "Listen to your favorite calming music",
            "Drink a glass of water and eat something nourishing",
            "Watch a comforting show or movie",
            "Be gentle with yourself — this feeling will pass"
        ],
        "helplines": [
            {"name": "iCall India", "number": "9152987821"},
            {"name": "Vandrevala Foundation", "number": "1860-2662-345"},
            {"name": "AASRA", "number": "9820466627"},
            {"name": "iCall Whatsapp", "number": "9152987821"}
        ],
        "affirmation": "You are stronger than you think. This moment will pass.",
        "color": "blue",
        "emoji": "💙"
    },
    "fear": {
        "title": "You seem to be feeling anxious 💜",
        "message": "Fear and anxiety are normal. Let us help you feel grounded.",
        "tips": [
            "Try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste",
            "Place both feet flat on the floor and take slow deep breaths",
            "Remind yourself: I am safe right now in this moment",
            "Call or text someone you trust immediately",
            "Avoid caffeine and try chamomile tea instead",
            "Write down exactly what you are afraid of — it helps reduce its power",
            "Do light stretching or yoga for 5 minutes"
        ],
        "helplines": [
            {"name": "iCall India", "number": "9152987821"},
            {"name": "Vandrevala Foundation", "number": "1860-2662-345"},
            {"name": "NIMHANS", "number": "080-46110007"},
            {"name": "Fortis Stress Helpline", "number": "8376804102"}
        ],
        "affirmation": "You have survived every difficult moment so far. You are doing great.",
        "color": "purple",
        "emoji": "💜"
    },
    "angry": {
        "title": "You seem to be feeling angry 🔴",
        "message": "Anger is valid. Let us help you release it safely.",
        "tips": [
            "Step away from the situation for at least 10 minutes before responding",
            "Do 10 jumping jacks or any physical movement to release tension",
            "Breathe in slowly for 4 counts, hold for 4, out for 4 — repeat 5 times",
            "Write down what made you angry without filtering",
            "Splash cold water on your face",
            "Do not make any big decisions while angry — wait 30 minutes",
            "Listen to music that matches then gradually calms your mood"
        ],
        "helplines": [
            {"name": "iCall India", "number": "9152987821"},
            {"name": "Vandrevala Foundation", "number": "1860-2662-345"},
            {"name": "Mann Talks", "number": "8686139139"}
        ],
        "affirmation": "You are in control. You can choose how to respond.",
        "color": "red",
        "emoji": "❤️"
    },
    "disgust": {
        "title": "Something is bothering you 🟢",
        "message": "It is okay to feel uncomfortable. Your feelings are valid.",
        "tips": [
            "Remove yourself from what is causing discomfort",
            "Set a healthy boundary — it is okay to say no",
            "Journal about what triggered this feeling",
            "Do a short mindfulness meditation for 5 minutes",
            "Talk to someone you trust about what bothered you"
        ],
        "helplines": [
            {"name": "iCall India", "number": "9152987821"},
            {"name": "Vandrevala Foundation", "number": "1860-2662-345"}
        ],
        "affirmation": "Your boundaries matter. You deserve to feel comfortable.",
        "color": "green",
        "emoji": "💚"
    },
    "happy": {
        "title": "You are feeling happy 😊",
        "message": "Amazing! Keep this energy going!",
        "tips": [
            "Share your happiness with someone you love",
            "Use this positive energy to tackle a goal you have been postponing",
            "Write down what made you happy today in a journal",
            "Do something creative — draw, sing, dance, cook",
            "Practice gratitude — write 5 things you appreciate right now"
        ],
        "helplines": [],
        "affirmation": "Your happiness matters. You deserve every good thing.",
        "color": "yellow",
        "emoji": "😊"
    },
    "neutral": {
        "title": "You are feeling calm and balanced 😐",
        "message": "A calm mind is a powerful mind.",
        "tips": [
            "This is a perfect time for focused deep work",
            "Plan your goals for the rest of the day",
            "Do a short mindfulness check-in",
            "Learn something new — read an article or watch a tutorial",
            "Connect with a friend or colleague"
        ],
        "helplines": [],
        "affirmation": "Balance is a superpower. Make the most of this clear-headed moment.",
        "color": "gray",
        "emoji": "😐"
    },
    "surprise": {
        "title": "You seem surprised 😮",
        "message": "Something caught you off guard — take a moment.",
        "tips": [
            "Pause before reacting — take 3 deep breaths",
            "Process what happened before making any decisions",
            "Talk to someone about what surprised you",
            "Write down your immediate thoughts and feelings",
            "Remember — surprises can be opportunities in disguise"
        ],
        "helplines": [],
        "affirmation": "You can handle whatever comes your way. Take it one step at a time.",
        "color": "orange",
        "emoji": "😮"
    }
}


def get_suggestion(emotion: str) -> dict:
    """Return wellness suggestion data for a given emotion."""
    emotion = emotion.lower().strip()
    return SUGGESTIONS.get(emotion, SUGGESTIONS["neutral"])
