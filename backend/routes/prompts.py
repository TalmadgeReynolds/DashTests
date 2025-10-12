"""
Prompt sharpening endpoints using OpenAI GPT-4o and Anthropic Claude.
Allows users to choose their preferred LLM for rewriting prompts.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
import difflib
import numpy as np
from typing import List, Optional, Literal
import logging

# Import clients
import openai
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

from backend.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/prompts", tags=["prompts"])

# Configuration from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# Initialize clients
openai.api_key = OPENAI_API_KEY
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if (ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY) else None


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


# Prompts and few-shot examples
SYSTEM_PROMPT = """You are an expert prompt editor for AI video generation systems. Your task is to rewrite user prompts to be clearer, more actionable, and optimized for text-to-video or image-to-video generation.

Rules:
1. Preserve the original intent and key message exactly
2. Add explicit visual/cinematic details: shot type, framing, lighting, camera movement
3. Specify subject positioning and motion (e.g., "centered", "slight head tilt")
4. Make dialogue explicit with quotes when applicable
5. Keep language concise and production-ready
6. Include negative cues when helpful (what to avoid)
7. Maximum clarity for AI video models like Veo 3 or Heygen

Output format: Return only the rewritten prompt, nothing else."""

FEW_SHOT_EXAMPLES = """
Example 1:
Original: "A person talking about shipping a new product"
Rewritten: "Tight medium close-up, subject centered, soft frontal key light, shallow depth of field. Subject speaks clearly: 'We finally shipped the feature, and it actually works.' Natural micro head motion, slight smile. Avoid exaggerated gestures."

Example 2:
Original: "Happy excited announcement"
Rewritten: "Close-up shot, bright key light, energetic delivery. Subject centered, slight forward lean. Speaks: 'I'm so excited to share this with you!' Big authentic smile, occasional blink. Steady eye contact with camera."

Example 3:
Original: "Professional business presentation style"
Rewritten: "Medium shot, professional setting, neutral background. Subject centered, confident posture. Speaks clearly: 'Let me walk you through our quarterly results.' Minimal hand gestures, steady gaze, occasional nod for emphasis."
"""


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


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two embedding vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


async def generate_with_openai(original: str, n: int, temperature: float, max_tokens: int) -> List[str]:
    """Generate variants using OpenAI GPT models."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + FEW_SHOT_EXAMPLES},
            {"role": "user", "content": f"Original prompt:\n{original}\n\nRewrite this prompt following the rules above."}
        ]
        
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            n=n,
            max_tokens=max_tokens,
        )
        
        variants = []
        for choice in response.choices:
            text = choice.message.get("content", "").strip()
            if text:
                variants.append(text)
        
        logger.info("openai_generate_success", count=len(variants), model=OPENAI_MODEL)
        return variants
        
    except openai.error.OpenAIError as e:
        logger.error("openai_generate_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")


async def generate_with_claude(original: str, n: int, temperature: float, max_tokens: int) -> List[str]:
    """Generate variants using Anthropic Claude."""
    if not anthropic_client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured or library not installed")
    
    try:
        variants = []
        
        # Claude doesn't support n parameter, so we make multiple calls
        for i in range(n):
            response = anthropic_client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=SYSTEM_PROMPT + "\n\n" + FEW_SHOT_EXAMPLES,
                messages=[
                    {
                        "role": "user",
                        "content": f"Original prompt:\n{original}\n\nRewrite this prompt following the rules above."
                    }
                ]
            )
            
            if response.content and len(response.content) > 0:
                text = response.content[0].text.strip()
                if text:
                    variants.append(text)
        
        logger.info("claude_generate_success", count=len(variants), model=ANTHROPIC_MODEL)
        return variants
        
    except Exception as e:
        logger.error("claude_generate_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")


async def score_variants(original: str, variants: List[tuple[str, str]]) -> List[VariantOut]:
    """Score and rank variants using embeddings."""
    if not OPENAI_API_KEY:
        # Fallback: return unscored variants
        logger.warning("openai_key_missing", message="Cannot score variants without OpenAI key")
        return [
            VariantOut(
                text=text,
                source=source,
                score=0.5,
                similarity=0.5,
                diff=simple_diff(original, text)
            )
            for source, text in variants
        ]
    
    try:
        # Get embeddings for original and all variants
        texts_to_embed = [original] + [text for _, text in variants]
        
        response = openai.Embedding.create(
            model=OPENAI_EMBED_MODEL,
            input=texts_to_embed
        )
        
        embeddings = [item["embedding"] for item in response["data"]]
        original_embedding = embeddings[0]
        variant_embeddings = embeddings[1:]
        
        # Score each variant
        scored_variants = []
        for (source, text), embedding in zip(variants, variant_embeddings):
            # Calculate similarity to original (preserve intent)
            similarity = cosine_similarity(original_embedding, embedding)
            
            # Heuristic penalties/bonuses
            length_ratio = len(text) / max(len(original), 1)
            length_penalty = max(0, (length_ratio - 2.0) * 0.1)  # Penalize if > 2x original length
            
            # Bonus for adding visual details (keywords)
            visual_keywords = ["close-up", "medium shot", "centered", "light", "motion", "framing", "shot"]
            detail_bonus = sum(0.02 for kw in visual_keywords if kw.lower() in text.lower())
            detail_bonus = min(detail_bonus, 0.15)  # Cap at 0.15
            
            # Final score: similarity (most important) + detail bonus - length penalty
            score = similarity + detail_bonus - length_penalty
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            
            scored_variants.append(VariantOut(
                text=text,
                source=source,
                score=round(score, 4),
                similarity=round(similarity, 4),
                diff=simple_diff(original, text)
            ))
        
        # Sort by score descending
        scored_variants.sort(key=lambda v: v.score, reverse=True)
        
        logger.info("variants_scored", count=len(scored_variants))
        return scored_variants
        
    except Exception as e:
        logger.error("scoring_error", error=str(e))
        # Fallback: return unscored
        return [
            VariantOut(
                text=text,
                source=source,
                score=0.5,
                similarity=0.5,
                diff=simple_diff(original, text)
            )
            for source, text in variants
        ]


@router.post("/sharpen", response_model=SharpenResponse)
async def sharpen_prompt(request: SharpenRequest):
    """
    Sharpen a prompt using GPT-4o and/or Claude.
    
    Returns ranked variants with quality scores and diffs.
    Users can choose which model(s) to use via the 'model' parameter.
    """
    logger.info(
        "sharpen_request",
        model=request.model,
        variants=request.variants,
        original_length=len(request.original)
    )
    
    # Collect variants from requested models
    all_variants = []
    
    if request.model in ("gpt", "both"):
        try:
            gpt_variants = await generate_with_openai(
                request.original,
                request.variants if request.model == "gpt" else max(1, request.variants // 2),
                request.temperature,
                request.max_tokens
            )
            all_variants.extend([("gpt", v) for v in gpt_variants])
        except HTTPException as e:
            if request.model == "gpt":
                raise  # If GPT-only requested and it fails, propagate error
            logger.warning("gpt_fallback", error=str(e))
    
    if request.model in ("claude", "both"):
        try:
            claude_variants = await generate_with_claude(
                request.original,
                request.variants if request.model == "claude" else max(1, request.variants // 2),
                request.temperature,
                request.max_tokens
            )
            all_variants.extend([("claude", v) for v in claude_variants])
        except HTTPException as e:
            if request.model == "claude":
                raise  # If Claude-only requested and it fails, propagate error
            logger.warning("claude_fallback", error=str(e))
    
    if not all_variants:
        raise HTTPException(
            status_code=502,
            detail="Failed to generate variants from any model"
        )
    
    # Deduplicate variants (same text from different models)
    seen_texts = set()
    unique_variants = []
    for source, text in all_variants:
        text_normalized = text.strip().lower()
        if text_normalized not in seen_texts:
            seen_texts.add(text_normalized)
            unique_variants.append((source, text))
    
    # Score and rank
    scored_variants = await score_variants(request.original, unique_variants)
    
    # Limit to requested number
    final_variants = scored_variants[:request.variants]
    
    logger.info(
        "sharpen_success",
        total_variants=len(final_variants),
        top_score=final_variants[0].score if final_variants else 0
    )
    
    return SharpenResponse(
        original=request.original,
        variants=final_variants
    )


@router.get("/health")
async def health_check():
    """Check availability of LLM providers."""
    return {
        "openai_available": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL if OPENAI_API_KEY else None,
        "claude_available": bool(anthropic_client),
        "claude_model": ANTHROPIC_MODEL if anthropic_client else None,
    }
