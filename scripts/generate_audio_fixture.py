"""Regenerates the audio test fixture under tests/fixtures/, using macOS's
built-in `say` for two-voice text-to-speech and ffmpeg to concatenate and
convert to mp3. Only works on macOS with ffmpeg installed.

Run from the repo root: python3 scripts/generate_audio_fixture.py
"""

import subprocess
import tempfile
from pathlib import Path

LINES = [
    ("Samantha", "Thanks for calling Riverside Dental, this is Jordan speaking. How can I help you today?"),
    ("Daniel", "Hi, I need to reschedule my cleaning appointment. It's currently booked for next Tuesday at 2 PM."),
    ("Samantha", "Sure, I can help with that. Let me pull up your file. I see it. We have an opening this Thursday at 10 AM, or next Monday at 3:30 PM. Which would you prefer?"),
    ("Daniel", "Thursday at 10 AM works better for me."),
    ("Samantha", "Great, I've moved your cleaning appointment to this Thursday at 10 AM. You'll get a reminder text the day before."),
]

OUTPUT_PATH = "tests/fixtures/sample_call.mp3"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        part_files = []
        for i, (voice, text) in enumerate(LINES):
            aiff_path = tmp_path / f"part_{i}.aiff"
            subprocess.run(["say", "-v", voice, "-o", str(aiff_path), text], check=True)
            part_files.append(aiff_path)

        concat_list = tmp_path / "concat.txt"
        concat_list.write_text("".join(f"file '{p}'\n" for p in part_files))

        combined_wav = tmp_path / "combined.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), str(combined_wav)],
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(combined_wav), "-b:a", "64k", OUTPUT_PATH],
            check=True,
            capture_output=True,
        )

    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
