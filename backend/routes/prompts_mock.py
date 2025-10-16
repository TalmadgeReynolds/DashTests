"""
Mock implementation for prompt sharpening for testing without API keys.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import os
import difflib
import random
from typing import List, Optional, Literal

router = APIRouter(prefix="/prompts", tags=["prompts"])

# Schemas
class SharpenRequest(BaseModel):
    original: str = Field(..., min_length=3, max_length=2000, description="Original prompt to sharpen")
    model: Literal["gpt", "claude", "both"] = Field("both", description="Which LLM to use: gpt, claude, or both")
    variants: int = Field(3, ge=1, le=6, description="Number of variants to generate")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Sampling temperature (lower = more deterministic)")
    max_tokens: int = Field(200, ge=50, le=500, description="Maximum tokens per variant")


class VariantOut(BaseModel):
    text: str = Field(..., description="Sharpened prompt text")
    source: str = Field(..., description="Model that generated this variant (gpt or claude)")
    score: float = Field(..., description="Overall quality score (0-1)")
    similarity: float = Field(..., description="Semantic similarity to original (0-1)")
    diff: str = Field(..., description="Human-readable diff showing changes")


class SharpenResponse(BaseModel):
    original: str = Field(..., description="Original input prompt")
    variants: List[VariantOut] = Field(..., description="Ranked list of sharpened variants")


def simple_diff(original: str, rewritten: str) -> str:
    """Generate a human-readable diff between two strings."""
    seq = difflib.SequenceMatcher(a=original, b=rewritten)
    result = []
    
    for tag, i1, i2, j1, j2 in seq.get_opcodes():
        if tag == "equal":
            result.append(original[i1:i2])
        elif tag == "replace":
            result.append(f"[-{original[i1:i2]}-]{{+{rewritten[j1:j2]}+}}")
        elif tag == "delete":
            result.append(f"[-{original[i1:i2]}-]")
        elif tag == "insert":
            result.append(f"{{+{rewritten[j1:j2]}+}}")
    
    return "".join(result)


def get_mock_variant(original: str, source: str, index: int) -> str:
    """Generate mock variants with cinematic details."""
    mock_variants = {
        "gpt": [
            f"Medium close-up, subject centered, professional lighting. Subject speaks directly to camera: \"{original}\" Natural facial expressions, occasional hand gestures for emphasis.",
            f"Close-up shot, soft key light from 45-degrees, shallow depth of field. Subject explains: \"{original}\" with confident tone and subtle head movements.",
            f"Medium shot, even lighting, clean background. Subject demonstrates clearly: \"{original}\" with deliberate hand movements showing app interface."
        ],
        "claude": [
            f"Professional medium shot, subject centered, warm frontal lighting. Subject explains with clarity: \"{original}\" while using appropriate hand gestures to emphasize key points.",
            f"Tight frame on subject, soft diffused lighting, neutral background. Subject walks through \"{original}\" with occasional zoom cuts to highlight important app features.",
            f"Medium close-up, subject positioned slightly off-center, soft key light. Subject speaks with enthusiasm: \"{original}\" while occasionally glancing at device in hand."
        ]
    }
    
    variant_list = mock_variants.get(source, ["Error generating variant"])
    return variant_list[index % len(variant_list)]


@router.post("/sharpen", response_model=SharpenResponse)
async def sharpen_prompt(request: SharpenRequest, req: Request):
    """
    Mock implementation of prompt sharpening.
    Returns pre-defined variants with random scores for testing.
    """
    variants = []
    
    # Generate variants based on requested models
    if request.model in ("gpt", "both"):
        count = request.variants if request.model == "gpt" else max(1, request.variants // 2)
        for i in range(count):
            text = get_mock_variant(request.original, "gpt", i)
            score = random.uniform(0.7, 0.95)
            similarity = random.uniform(0.6, 0.9)
            variants.append(VariantOut(
                text=text,
                source="gpt",
                score=round(score, 4),
                similarity=round(similarity, 4),
                diff=simple_diff(request.original, text)
            ))
    
    if request.model in ("claude", "both"):
        count = request.variants if request.model == "claude" else max(1, request.variants // 2)
        for i in range(count):
            text = get_mock_variant(request.original, "claude", i)
            score = random.uniform(0.7, 0.95)
            similarity = random.uniform(0.6, 0.9)
            variants.append(VariantOut(
                text=text,
                source="claude",
                score=round(score, 4),
                similarity=round(similarity, 4),
                diff=simple_diff(request.original, text)
            ))
    
    # Sort by score descending
    variants.sort(key=lambda v: v.score, reverse=True)
    
    return SharpenResponse(
        original=request.original,
        variants=variants[:request.variants]
    )


@router.get("/health")
async def health_check():
    """Check availability of LLM providers."""
    return {
        "openai_available": True,
        "openai_model": "gpt-4o-mock",
        "claude_available": True,
        "claude_model": "claude-3-5-sonnet-mock",
    }