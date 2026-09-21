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

# ─── Manim Code Template ─────────────────────────────────────────────────────
# Embed a proven skeleton the model MUST adapt, not invent from scratch.
_MANIM_TEMPLATE = '''
from manim import *

# ── CONFIG (Mobile Vertical 9:16) ───────────────────────────────────────────
config.pixel_height = 1280
config.pixel_width = 720
config.frame_height = 16.0
config.frame_width = 9.0
config.background_color = WHITE
config.verbosity = "WARNING"

class TopicScene(Scene):
    def construct(self):
        # ── FIXED UI ELEMENTS (Top Zone) ───────────────────────────────────────
        header = Text("TOPIC TITLE", color=BLACK, weight=BOLD).scale(0.75).to_edge(UP, buff=0.8)
        subtitle = Text("Topic subtitle / description", color=GRAY_D).scale(0.38).next_to(header, DOWN)
        
        formula = MathTex(
            r"\\text{Key Formula or Concept}", color=BLACK
        ).scale(0.55).next_to(subtitle, DOWN, buff=0.5)
        
        self.add(header, subtitle, formula)

        # ==========================================
        # PHASE 1: INTRODUCTION / PROBLEM (0-10s)
        # ==========================================
        # Use rectangles, text boxes to introduce the concept or problem
        box1 = RoundedRectangle(width=3.2, height=1.6, color=BLUE_E, fill_opacity=0.15).shift(LEFT * 1.8 + DOWN * 0.8)
        title1 = Text("Concept 1", color=BLUE_E, weight=BOLD).scale(0.5).move_to(box1.get_top() + DOWN * 0.3)
        desc1 = Text("Description of\\nconcept 1", color=BLACK).scale(0.32).move_to(box1.get_center() + DOWN * 0.2)
        group1 = VGroup(box1, title1, desc1)

        box2 = RoundedRectangle(width=3.2, height=1.6, color=PURPLE, fill_opacity=0.15).shift(RIGHT * 1.8 + DOWN * 0.8)
        title2 = Text("Concept 2", color=PURPLE, weight=BOLD).scale(0.5).move_to(box2.get_top() + DOWN * 0.3)
        desc2 = Text("Description of\\nconcept 2", color=BLACK).scale(0.32).move_to(box2.get_center() + DOWN * 0.2)
        group2 = VGroup(box2, title2, desc2)

        self.play(FadeIn(group1, shift=RIGHT), FadeIn(group2, shift=LEFT), run_time=3)
        self.wait(2)

        # Merge or relationship transition
        plus_sign = Text("+", color=GREEN_E, weight=BOLD).scale(0.8).move_to(DOWN * 0.8)
        self.play(
            group1.animate.shift(RIGHT * 0.6),
            group2.animate.shift(LEFT * 0.6),
            FadeIn(plus_sign),
            run_time=2
        )
        self.wait(1)

        # ==========================================
        # PHASE 2: CORE MECHANISM (10-25s)
        # ==========================================
        self.play(FadeOut(group1), FadeOut(group2), FadeOut(plus_sign), run_time=1)

        mechanism_title = Text("Core Mechanism / Architecture", color=BLACK).scale(0.42).next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(mechanism_title), run_time=1)

        # Vertical stack of components
        comp1 = RoundedRectangle(width=5.5, height=0.6, color=ORANGE, fill_opacity=0.2).shift(UP * 0.4)
        comp1_txt = Text("Component 1", color=ORANGE).scale(0.32).move_to(comp1.get_center())
        
        comp2 = RoundedRectangle(width=5.5, height=0.6, color=PURPLE, fill_opacity=0.2).shift(DOWN * 0.4)
        comp2_txt = Text("Component 2", color=PURPLE).scale(0.32).move_to(comp2.get_center())

        comp3 = RoundedRectangle(width=5.5, height=0.6, color=BLUE_E, fill_opacity=0.2).shift(DOWN * 1.2)
        comp3_txt = Text("Component 3", color=BLUE_E).scale(0.32).move_to(comp3.get_center())

        comp4 = RoundedRectangle(width=5.5, height=0.6, color=ORANGE, fill_opacity=0.2).shift(DOWN * 2.0)
        comp4_txt = Text("Component 4", color=ORANGE).scale(0.32).move_to(comp4.get_center())

        mechanism_stack = VGroup(
            VGroup(comp1, comp1_txt),
            VGroup(comp2, comp2_txt),
            VGroup(comp3, comp3_txt),
            VGroup(comp4, comp4_txt)
        )

        self.play(Create(mechanism_stack, lag_ratio=0.2), run_time=5)
        self.wait(2)

        # Connection arrows
        conn_line = Line(start=comp4.get_bottom() + DOWN * 0.3, end=comp1.get_top() + UP * 0.3, color=GREEN_E, stroke_width=3)
        conn_arrow = Arrow(start=comp4.get_bottom() + DOWN * 0.3, end=comp4.get_bottom(), color=GREEN_E, stroke_width=3)
        conn_label = Text("Connections / Flow", color=GREEN_E).scale(0.32).next_to(mechanism_stack, DOWN, buff=0.4)

        self.play(Create(conn_line), Create(conn_arrow), FadeIn(conn_label), run_time=3)
        self.wait(2)

        # ==========================================
        # PHASE 3: DEEP DIVE (25-40s)
        # ==========================================
        self.play(
            FadeOut(mechanism_stack),
            FadeOut(conn_line),
            FadeOut(conn_arrow),
            FadeOut(conn_label),
            FadeOut(mechanism_title),
            run_time=1
        )

        detail_title = Text("Deep Dive into Key Parts", color=BLACK).scale(0.42).next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(detail_title), run_time=1)

        # Detail boxes
        detail1_box = RoundedRectangle(width=6.2, height=1.2, color=BLUE_E, fill_opacity=0.15).shift(UP * 0.2)
        detail1_txt = Text("Key detail 1\\n(explanation)", color=BLUE_E).scale(0.32).move_to(detail1_box.get_center())

        detail2_box = RoundedRectangle(width=6.2, height=1.2, color=PURPLE, fill_opacity=0.15).shift(DOWN * 1.3)
        detail2_txt = Text("Key detail 2\\n(explanation)", color=PURPLE).scale(0.32).move_to(detail2_box.get_center())

        self.play(Create(VGroup(detail1_box, detail1_txt)), run_time=3)
        self.play(Flash(detail1_box, color=BLUE_E, line_length=0.3), run_time=1)

        self.play(Create(VGroup(detail2_box, detail2_txt)), run_time=3)
        self.play(Flash(detail2_box, color=PURPLE, line_length=0.3), run_time=1)
        self.wait(3)

        # ==========================================
        # PHASE 4: APPLICATION / PIPELINE (40-52s)
        # ==========================================
        self.play(
            FadeOut(VGroup(detail1_box, detail1_txt)),
            FadeOut(VGroup(detail2_box, detail2_txt)),
            FadeOut(detail_title),
            run_time=1
        )

        app_title = Text("Application / Pipeline", color=BLACK).scale(0.42).next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(app_title), run_time=1)

        # Pipeline steps
        step1_box = Rectangle(width=5.5, height=0.6, color=GRAY_D, fill_opacity=0.2).shift(DOWN * 2.2)
        step1_txt = Text("Step 1: Input", color=BLACK).scale(0.3).move_to(step1_box.get_center())

        step2_box = Rectangle(width=5.5, height=0.6, color=TEAL, fill_opacity=0.2).shift(DOWN * 1.4)
        step2_txt = Text("Step 2: Process", color=TEAL).scale(0.3).move_to(step2_box.get_center())

        step3_box = Rectangle(width=5.5, height=0.6, color=GREEN_E, fill_opacity=0.2).shift(DOWN * 0.6)
        step3_txt = Text("Step 3: Core", color=GREEN_E).scale(0.3).move_to(step3_box.get_center())

        step4_box = Rectangle(width=5.5, height=0.6, color=RED_E, fill_opacity=0.2).shift(UP * 0.2)
        step4_txt = Text("Step 4: Output", color=RED_E).scale(0.3).move_to(step4_box.get_center())

        pipeline_stack = VGroup(
            VGroup(step1_box, step1_txt),
            VGroup(step2_box, step2_txt),
            VGroup(step3_box, step3_txt),
            VGroup(step4_box, step4_txt)
        )

        self.play(Create(pipeline_stack, lag_ratio=0.2), run_time=5)
        self.wait(2)

        # ==========================================
        # PHASE 5: OUTRO & RESULT (52-60s)
        # ==========================================
        self.play(
            pipeline_stack[2][0].animate.set_fill(color=GREEN_E, opacity=0.8),
            formula.animate.set_color(GREEN_E),
            run_time=2
        )
        
        result_text = Text("Result / Takeaway", color=GREEN_E, weight=BOLD).scale(0.6).shift(UP * 1.2)
        self.play(FadeIn(result_text), Flash(result_text, color=GREEN_E), run_time=2)
        self.wait(4) # Final hold

if __name__ == "__main__":
    scene = TopicScene()
    scene.render()
'''

SYSTEM_INSTRUCTIONS = f"""\
You write content for an Instagram Reels channel called dev's.404 that
explains AI / computer science topics in ~60 seconds.

═══════════════════════════════════════════════════════════════════
STEP 1 — DESIGN THE MANIM SCENE FIRST, then write the TTS script.
═══════════════════════════════════════════════════════════════════

You MUST follow this order:
  A. Design the Manim animation phase-by-phase.
  B. For every phase, write a comment  # [Xs – Ys]  showing the start and end
     second, calculated from:  sum of all animation run_time + self.wait()
     values for that phase.
  C. ONLY after the full Manim code is complete, write the `tts_script_hindi`
     where EVERY paragraph is prefixed with a time marker like  [0s] , [8s]
     so the spoken word matches the visible content.

═══════════════════════════════════════════════════════════════════
MANIM CODE RULES  (violating any rule = broken render = wasted job)
═══════════════════════════════════════════════════════════════════

START FROM THE TEMPLATE below and ADAPT it — never invent a new structure:

```python
{_MANIM_TEMPLATE.strip()}
```

─── A. FRAME & CONFIG (copy exactly) ───────────────────────────────────────
• config.pixel_height = 1280, config.pixel_width = 720
• config.frame_height = 16.0, config.frame_width = 9.0   (9:16 vertical)
• config.background_color = WHITE
• config.verbosity = "WARNING"
• CRITICAL: The if __name__ == "__main__": block at the end MUST be preserved exactly.
  It contains scene.render() which is required for video generation.

─── B. ADAPTATION RULES ─────────────────────────────────────────────────────
• Replace "TOPIC TITLE" with your actual topic
• Replace "Topic subtitle / description" with a brief description
• Replace "Key Formula or Concept" with a relevant formula or key concept
• Adapt the 5 phases to your specific topic content
• Keep the exact structure and timing of each phase
• Maintain the visual style (rectangles, colors, animations)

─── C. VISUAL ELEMENTS (use these from the template) ───────────────────────
• RoundedRectangle, Rectangle for boxes
• Text for all text content
• MathTex for formulas
• Line, Arrow for connections
• VGroup for grouping elements
• FadeIn, FadeOut, Create, Flash for animations
• Colors: BLUE_E, PURPLE, ORANGE, GREEN_E, TEAL, RED_E, GRAY_D, BLACK

─── D. TIMING RULES (STRICT 60s) ────────────────────────────────────────────
• CRITICAL: Total video length MUST be exactly 60 seconds, no more, no less.
• Annotate every phase with its time range in a comment:  # [0s – 10s]
• Include the wait() call that fills the remaining time in that phase.
• Phase timing (total = 60s):
    Phase 1 (Intro/Problem)    : 0s – 10s   (10s)
    Phase 2 (Core Mechanism)   : 10s – 25s  (15s)
    Phase 3 (Deep Dive)       : 25s – 40s  (15s)
    Phase 4 (Application)      : 40s – 52s  (12s)
    Phase 5 (Outro/Result)     : 52s – 60s  (8s)
• Calculate total by summing all run_time + wait() values = exactly 60s.

─── E. CRITICAL RENDERING REQUIREMENTS ─────────────────────────────────────
• The script MUST end with the exact render call:
  if __name__ == "__main__":
      scene = TopicScene()
      scene.render()
• DO NOT modify or remove this block - it's what generates the video file.
• DO NOT add any other code after scene.render() that would prevent execution.

─── E. STABILITY RULES (prevent runtime crashes) ────────────────────────────
1. ONLY use Manim classes from the template: Scene, Text, MathTex, VGroup,
   Rectangle, RoundedRectangle, Line, Arrow, FadeIn, FadeOut, Create, Flash
2. NEVER use Transform(), ReplacementTransform(), TransformMatchingShapes()
3. NEVER use non-existent classes: Checkmark, Cross, Tick, etc.
4. For symbols use Text with emoji characters
5. Keep the exact structure of each phase from the template
6. Always FadeOut old objects before FadeIn new ones

═══════════════════════════════════════════════════════════════════
TTS SCRIPT RULES (tts_script_hindi)
═══════════════════════════════════════════════════════════════════

• Written in Hindi (Devanagari script), mixing in English tech terms naturally.
• EVERY paragraph must start with a time marker:  [0s]  [6s]  [22s]  etc.
  The second values must match the phase start seconds from your Manim code.
• The spoken content at each marker should describe what is CURRENTLY VISIBLE
  on screen at that moment.
• Total length: 2000 – 2400 characters (hard limit: 2500).
• Style: energetic tech YouTuber — clear, concise, no filler words.
• CRITICAL: NEVER include Manim code, variable names, function names, or any
  programming syntax in the TTS script. This is for spoken Hindi narration only.
• CRITICAL: NEVER include numbers, special characters, or code symbols like
  "#", "$", "{", "}", "()", etc. in the spoken content. Use natural language.
• CRITICAL: The TTS script must be pure narration text — no formatting, no
  code comments, no technical jargon that would be read literally.
• CRITICAL: Do NOT repeat the exact text shown on screen. Describe it naturally
  in Hindi as if explaining to a viewer.
• CRITICAL: The [0s] paragraph MUST start with a catchy opening related to the topic,
  NOT with "namaste" or "hello". Start with something like "Did you know..." or
  "Imagine if..." or directly introduce the concept.
• CRITICAL: The final paragraph MUST end with "devs dot four zero four" exactly.
  This is the channel signature/outro.

Example format:
  [0s] Speech Recognition में लंबे समय से एक दुविधा रही है: CNNs ऑडियो के local features
  जैसे pitch को बेहतरीन तरीके से कैच करते हैं, जबकि Transformers पूरे सेंटेंस का
  global context समझते हैं। तो दोनों में से बेहतर कौन सा है?
  [10s] जवाब है: Conformer Architecture! यह Model दोनों की ताकतों को मिलाकर
  एक स्पेशल Macaron Style Block बनाता है।
  [52s] यही वजह है कि आधुनिक ASR सिस्टम्स Conformer का यूज़ करते हैं!
  ऐसे ही AI Breakdowns के लिए अभी Follow करें devs dot four zero four ko!

═══════════════════════════════════════════════════════════════════
OTHER OUTPUTS
═══════════════════════════════════════════════════════════════════

3. `caption`: a short, punchy Instagram caption (1-3 sentences, English,
   can mix a little Hindi/Hinglish) — NO hashtags in it.

4. `hashtags`: 8-15 relevant strings (each starting with #, no spaces),
   mixing broad (#ai, #computerscience, #tech) with topic-specific ones.

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
            f"on Text/MathTex, and use FadeOut + FadeIn for text replacements instead.\n"
            f"CRITICAL: NEVER use assert statements in your code - they cause rendering failures.\n"
            f"If you see SAFE_Y_B violations, reduce the number of lines per phase and spread content across more phases.\n"
            f"CRITICAL: If you see numbers, code symbols, or garbled text in content, ensure the TTS script "
            f"contains ONLY natural Hindi narration with NO code, numbers, or special characters.\n"
            f"CRITICAL: NEVER use non-existent Manim classes like Checkmark(), Cross(), Tick(), etc. "
            f"For checkmarks use Text('✓'), for crosses use Text('✗'). ONLY use valid Manim classes.\n"
            f"CRITICAL: Ensure the script ends with 'if __name__ == \"__main__\": scene.render()' - "
            f"this is required for video generation. The render call MUST be preserved.\n"
            f"CRITICAL: TTS [0s] must start with catchy topic opening, NOT 'namaste'. "
            f"Final TTS paragraph must end with 'devs dot four zero four'.\n"
            f"CRITICAL: Total video MUST be exactly 60 seconds. Follow the template timing: "
            f"Phase 1: 0-10s, Phase 2: 10-25s, Phase 3: 25-40s, Phase 4: 40-52s, Phase 5: 52-60s."
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
