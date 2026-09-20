"""
Calls Gemini (google-genai SDK, model gemini-2.5-flash) with a prompt that
mirrors your existing manual workflow: give it a topic, get back a
self-contained Manim scene (mobile 9:16, matches your existing style) and a
Hindi narration script for Sarvam TTS. Forces JSON output via
response_mime_type so there's no fragile markdown-fence parsing.
"""
from __future__ import annotations

from dataclasses import dataclass

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTIONS = """\
You write content for an Instagram Reels channel called dev's.404 that
explains AI / computer science topics in ~60 seconds.

You must output two things:

1. `manim_code`: a COMPLETE, runnable Python file using the `manim` library
   (Manim Community edition) that follows this exact structure:
   - config.pixel_height = 1280, config.pixel_width = 720
   - config.frame_height = 16.0, config.frame_width = 9.0
   - config.background_color = WHITE
   - one Scene subclass whose construct() builds a clear, labeled diagram
     that explains the topic step by step (title/subtitle at top, then
     phases separated by FadeOut/FadeIn, using Text/MathTex/shapes/arrows)
   - end the file with instantiating the scene and calling `scene.render()`
   - total on-screen duration (sum of self.wait() and animation run_time)
     should be roughly 55-70 seconds
   - use only black/gray/red/green/blue color constants for a clean look
     on a white background, matching a tech-explainer aesthetic

2. `tts_script_hindi`: a Hindi (Devanagari) narration script, mixing in
   English technical terms as needed, written the way a tech YouTuber would
   narrate this. It should roughly match the pacing/length of the on-screen
   phases in manim_code so a ~60s TTS render can be laid under the video.
   Keep it under 2400 characters (TTS provider limit is 2500).

3. `caption`: a short, punchy Instagram caption (1-3 sentences, English,
   can mix in a little Hindi/Hinglish if it fits the channel's voice) that
   makes people want to watch, with NO hashtags in it.

4. `hashtags`: a list of 8-15 relevant hashtag strings (each starting with
   #, no spaces), mixing broad tags (#ai, #computerscience, #tech) with
   more specific ones for the topic (e.g. #transformers, #machinelearning).

Return ONLY the JSON object matching the given schema — no markdown fences,
no commentary.
"""


@dataclass
class ScriptResult:
    manim_code: str
    tts_script_hindi: str
    caption: str
    hashtags: list[str]


def generate_script(topic: str, api_key: str) -> ScriptResult:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL,
        contents=f"Topic for today's reel: {topic}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTIONS,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "manim_code": {"type": "STRING"},
                    "tts_script_hindi": {"type": "STRING"},
                    "caption": {"type": "STRING"},
                    "hashtags": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                },
                "required": ["manim_code", "tts_script_hindi", "caption", "hashtags"],
            },
        ),
    )

    import json

    data = json.loads(response.text)
    return ScriptResult(
        manim_code=data["manim_code"],
        tts_script_hindi=data["tts_script_hindi"],
        caption=data["caption"],
        hashtags=data["hashtags"],
    )
