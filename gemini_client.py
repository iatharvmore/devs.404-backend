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

# ── CONFIG ── do NOT change these four lines ──────────────────────────────────
config.pixel_height  = 1920
config.pixel_width   = 720
config.frame_height  = 16.0    # Manim units tall  → y ∈ [-8.0, +8.0]
config.frame_width   = 9.0     # Manim units wide  → x ∈ [-4.5, +4.5]
config.background_color = WHITE

# ── SAFE AREA ── ALL content must live inside these bounds ───────────────────
# The Instagram Reels UI overlays ~20% at the bottom (like/comment bar, caption)
# and ~10% at the top (back arrow). Keep content strictly within:
#   X : -3.4  to  +3.4   (leaving 1.1 units of padding on each side)
#   Y : -4.8  to  +6.8   (leaving 3.2 at bottom for IG UI, 1.2 at top)
SAFE_X    = 3.4    # max |x| value
SAFE_Y_T  = 6.8    # max y (top)
SAFE_Y_B  = -4.8   # min y (bottom — avoids IG like/comment overlay)
MAX_W     = 2 * SAFE_X - 0.4   # = 6.4  max width for any Text or shape

# ── FONTS ────────────────────────────────────────────────────────────────────
F_TITLE   = 52   # Scene title  (one per scene, bold)
F_HEADING = 40   # Section heading
F_BODY    = 32   # Regular body text
F_SMALL   = 24   # Labels / footnotes — never go below 24

# ── COLORS ── use only these on a WHITE background ───────────────────────────
C_TITLE   = "#0f172a"   # near-black
C_BODY    = "#1e293b"   # dark slate
C_ACCENT  = "#6366f1"   # indigo
C_GREEN   = "#059669"   # emerald
C_RED     = "#dc2626"   # red
C_MUTED   = "#64748b"   # slate-gray for secondary text

def safe_text(text_str, font_size, color, **kwargs):
    """Create a Text that is guaranteed to fit inside MAX_W."""
    t = Text(text_str, font_size=font_size, color=color, **kwargs)
    if t.width > MAX_W:
        t.scale_to_fit_width(MAX_W)
    return t

def wrap_text(text_str, font_size, color, max_width=MAX_W, **kwargs):
    """
    For long strings: break at word boundaries to keep each line <= max_width.
    Returns a VGroup of Text lines arranged with buff=0.25 downward.
    """
    words = text_str.split()
    lines, current = [], ""
    probe = Text("A", font_size=font_size, color=color)
    char_w = probe.width  # approximate width per char at this font size
    chars_per_line = max(10, int(max_width / (char_w * 0.55)))
    for word in words:
        if len(current) + len(word) + 1 <= chars_per_line:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    objs = [Text(l, font_size=font_size, color=color, **kwargs) for l in lines]
    for o in objs:
        if o.width > max_width:
            o.scale_to_fit_width(max_width)
    group = VGroup(*objs).arrange(DOWN, buff=0.25)
    return group


class TopicScene(Scene):
    def construct(self):
        # ── PHASE 1 : Title card   [0s – 6s] ─────────────────────────────────
        title = safe_text("Topic Title Here", F_TITLE, C_TITLE, weight=BOLD)
        title.move_to(UP * 6.0)   # near top, inside SAFE_Y_T

        subtitle = safe_text("Hindi subtitle / tagline", F_BODY, C_MUTED)
        subtitle.next_to(title, DOWN, buff=0.55)

        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle), run_time=0.8)
        self.wait(3.5)   # ← adjust so sum of animations + waits ≈ phase length

        # ── PHASE 2 : First concept   [6s – 22s] ─────────────────────────────
        heading1 = safe_text("Section 1 Heading", F_HEADING, C_ACCENT, weight=BOLD)
        heading1.move_to(UP * 4.8)   # below title area

        # For multi-line body text, always use wrap_text():
        body1 = wrap_text(
            "First explanation line goes here and wraps automatically if long",
            F_BODY, C_BODY
        )
        body1.next_to(heading1, DOWN, buff=0.55)

        body2 = wrap_text("Second point of the concept", F_BODY, C_BODY)
        body2.next_to(body1, DOWN, buff=0.45)

        # ← Before each self.play(), verify: are all new objects above SAFE_Y_B?
        assert all(o.get_bottom()[1] > SAFE_Y_B for o in [heading1, body1, body2]), \
            "Content extends below safe area bottom! Move elements up."

        self.play(FadeOut(subtitle), run_time=0.4)
        self.play(FadeIn(heading1), run_time=0.5)
        self.play(Write(body1),  run_time=1.8)
        self.play(Write(body2),  run_time=1.5)
        self.wait(9.0)
        self.play(FadeOut(heading1), FadeOut(body1), FadeOut(body2), run_time=0.6)

        # ── PHASE 3 : Second concept   [22s – 40s] ────────────────────────────
        # ... (same pattern — heading near y=4.8, body below it with buff=0.5)

        # ── PHASE 4 : Summary / CTA   [40s – 55s] ────────────────────────────
        summary_heading = safe_text("Summary", F_HEADING, C_GREEN, weight=BOLD)
        summary_heading.move_to(UP * 4.8)

        bullet1 = safe_text("• Key takeaway one", F_BODY, C_BODY)
        bullet1.next_to(summary_heading, DOWN, buff=0.6).align_to(summary_heading, LEFT)

        bullet2 = safe_text("• Key takeaway two", F_BODY, C_BODY)
        bullet2.next_to(bullet1, DOWN, buff=0.4).align_to(bullet1, LEFT)

        self.play(FadeIn(summary_heading), run_time=0.5)
        self.play(FadeIn(bullet1), run_time=0.6)
        self.play(FadeIn(bullet2), run_time=0.6)
        self.wait(12.0)
        self.play(FadeOut(summary_heading), FadeOut(bullet1), FadeOut(bullet2))

        # ── END : hold the last frame for 1 second ────────────────────────────
        self.wait(1.0)


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
• config.pixel_height = 1920, config.pixel_width = 720
• config.frame_height = 16.0, config.frame_width = 9.0   (9:16 vertical)
• config.background_color = WHITE

─── B. SAFE AREA (HARD CONSTRAINTS — never exceed) ─────────────────────────
• ALL objects must have:
    x ∈ [-3.4, +3.4]    — horizontal safe zone (Instagram has none, but be safe)
    y ∈ [-4.8, +6.8]    — vertical safe zone
  The bottom is cut short to -4.8 (not -8.0) because Instagram Reels overlays
  (like/comment/share buttons, username, caption) cover roughly the bottom 20%
  of the screen — anything below y = -4.8 will be hidden.
• title.move_to(UP * 6.0) is the standard top position for a scene title.
• After placing each object, the LOWEST point of that object (get_bottom()[1])
  must be > -4.8. Add an assert in your code to catch violations.
• NEVER use get_center() ± large offsets that push objects out of the safe area.

─── C. FONT SIZES (hard caps) ───────────────────────────────────────────────
• Scene title        : F_TITLE  = 52   (bold, one per scene)
• Section headings   : F_HEADING = 40
• Body text          : F_BODY   = 32
• Labels / footnotes : F_SMALL  = 24   ← MINIMUM — never go below 24
• If a Text object exceeds MAX_W = 6.4 in width, call scale_to_fit_width(6.4)
  on it — never let text go wider than MAX_W.

─── D. TEXT WRAPPING (required for any sentence > ~5 words) ─────────────────
• Use the wrap_text() helper from the template for ALL body content strings.
• NEVER put a long sentence in a single Text object without wrapping.
• Break long concepts into 2–3 short lines, each ≤ 6–7 words.
• Lines in a section must be stacked with VGroup(...).arrange(DOWN, buff=0.3).

─── E. VERTICAL SPACING (mandatory minimums) ────────────────────────────────
• buff between title and first section heading : 0.5 – 0.7
• buff between heading and first body line     : 0.45 – 0.65
• buff between successive body lines           : 0.3 – 0.45
• buff between two separate VGroups/sections   : 0.5 – 0.8
• NEVER use buff < 0.25 anywhere.
• Leave at least 1.5 units of empty space at the BOTTOM of each phase so
  the Instagram caption overlay doesn't clash with content.

─── F. NO OVERLAP RULE ──────────────────────────────────────────────────────
• Before every self.play(), mentally verify: are all CURRENTLY VISIBLE objects
  non-overlapping? If you FadeOut old objects, they are no longer visible.
• NEVER add a new object whose bounding box intersects an already-visible one.

─── G. TIMING (total 55 – 70 s) ─────────────────────────────────────────────
• Annotate every phase with its time range in a comment:  # [0s – 6s]
• Include the wait() call that fills the remaining time in that phase.
• Typical phase lengths:
    Title card    : 5 – 8 s
    Each concept  : 12 – 18 s
    Summary / CTA : 10 – 14 s
    Final hold    : 1 – 2 s
• Total must be 55 – 70 s. Calculate by summing all run_time + wait() values.

─── H. STABILITY RULES (prevent runtime crashes) ────────────────────────────
1. NEVER use Transform(), ReplacementTransform(), TransformMatchingShapes()
   or TransformMatchingTex() on Text, MathTex, or Tex objects.
2. NEVER directly transform one Text into another Text with different words.
3. To change text: FadeOut(old), then FadeIn(new) — always.
4. .animate.shift(), .animate.scale(), .animate.move_to() are fine.
5. Do NOT change the submobject count of any Mobject during animation.
6. Prefer: FadeIn, FadeOut, Write, Create, GrowArrow, Indicate.
7. No deprecated methods (e.g. .set_width() on Text in an animation context).
8. Never use non-existent Manim classes. For checkmarks use Text('✓') or
   MathTex(r'\\checkmark'). For crosses use Cross() or Text('✗').
9. Every object placed on screen must be explicitly FadeOut-ed before a new
   object is placed at a nearby position in the next phase.

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

Example format:
  [0s] आज हम सीखेंगे Chain of Thought Prompting के बारे में — एक technique
  जो LLMs को step-by-step सोचने पर मजबूर करती है।
  [6s] पहले देखते हैं बिना CoT के क्या होता है। जब हम LLM को directly पूछते
  हैं...

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
