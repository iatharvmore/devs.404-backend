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
import numpy as np
import random
from IPython.display import Video

# --- CONFIG (Mobile Vertical 9:16) ---
config.pixel_height = 1280
config.pixel_width = 720
config.frame_height = 16.0
config.frame_width = 9.0
config.background_color = WHITE
config.verbosity = "WARNING"

class ConformerASR60s(Scene):
    def construct(self):
        # --- FIXED UI ELEMENTS (Top Zone) ---
        header = Text("CONFORMER FOR ASR", color=BLACK, weight=BOLD).scale(0.75).to_edge(UP, buff=0.8)
        subtitle = Text("Combining CNNs + Transformers for Speech", color=GRAY_D).scale(0.38).next_to(header, DOWN)
        
        formula = MathTex(
            r"\\text{Conformer} = \\text{CNN (Local)} + \\text{Transformer (Global)}", color=BLACK
        ).scale(0.55).next_to(subtitle, DOWN, buff=0.5)
        
        self.add(header, subtitle, formula)

        # ==========================================
        # PHASE 1: THE DILEMMA - CNN VS TRANSFORMER (0-10s)
        # ==========================================
        cnn_box = RoundedRectangle(width=3.2, height=1.6, color=BLUE_E, fill_opacity=0.15).shift(LEFT * 1.8 + DOWN * 0.8)
        cnn_title = Text("CNN", color=BLUE_E, weight=BOLD).scale(0.5).move_to(cnn_box.get_top() + DOWN * 0.3)
        cnn_desc = Text("Local Acoustic\\nFeatures", color=BLACK).scale(0.32).move_to(cnn_box.get_center() + DOWN * 0.2)
        cnn_group = VGroup(cnn_box, cnn_title, cnn_desc)

        trans_box = RoundedRectangle(width=3.2, height=1.6, color=PURPLE, fill_opacity=0.15).shift(RIGHT * 1.8 + DOWN * 0.8)
        trans_title = Text("Transformer", color=PURPLE, weight=BOLD).scale(0.5).move_to(trans_box.get_top() + DOWN * 0.3)
        trans_desc = Text("Global Context &\\nDependencies", color=BLACK).scale(0.32).move_to(trans_box.get_center() + DOWN * 0.2)
        trans_group = VGroup(trans_box, trans_title, trans_desc)

        self.play(FadeIn(cnn_group, shift=RIGHT), FadeIn(trans_group, shift=LEFT), run_time=3)
        self.wait(2)

        # Merge transition
        plus_sign = Text("+", color=GREEN_E, weight=BOLD).scale(0.8).move_to(DOWN * 0.8)
        self.play(
            cnn_group.animate.shift(RIGHT * 0.6),
            trans_group.animate.shift(LEFT * 0.6),
            FadeIn(plus_sign),
            run_time=2
        )
        self.wait(1)

        # ==========================================
        # PHASE 2: THE MACARON-STYLE CONFORMER BLOCK (10-25s)
        # ==========================================
        self.play(FadeOut(cnn_group), FadeOut(trans_group), FadeOut(plus_sign), run_time=1)

        block_title = Text("Macaron-Style Conformer Block", color=BLACK).scale(0.42).next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(block_title), run_time=1)

        # Vertical Macaron Modules
        ffn1 = RoundedRectangle(width=5.5, height=0.6, color=ORANGE, fill_opacity=0.2).shift(UP * 0.4)
        ffn1_txt = Text("Feed Forward Module (1/2)", color=ORANGE).scale(0.32).move_to(ffn1.get_center())
        
        mhsa = RoundedRectangle(width=5.5, height=0.6, color=PURPLE, fill_opacity=0.2).shift(DOWN * 0.4)
        mhsa_txt = Text("Multi-Head Self-Attention", color=PURPLE).scale(0.32).move_to(mhsa.get_center())

        conv = RoundedRectangle(width=5.5, height=0.6, color=BLUE_E, fill_opacity=0.2).shift(DOWN * 1.2)
        conv_txt = Text("Convolution Module", color=BLUE_E).scale(0.32).move_to(conv.get_center())

        ffn2 = RoundedRectangle(width=5.5, height=0.6, color=ORANGE, fill_opacity=0.2).shift(DOWN * 2.0)
        ffn2_txt = Text("Feed Forward Module (1/2)", color=ORANGE).scale(0.32).move_to(ffn2.get_center())

        macaron_stack = VGroup(
            VGroup(ffn1, ffn1_txt),
            VGroup(mhsa, mhsa_txt),
            VGroup(conv, conv_txt),
            VGroup(ffn2, ffn2_txt)
        )

        self.play(Create(macaron_stack, lag_ratio=0.2), run_time=5) # 13-18s
        self.wait(2)

        # Residual arrows
        res_line = Line(start=ffn2.get_bottom() + DOWN * 0.3, end=ffn1.get_top() + UP * 0.3, color=GREEN_E, stroke_width=3)
        res_arrow = Arrow(start=ffn2.get_bottom() + DOWN * 0.3, end=ffn2.get_bottom(), color=GREEN_E, stroke_width=3)
        res_label = Text("Residual Connections + LayerNorm", color=GREEN_E).scale(0.32).next_to(macaron_stack, DOWN, buff=0.4)

        self.play(Create(res_line), Create(res_arrow), FadeIn(res_label), run_time=3) # 20-23s
        self.wait(2)

        # ==========================================
        # PHASE 3: DEEP DIVE INTO CONVOLUTION & ATTENTION (25-40s)
        # ==========================================
        self.play(
            FadeOut(macaron_stack),
            FadeOut(res_line),
            FadeOut(res_arrow),
            FadeOut(res_label),
            FadeOut(block_title),
            run_time=1
        )

        detail_title = Text("Inside the Key Modules", color=BLACK).scale(0.42).next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(detail_title), run_time=1)

        # Depthwise Conv breakdown
        depthwise_box = RoundedRectangle(width=6.2, height=1.2, color=BLUE_E, fill_opacity=0.15).shift(UP * 0.2)
        depthwise_txt = Text("Depthwise Separable Conv\\n(Gated Linear Units + 1D Depthwise Conv)", color=BLUE_E).scale(0.32).move_to(depthwise_box.get_center())

        # Relative Positional MHSA
        rel_mhsa_box = RoundedRectangle(width=6.2, height=1.2, color=PURPLE, fill_opacity=0.15).shift(DOWN * 1.3)
        rel_mhsa_txt = Text("Multi-Head Self-Attention\\n(Relative Positional Encoding for Speech)", color=PURPLE).scale(0.32).move_to(rel_mhsa_box.get_center())

        self.play(
            Create(VGroup(depthwise_box, depthwise_txt)),
            run_time=3
        )
        self.play(Flash(depthwise_box, color=BLUE_E, line_length=0.3), run_time=1)

        self.play(
            Create(VGroup(rel_mhsa_box, rel_mhsa_txt)),
            run_time=3
        )
        self.play(Flash(rel_mhsa_box, color=PURPLE, line_length=0.3), run_time=1)
        self.wait(3)

        # ==========================================
        # PHASE 4: END-TO-END ASR PIPELINE (40-52s)
        # ==========================================
        self.play(
            FadeOut(VGroup(depthwise_box, depthwise_txt)),
            FadeOut(VGroup(rel_mhsa_box, rel_mhsa_txt)),
            FadeOut(detail_title),
            run_time=1
        )

        pipeline_title = Text("End-to-End ASR Pipeline", color=BLACK).scale(0.42).next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(pipeline_title), run_time=1)

        # Pipeline Flow Elements
        spec_box = Rectangle(width=5.5, height=0.6, color=GRAY_D, fill_opacity=0.2).shift(DOWN * 2.2)
        spec_txt = Text("1. Audio / Mel-Spectrogram Input", color=BLACK).scale(0.3).move_to(spec_box.get_center())

        sub_box = Rectangle(width=5.5, height=0.6, color=TEAL, fill_opacity=0.2).shift(DOWN * 1.4)
        sub_txt = Text("2. Convolutional Subsampling (4x Reduction)", color=TEAL).scale(0.3).move_to(sub_box.get_center())

        conf_enc_box = Rectangle(width=5.5, height=0.6, color=GREEN_E, fill_opacity=0.2).shift(DOWN * 0.6)
        conf_enc_txt = Text("3. N x Conformer Blocks (Encoder)", color=GREEN_E).scale(0.3).move_to(conf_enc_box.get_center())

        ctc_box = Rectangle(width=5.5, height=0.6, color=RED_E, fill_opacity=0.2).shift(UP * 0.2)
        ctc_txt = Text("4. CTC / Decoder -> Text Tokens", color=RED_E).scale(0.3).move_to(ctc_box.get_center())

        pipeline_stack = VGroup(
            VGroup(spec_box, spec_txt),
            VGroup(sub_box, sub_txt),
            VGroup(conf_enc_box, conf_enc_txt),
            VGroup(ctc_box, ctc_txt)
        )

        self.play(Create(pipeline_stack, lag_ratio=0.2), run_time=5) # 43-48s
        self.wait(2)

        # ==========================================
        # PHASE 5: OUTRO & RESULT (52-60s)
        # ==========================================
        self.play(
            pipeline_stack[2][0].animate.set_fill(color=GREEN_E, opacity=0.8),
            formula.animate.set_color(GREEN_E),
            run_time=2
        )
        
        output_text = Text('"Hello World"', color=GREEN_E, weight=BOLD).scale(0.6).shift(UP * 1.2)
        self.play(FadeIn(output_text), Flash(output_text, color=GREEN_E), run_time=2)
        self.wait(4) # CTA hold

# --- RENDER ---
scene = ConformerASR60s()
scene.render()
Video(scene.renderer.file_writer.movie_file_path, embed=True)
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

─── A. ADAPTATION RULES ─────────────────────────────────────────────────────
• Adapt the Conformer ASR example to your specific topic
• Replace "CONFORMER FOR ASR" with your topic title
• Replace specific Conformer content with your topic's content
• Keep the exact structure, timing, and visual style from the example
• The example produces exactly 60-second videos with matching TTS scripts

─── B. TIMING RULES ────────────────────────────────────────────────────────
• The example is exactly 60 seconds: 0-10s, 10-25s, 25-40s, 40-52s, 52-60s
• Maintain the same timing structure for your topic
• The TTS script in the example naturally matches the 60s video timing

─── C. VISUAL ELEMENTS ─────────────────────────────────────────────────────
• Use the same visual style: rectangles, text boxes, animations
• Keep the color scheme: BLUE_E, PURPLE, ORANGE, GREEN_E, TEAL, RED_E, GRAY_D, BLACK
• Use MathTex for formulas, Text for regular content
• Keep animations simple and effective

─── D. CRITICAL REQUIREMENTS ────────────────────────────────────────────────
• The script MUST end with: scene = ConformerASR60s(); scene.render()
• DO NOT modify the render block
• The TTS script should naturally match the visual content timing
• End with "ऐसे ही AI Breakdowns के लिए अभी Follow करें!"

═══════════════════════════════════════════════════════════════════
TTS SCRIPT RULES (tts_script_hindi)
═══════════════════════════════════════════════════════════════════

• Written in Hindi (Devanagari script), mixing in English tech terms naturally.
• The TTS script should naturally match the visual content and timing (approx 60 seconds).
• End with "ऐसे ही AI Breakdowns के लिए अभी Follow करें!"
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
  Speech Recognition में लंबे समय से एक दुविधा रही है: Convolutional Neural Networks यानी CNNs ऑडियो के local acoustic features जैसे pitch और timbre को बेहतरीन तरीके से कैच करते हैं, जबकि Transformers पूरे सेंटेंस का global context और long range dependencies समझते हैं। तो दोनों में से बेहतर कौन सा है? जवाब है: Conformer Architecture! Google का यह Conformer Model दोनों की ताकतों को मिलाकर एक स्पेशल Macaron Style Block बनाता है। इस ब्लॉक में एक नहीं, बल्कि दो half step Feed Forward Modules के बीच में Multi Head Self Attention और Convolution Module को सैंडविच किया जाता है! इसका Convolution module Depthwise Separable Convolutions यूज़ करके स्पीच सिग्नल के लोकल पेटर्न्स प्रोसेस करता है, और Multi Head Self Attention में Relative Positional Encoding ऐड करके यह सेंटेंस के दूर-दराज शब्दों को कनेक्ट करता है। Pipeline में सबसे पहले Audio Mel Spectrogram Convolutional Subsampling के ज़रिए कम रिज़ॉल्यूशन में कंप्रेस होता है, फिर multiple Conformer blocks से गुजरकर CTC Decoder की मदद से सुपर एक्यूरेट Text Tokens जनरेट करता है! यही वजह है कि Whisper, NeMo और आधुनिक ASR सिस्टम्स Conformer का यूज़ करते हैं! ऐसे ही AI Breakdowns के लिए अभी Follow करें!

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
            f"Generate a 60-second video script and matching TTS script following the working example provided in the template."
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
