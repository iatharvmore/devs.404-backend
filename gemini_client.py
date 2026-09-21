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

   MOBILE REEL SAFE AREA — CRITICAL:
   Canvas is 720x1280, 9:16 (frame_height = 16.0, frame_width = 9.0).
   Keep ALL important content inside a generous safe area.
   Horizontal:
   - leave at least 0.8 Manim units from both left and right edges (keep x within [-3.7, +3.7]).
   Vertical:
   - leave at least 1.0 Manim units from both top and bottom edges (keep y within [-7.0, +7.0]).
   This applies to:
   - titles
   - subtitles
   - Text
   - MathTex
   - diagrams
   - arrows
   - boxes
   - labels
   - animated objects
   Never allow any object to touch or cross the frame boundary.
   Never use the entire frame width for text.
   Long text must be wrapped into multiple lines.
   Prefer smaller content with generous whitespace.
   Before every self.play() sequence, ensure the complete visible composition remains inside the safe area.
   The viewer must be able to see every important element comfortably on a phone without edge clipping.

   MANIM STABILITY RULES — CRITICAL:
   Generate only robust Manim animations that work reliably in Manim Community.
   1. NEVER use Transform(), ReplacementTransform(), TransformMatchingShapes(),
      TransformMatchingTex(), or similar structural interpolation between Text,
      MathTex, Tex, or other Mobjects whose internal submobject counts may differ.
   2. NEVER transform one Text object directly into another Text object containing
      different words.
   3. When changing displayed text, use:
      FadeOut(old_text)
      followed by
      FadeIn(new_text)
      rather than Transform(old_text, new_text).
   4. For moving, scaling, positioning, or rotating an existing object, normal
      .animate methods are allowed, but do not use .animate.become() to replace
      its underlying structure.
   5. Do not change the number of submobjects of a Mobject during an animation.
   6. Prefer FadeIn, FadeOut, Write, Create, GrowArrow, Indicate, and simple
      .animate.shift(), .animate.scale(), .animate.move_to(), .animate.set_opacity()
      for reliable animations.
   7. Every self.play() call must animate Mobjects that remain structurally valid
      throughout the entire animation.
   8. For any uncertain transformation, use FadeOut + FadeIn instead.
   9. Before returning the code, mentally validate every self.play() sequence for
      compatible Mobject structure and avoid risky text transformations.
   10. Do not use deprecated Manim methods or deprecated method-animation patterns
       (e.g. avoid .set_width() in animation contexts). Prefer current Manim Community
       APIs and ordinary attribute/set operations where appropriate.
   11. Do not hallucinate non-existent Manim classes (like `Check`). If you need a checkmark,
       use `MathTex(r'\checkmark')` or `Text('✓')`. For a cross, use `Cross()`.

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


def generate_script(
    topic: str,
    api_key: str,
    error_feedback: str | None = None,
) -> ScriptResult:
    client = genai.Client(api_key=api_key)

    user_prompt = f"Topic for today's reel: {topic}"
    if error_feedback:
        error_snippet = error_feedback[-2500:] if len(error_feedback) > 2500 else error_feedback
        user_prompt += (
            f"\n\nCRITICAL FIX REQUIRED:\n"
            f"The previous Manim scene failed during rendering.\n\n"
            f"Rendering error:\n{error_snippet}\n\n"
            f"Generate a corrected scene.\n"
            f"Do not repeat the animation pattern that caused the error.\n"
            f"Strictly enforce MANIM STABILITY RULES: NEVER use Transform() or ReplacementTransform() "
            f"on Text/MathTex, and use FadeOut + FadeIn for text replacements instead."
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=user_prompt,
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
