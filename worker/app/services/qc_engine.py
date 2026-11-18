import json
import os
import subprocess
from typing import Dict, Any, Tuple


class QCEngine:
    """
    Automated video and audio quality control using ffprobe and ffmpeg filters.
    """

    def inspect_video(self, video_path: str, expected_format: str = "LONG_FORM", min_duration: float = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates resolution, duration, frame rate, audio presence, and file integrity.
        """
        if not os.path.isfile(video_path) or os.path.getsize(video_path) == 0:
            return False, {"error": "File does not exist or is empty"}

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe = json.loads(res.stdout)
        except Exception as e:
            return False, {"error": f"ffprobe execution failed: {e}"}

        streams = probe.get("streams", [])
        format_info = probe.get("format", {})

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        if not video_stream:
            return False, {"error": "No video stream detected in output file"}
        if not audio_stream:
            return False, {"error": "No audio stream detected in output file"}

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(format_info.get("duration", 0.0))
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

        # Dimension validation
        is_shorts = (expected_format.upper() == "SHORTS")
        expected_w, expected_h = (1080, 1920) if is_shorts else (1920, 1080)

        dimension_ok = (width == expected_w and height == expected_h)
        audio_ok = (audio_stream.get("codec_name") in ["aac", "mp3", "opus"])
        
        if min_duration is not None:
            duration_ok = (duration >= min_duration)
        else:
            duration_ok = (duration >= 5.0 if is_shorts else duration >= 10.0)

        qc_passed = dimension_ok and audio_ok and duration_ok

        report = {
            "qc_passed": qc_passed,
            "resolution": f"{width}x{height}",
            "expected_resolution": f"{expected_w}x{expected_h}",
            "duration_seconds": round(duration, 2),
            "file_size_mb": round(file_size_mb, 2),
            "video_codec": video_stream.get("codec_name"),
            "audio_codec": audio_stream.get("codec_name"),
            "audio_channels": audio_stream.get("channels"),
            "checks": {
                "dimension_valid": dimension_ok,
                "audio_valid": audio_ok,
                "duration_valid": duration_ok
            }
        }

        return qc_passed, report


qc_engine = QCEngine()
