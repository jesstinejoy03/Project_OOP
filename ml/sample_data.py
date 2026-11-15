"""Small synthetic dataset so the app still works without the full download.

Only a fallback for demos; the real model should be trained on dair-ai/emotion.
"""

SAMPLES = {
    "sadness": [
        "i feel so empty and alone today", "i cried myself to sleep last night",
        "i miss my old friends so much", "everything feels hopeless and heavy",
        "i feel down and i do not know why", "i am heartbroken after the news",
        "i feel like a failure and nothing helps", "i have been feeling really low lately",
        "i feel lonely even when i am around people", "it hurts that nobody called me",
        "i feel miserable and tired of everything", "i am so sad that it is over",
    ],
    "joy": [
        "i feel so happy and excited today", "i am thrilled that i passed my exam",
        "this is the best day ever", "i feel cheerful and full of energy",
        "i am delighted with how the project went", "i feel proud and really satisfied",
        "i love how relaxed and content i feel", "i am so glad everything worked out",
        "i feel great and i cannot stop smiling", "i am enjoying every moment of this trip",
        "i feel grateful and joyful this morning", "what a wonderful and fun weekend",
    ],
    "love": [
        "i feel so loved and cared for", "i adore spending time with my family",
        "i am so fond of my best friend", "i feel warm and affectionate towards her",
        "i care deeply about the people around me", "i feel tender and devoted to my partner",
        "my heart is full when i am with them", "i feel so close and connected to him",
        "i cherish every moment we share", "i am so in love with this life",
        "i feel supportive and caring today", "i value my friends so much",
    ],
    "anger": [
        "i am furious about how they treated me", "i feel so angry and frustrated",
        "this makes me so mad i could scream", "i am irritated by all the noise",
        "i feel resentful and bitter about the unfair grade", "i hate being ignored like this",
        "i am annoyed that they lied to me", "i feel outraged by this decision",
        "i am so fed up with everything", "i feel rage every time i think about it",
        "i feel offended and disrespected", "i am livid that nobody listened",
    ],
    "fear": [
        "i feel anxious about my deadlines", "i am scared that i will fail the exam",
        "i feel nervous and cannot calm down", "i am terrified of speaking in front of people",
        "i feel panicked and my heart is racing", "i am worried about what will happen next",
        "i feel overwhelmed and afraid i cannot cope", "i am so stressed and tense about tomorrow",
        "i feel uneasy and on edge all day", "i am afraid something bad will happen",
        "i feel insecure and unsure about everything", "i cannot sleep because i am so worried",
    ],
    "surprise": [
        "i am shocked by the unexpected news", "i was amazed when they showed up",
        "i feel stunned and cannot believe it", "what a surprise to see you here",
        "i am astonished by the sudden change", "i did not expect that result at all",
        "i feel startled by the loud noise", "i am speechless after that announcement",
        "that was completely unexpected", "i was caught off guard by the question",
        "i feel taken aback by what she said", "i am amazed that it actually happened",
    ],
}


KEYWORDS = {
    "sadness": ["sad", "lonely", "hopeless", "miserable", "heartbroken", "empty", "down", "gloomy"],
    "joy": ["happy", "joyful", "cheerful", "delighted", "thrilled", "excited", "glad", "proud"],
    "love": ["loved", "affectionate", "caring", "fond", "devoted", "tender", "adored", "close"],
    "anger": ["angry", "furious", "irritated", "annoyed", "outraged", "resentful", "mad", "frustrated"],
    "fear": ["anxious", "scared", "nervous", "terrified", "worried", "afraid", "panicked", "stressed"],
    "surprise": ["shocked", "amazed", "stunned", "startled", "astonished", "surprised", "speechless",
                 "bewildered"],
}

FRAMES = [
    "i feel {w}", "i am so {w} today", "honestly i am {w} about everything",
    "{w} is all i can feel right now", "lately i have been feeling {w}",
    "i feel {w} and i do not know what to do",
]


def sample_dataset():
    """Return (texts, labels): hand-written sentences plus keyword templates."""
    texts, labels = [], []
    for emotion, sentences in SAMPLES.items():
        for s in sentences:
            texts.append(s)
            labels.append(emotion)
        for word in KEYWORDS[emotion]:
            for frame in FRAMES:
                texts.append(frame.format(w=word))
                labels.append(emotion)
    return texts, labels
