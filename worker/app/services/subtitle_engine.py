from pathlib import Path
from typing import List, Tuple
from app.config import settings
from app.schemas import WordTimestamp


class SubtitleEngine:
    """
    Generates synchronized .srt and stylized .ass subtitle files.
    Supports clean 16:9 documentary styling and dynamic 9:16 Shorts styling.
    """

    @staticmethod
    def format_srt_time(ms: int) -> str:
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @staticmethod
    def format_ass_time(ms: int) -> str:
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        centiseconds = (ms % 1000) // 10
        return f"{hours:01d}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def build_subtitles(
        self,
        word_timestamps: List[WordTimestamp],
        output_basename: str,
        video_format: str = "LONG_FORM",
        words_per_group: int = 5
    ) -> Tuple[str, str]:
        """
        Groups words into readable sentences/phrases and builds both .srt and .ass files.
        Returns: (ass_path, srt_path)
        """
        srt_path = settings.subtitles / f"{output_basename}.srt"
        ass_path = settings.subtitles / f"{output_basename}.ass"

        if not word_timestamps:
            # Create empty files
            srt_path.write_text("", encoding="utf-8")
            ass_path.write_text("", encoding="utf-8")
            return str(ass_path), str(srt_path)

        # 1. Group words into natural sentence chunks
        groups = []
        current_words = []
        for wt in word_timestamps:
            current_words.append(wt)
            # Break group on punctuation or max words
            if len(current_words) >= words_per_group or wt.word.endswith((".", "!", "?", ",", ";", ":")):
                groups.append(current_words)
                current_words = []
        if current_words:
            groups.append(current_words)

        # 2. Write SRT file
        srt_lines = []
        for idx, grp in enumerate(groups, 1):
            start = self.format_srt_time(grp[0].start_time_ms)
            end = self.format_srt_time(grp[-1].end_time_ms + 100)
            text = " ".join(w.word for w in grp)
            srt_lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

        # 3. Write ASS file with formatting
        is_shorts = (video_format.upper() == "SHORTS")
        play_res_x = 1080 if is_shorts else 1920
        play_res_y = 1920 if is_shorts else 1080
        font_size = 46 if is_shorts else 28
        margin_v = 450 if is_shorts else 65  # Centered lower area for Shorts, bottom for long form

        ass_header = f"""[Script Info]
Title: VOIDORA Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.5,1.5,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogue_lines = []
        for grp in groups:
            start_str = self.format_ass_time(grp[0].start_time_ms)
            end_str = self.format_ass_time(grp[-1].end_time_ms + 100)
            text_str = " ".join(w.word for w in grp)
            # Escape curly braces for ASS syntax
            text_str = text_str.replace("{", "(").replace("}", ")")
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_str}")

        ass_content = ass_header + "\n".join(dialogue_lines) + "\n"
        ass_path.write_text(ass_content, encoding="utf-8")

        return str(ass_path), str(srt_path)


subtitle_engine = SubtitleEngine()
