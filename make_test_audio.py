"""Generate .wav test clips for the Mood Journal 'Voice entry' feature.

Put this file in the project folder (next to main.py), then run:
    pip install pyttsx3
    python make_test_audio.py

It creates a 'test_audio' folder with one .wav per sentence plus
'expected_emotions.txt'. In the app: Journal tab -> "Voice entry (.wav)..." -> pick a clip.

Platform notes
- Windows: works out of the box (uses the built-in voices).
- macOS: pyttsx3 may save AIFF data even with a .wav name. If the app rejects a clip, use
      say -o clip.aiff "i feel so sad"
      afconvert -f WAVE -d LEI16 clip.aiff clip.wav
- Linux: install the voice engine first: sudo apt install espeak
"""
from pathlib import Path

CLIPS = [
    ("sadness_1", "i feel so sad and lonely today, i miss my family so much"),
    ("sadness_2", "i am heartbroken and i feel hopeless about everything"),
    ("joy_1", "i feel so happy and excited, i just got the internship offer"),
    ("joy_2", "today was wonderful and i am so glad everything worked out"),
    ("love_1", "i feel so loved and grateful for my friends, they mean everything to me"),
    ("anger_1", "i am furious that they lied to me and nobody even apologised"),
    ("anger_2", "i am so fed up and frustrated, they took all the credit for my work"),
    ("fear_1", "i feel terrified about my presentation tomorrow, my heart is racing"),
    ("fear_2", "i have three deadlines this week and i cannot sleep because i am so worried"),
    ("surprise_1", "i am completely shocked, i did not expect that at all"),
    ("mixed_1", "i got the grade i wanted but i feel strangely empty and a bit sad"),
    ("despair_1", "i feel so hopeless and helpless, i cannot see a way forward"),
    ("despair_2", "i feel completely overwhelmed and i cannot cope with anything anymore"),
    ("despair_3", "i feel utterly hopeless and i cannot find any light at the end of the tunnel")
]


def main() -> None:
    try:
        import pyttsx3
    except ImportError:
        raise SystemExit("pyttsx3 is not installed. Run:  pip install pyttsx3")

    out_dir = Path(__file__).resolve().parent / "test_audio"
    out_dir.mkdir(exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)          # slightly slow = easier for the recogniser

    for name, text in CLIPS:
        engine.save_to_file(text, str(out_dir / f"{name}.wav"))
    engine.runAndWait()                      # writes all files

    lines = [f"{name}.wav  ->  expected: {name.split('_')[0]}  |  \"{text}\""
             for name, text in CLIPS]
    (out_dir / "expected_emotions.txt").write_text("\n".join(lines), encoding="utf-8")

    made = sorted(p.name for p in out_dir.glob("*.wav"))
    print(f"Created {len(made)} clips in {out_dir}")
    if len(made) < len(CLIPS):
        print("Some clips are missing. See the platform notes at the top of this file.")


if __name__ == "__main__":
    main()
