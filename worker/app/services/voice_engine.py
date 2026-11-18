import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import edge_tts

from app.config import settings
from app.schemas import WordTimestamp


class VoiceEngine:
    """
    Synthesizes broadcast-quality English narration using Edge-TTS neural models.
    Extracts millisecond word-boundary timestamps for synchronized subtitles.
    """

    DEFAULT_VOICE = "en-US-ChristopherNeural"  # Deep, documentary authoritative tone
    ALTERNATE_VOICES = {
        "documentary_male": "en-US-ChristopherNeural",
        "storytelling_male": "en-US-GuyNeural",
        "british_narration": "en-GB-RyanNeural",
        "documentary_female": "en-US-JennyNeural",
        "intense_storytelling": "en-US-EricNeural"
    }

    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Removes markdown headers, formatting, bracketed stage directions."""
        text = re.sub(r"\[.*?\]", "", text)       # [Pause], [Sound effect]
        text = re.sub(r"\(.*?\)", "", text)       # (Narrator note)
        text = re.sub(r"#+\s*", "", text)         # # Headers
        text = re.sub(r"\*+", "", text)           # *Bold / Italic*
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def synthesize(
        self,
        text: str,
        output_filename: str,
        voice: str = DEFAULT_VOICE,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Tuple[str, float, List[WordTimestamp]]:
        """
        Synthesizes text to an MP3 file and returns:
        (file_path, duration_seconds, word_timestamps)
        """
        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            raise ValueError("Input text is empty after cleaning.")

        out_path = settings.audio_narrations / output_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)

        selected_voice = self.ALTERNATE_VOICES.get(voice, voice)
        communicate = edge_tts.Communicate(
            clean_text,
            selected_voice,
            rate=rate,
            pitch=pitch,
            boundary="WordBoundary"
        )

        word_timestamps: List[WordTimestamp] = []

        # Stream audio and capture WordBoundary events
        with open(out_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # Offset & duration are provided in ticks (1 tick = 100 nanoseconds = 0.0001 ms)
                    offset_ms = int(chunk["offset"] / 10000)
                    duration_ms = int(chunk["duration"] / 10000)
                    word_timestamps.append(
                        WordTimestamp(
                            word=chunk["text"],
                            start_time_ms=offset_ms,
                            end_time_ms=offset_ms + duration_ms
                        )
                    )

        # Calculate exact duration using ffprobe if available
        duration_seconds = 0.0
        try:
            import subprocess
            probe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(out_path)
            ]
            probe_out = subprocess.check_output(probe_cmd, stderr=subprocess.DEVNULL).decode().strip()
            duration_seconds = round(float(probe_out), 3)
        except Exception:
            if word_timestamps:
                duration_seconds = round(max(word_timestamps[-1].end_time_ms / 1000.0, 1.0), 3)
            else:
                file_size = os.path.getsize(out_path)
                duration_seconds = round(max(file_size / 16000.0, 1.0), 3)

        return str(out_path), duration_seconds, word_timestamps


voice_engine = VoiceEngine()
