"""Plant health diagnosis using Claude's vision + structured outputs."""

from __future__ import annotations

import base64
from typing import List, Literal, Optional

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


# ---------- Output schema (what the UI renders) ----------

class NextStep(BaseModel):
    priority: Literal["now", "this_week", "ongoing"]
    action: str = Field(description="One concrete, doable action for a home gardener")
    why: str = Field(description="One short sentence on why this helps")


class Diagnosis(BaseModel):
    image_usable: bool = Field(
        description="False if the photo is too blurry/dark or does not show a plant clearly"
    )
    retake_advice: Optional[str] = Field(
        description="If image_usable is false, how to take a better photo; otherwise null"
    )
    plant_identified: str = Field(description="Common name of the plant seen in the photo")
    matches_user_input: bool = Field(
        description="Whether the photo matches the plant name the user gave (true if user gave none)"
    )
    health_status: Literal["healthy", "mild_issue", "unhealthy", "critical"]
    health_score: int = Field(description="0 (dying) to 100 (thriving)")
    confidence: Literal["low", "medium", "high"]
    summary: str = Field(description="One-line verdict a non-expert understands")
    current_state: str = Field(description="What is visibly happening to the plant right now")
    observed_symptoms: List[str]
    likely_causes: List[str]
    next_steps: List[NextStep]
    location_specific_tips: str = Field(
        description="Advice specific to where the plant is grown (terrace, balcony, farm, ...)"
    )
    green_tip: str = Field(
        description="One eco-friendly practice relevant to this plant: composting, water saving, "
        "natural pest control, biodiversity, etc."
    )
    when_to_seek_expert: str


# ---------- Prompt ----------

SYSTEM_PROMPT = """You are an experienced, friendly plant doctor helping everyday growers - mostly
home gardeners on terraces, balconies and gardens, but also small farmers.

Look carefully at the photo(s) and the details the user gives, then diagnose the plant's health.

Guidelines:
- Base the diagnosis on what is actually visible. If something is uncertain, say so and lower
  the confidence rather than guessing.
- Use the growing location as context: terraces and balconies mean pots, heat, wind and
  drainage issues; indoor means low light and overwatering; farms mean field-scale pests and soil.
- Prefer organic, low-cost and eco-friendly remedies first (neem oil, pruning, compost, mulching,
  companion planting, better watering). Mention chemical treatment only when really needed,
  and then as a last resort with safety notes.
- Next steps must be practical and specific (quantities, frequency, timing), ordered by urgency.
  Give 3-6 steps. A healthy plant still gets maintenance steps.
- If the photo is unusable, set image_usable=false, explain how to retake it, and fill the other
  fields with your best cautious guess at low confidence.
- If the plant in the photo differs from what the user named, set matches_user_input=false and
  diagnose the plant you actually see.
- Write all text fields in the language requested by the user. Keep wording simple."""


def _build_user_text(
    plant_name: str,
    location: str,
    language: str,
    pot_or_ground: str,
    watering: str,
    notes: str,
    organic_only: bool,
) -> str:
    lines = [
        f"Plant (as named by user): {plant_name or 'Not sure - please identify it'}",
        f"Growing location: {location}",
    ]
    if pot_or_ground:
        lines.append(f"Planted in: {pot_or_ground}")
    if watering:
        lines.append(f"Watering routine: {watering}")
    if notes:
        lines.append(f"User's notes / symptoms noticed: {notes}")
    lines.append(
        "Remedy preference: ORGANIC ONLY - do not suggest synthetic chemicals."
        if organic_only
        else "Remedy preference: organic first, chemical only if necessary."
    )
    lines.append(f"Respond in: {language}")
    return "\n".join(lines)


class DiagnosisError(Exception):
    pass


def diagnose_plant(
    images: List[tuple[bytes, str]],
    plant_name: str = "",
    location: str = "Garden",
    language: str = "English",
    pot_or_ground: str = "",
    watering: str = "",
    notes: str = "",
    organic_only: bool = False,
) -> Diagnosis:
    """images: list of (raw_bytes, media_type)."""
    content: list = []
    for data, media_type in images:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64.standard_b64encode(data).decode("utf-8"),
                },
            }
        )
    content.append(
        {
            "type": "text",
            "text": _build_user_text(
                plant_name, location, language, pot_or_ground, watering, notes, organic_only
            ),
        }
    )

    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
        output_format=Diagnosis,
        output_config={"effort": "medium"},
        # If a safety classifier declines, retry server-side on Anthropic's recommended model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    if response.stop_reason == "refusal":
        raise DiagnosisError("The model declined to analyse this image. Please try another photo.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise DiagnosisError("The analysis was incomplete. Please try again.")
    return response.parsed_output
