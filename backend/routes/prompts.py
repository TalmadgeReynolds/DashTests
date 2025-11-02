"""
Prompt sharpening endpoints using OpenAI GPT-4o and Anthropic Claude.
Allows users to choose their preferred LLM for rewriting prompts.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
import difflib
import numpy as np
import json
from typing import List, Optional, Literal, Dict, Tuple, Any
from enum import Enum
import logging

# Import clients
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

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
# Claude Sonnet 4.5 (Sept 2025) - excellent balance of speed and capability
# Alternative: claude-opus-4-1-20250805 (most capable but slower)
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# Initialize clients with timeout configuration
openai_client = OpenAI(api_key=OPENAI_API_KEY, timeout=30.0) if (OPENAI_AVAILABLE and OPENAI_API_KEY) else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY, timeout=60.0) if (ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY) else None


# Schemas
class EmphasisLayer(str, Enum):
    DESCRIPTIVE = "descriptive"
    DYNAMIC = "dynamic" 
    CINEMATIC = "cinematic"
    CONCEPTUAL = "conceptual"

class SharpenRequest(BaseModel):
    original: str = Field(..., min_length=3, max_length=2000, description="Original prompt to sharpen")
    model: Literal["gpt", "claude", "both"] = Field("both", description="Which LLM to use: gpt, claude, or both")
    variants: int = Field(3, ge=1, le=6, description="Number of variants to generate")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Sampling temperature (lower = more deterministic)")
    max_tokens: int = Field(200, ge=50, le=2000, description="Maximum tokens per variant")
    structured: bool = Field(False, description="Whether to generate structured creative elements")
    emphasis: Optional[List[EmphasisLayer]] = Field(None, description="Layers to emphasize: descriptive, dynamic, cinematic, conceptual")


class CreativeElement(BaseModel):
    character: Optional[str] = Field(None, description="Character traits, emotion, wardrobe, and role")
    action: Optional[str] = Field(None, description="What the character(s) are doing; physical movement and gestures")
    expression: Optional[str] = Field(None, description="Mood, tone, or energy in the scene")
    camera: Optional[str] = Field(None, description="Framing, motion, and shot style")
    location: Optional[str] = Field(None, description="Where the scene takes place, atmosphere, time of day, lighting")
    art_direction: Optional[str] = Field(None, description="Cinematic style, color palette, lens type, visual mood")
    dialogue: Optional[str] = Field(None, description="Spoken text or narrative meaning")
    context: Optional[str] = Field(None, description="Implicit cues, subtext, symbolism, genre, or pacing")

class VariantOut(BaseModel):
    text: str = Field(..., description="Sharpened prompt text")
    source: str = Field(..., description="Model that generated this variant (gpt or claude)")
    score: float = Field(..., description="Overall quality score (0-1)")
    similarity: float = Field(..., description="Semantic similarity to original (0-1)")
    diff: str = Field(..., description="Human-readable diff showing changes")
    elements: Optional[CreativeElement] = Field(None, description="Structured creative elements")
    model_optimized: Optional[str] = Field(None, description="Version optimized for generation models")


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

STRUCTURED_SYSTEM_PROMPT = """You are an expert prompt engineer for AI video and image generation. Your task is to analyze and transform text into structured, production-ready prompts optimized for multimodal AI models like Runway, Veo, Wan, and Seedance.

Your goal is to deconstruct the provided text (often from screenplays, scripts, or creative briefs) into distinct creative elements, and then recombine them into a highly effective prompt.

ANALYZE THE TEXT FOR THESE ELEMENTS:
1. Character – who is present, including traits, emotion, wardrobe, and role
2. Action – what the character(s) are doing; physical movement, gestures, and micro-actions
3. Expression/Emotion – mood, tone, or energy in the scene
4. Camera/Movement – framing, motion (dolly, pan, handheld), shot style
5. Location/Environment – where the scene takes place, atmosphere, time of day, lighting, weather
6. Art Direction/Style – cinematic style, color palette, lens type, visual mood
7. Dialogue/Narrative Intent – spoken text or narrative meaning (if present)
8. Other Context – implicit cues (subtext, symbolism, genre, pacing) that enhance AI understanding

PROVIDE OUTPUT IN THIS FORMAT:
```json
{
  "elements": {
    "character": "Description of character(s)",
    "action": "Description of action/movement",
    "expression": "Description of emotional tone/expression",
    "camera": "Description of framing and camera work",
    "location": "Description of setting and environment",
    "art_direction": "Description of visual style",
    "dialogue": "Any spoken text (if applicable)",
    "context": "Additional context, subtext, or symbolic elements"
  },
  "human_readable": "Complete, coherent prompt optimized for human readability and editing",
  "model_optimized": "Streamlined version optimized for direct input to AI models"
}
```"""

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


async def generate_with_openai(
    original: str, 
    n: int, 
    temperature: float, 
    max_tokens: int,
    structured: bool = False,
    emphasis: Optional[List[EmphasisLayer]] = None
) -> List[tuple[str, Optional[dict]]]:
    """Generate variants using OpenAI GPT models."""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        if structured:
            # For structured prompts, we need to use a different system prompt
            emphasis_instruction = ""
            if emphasis:
                emphasis_map = {
                    "descriptive": "nouns and adjectives, focus on describing the scene and characters in detail",
                    "dynamic": "verbs and motion, focus on actions and movements",
                    "cinematic": "camera work, lighting, and tone",
                    "conceptual": "theme, symbolism, and emotional intent"
                }
                emphasis_layers = [emphasis_map.get(layer, "") for layer in emphasis if layer in emphasis_map]
                if emphasis_layers:
                    emphasis_instruction = f"\n\nPUT SPECIAL EMPHASIS ON: {', '.join(emphasis_layers)}"
            
            messages = [
                {"role": "system", "content": STRUCTURED_SYSTEM_PROMPT + emphasis_instruction},
                {"role": "user", "content": f"Text to analyze:\n{original}\n\nPlease transform this into a structured prompt."}
            ]
            
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                n=n,
                max_tokens=max(max_tokens, 800),  # Structured output needs more tokens
                response_format={"type": "json_object"}
            )
            
            variants = []
            for choice in response.choices:
                content = choice.message.content.strip()
                if content:
                    try:
                        parsed = json.loads(content)
                        human_readable = parsed.get("human_readable", "")
                        elements = parsed.get("elements", {})
                        model_optimized = parsed.get("model_optimized", "")
                        
                        if human_readable:
                            variants.append((human_readable, {
                                "elements": elements,
                                "model_optimized": model_optimized
                            }))
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        variants.append((content, None))
            
        else:
            # Standard prompt sharpening
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + FEW_SHOT_EXAMPLES},
                {"role": "user", "content": f"Original prompt:\n{original}\n\nRewrite this prompt following the rules above."}
            ]
            
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                n=n,
                max_tokens=max_tokens,
            )
            
            variants = []
            for choice in response.choices:
                text = choice.message.content.strip()
                if text:
                    variants.append((text, None))
        
        logger.info("openai_generate_success", count=len(variants), model=OPENAI_MODEL, structured=structured)
        return variants
        
    except Exception as e:
        logger.error("openai_generate_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")


async def generate_with_claude(
    original: str, 
    n: int, 
    temperature: float, 
    max_tokens: int,
    structured: bool = False,
    emphasis: Optional[List[EmphasisLayer]] = None
) -> List[Tuple[str, Optional[Dict[str, Any]]]]:
    """Generate variants using Anthropic Claude."""
    if not anthropic_client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured or library not installed")
    
    try:
        variants = []
        
        # Claude doesn't support n parameter, so we make multiple sequential calls
        # Note: This can be slow for large n values (3-10 seconds per call)
        logger.info("claude_generate_start", count=n, model=ANTHROPIC_MODEL)
        
        for i in range(n):
            if structured:
                # For structured prompts
                emphasis_instruction = ""
                if emphasis:
                    emphasis_map = {
                        EmphasisLayer.DESCRIPTIVE: "nouns and adjectives, focus on describing the scene and characters in detail",
                        EmphasisLayer.DYNAMIC: "verbs and motion, focus on actions and movements",
                        EmphasisLayer.CINEMATIC: "camera work, lighting, and tone",
                        EmphasisLayer.CONCEPTUAL: "theme, symbolism, and emotional intent"
                    }
                    emphasis_layers = [emphasis_map.get(layer, "") for layer in emphasis if layer in emphasis_map]
                    if emphasis_layers:
                        emphasis_instruction = f"\n\nPUT SPECIAL EMPHASIS ON: {', '.join(emphasis_layers)}"
                
                response = anthropic_client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=max(max_tokens, 800),  # Structured output needs more tokens
                    temperature=temperature,
                    system=STRUCTURED_SYSTEM_PROMPT + emphasis_instruction,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Text to analyze:\n{original}\n\nPlease transform this into a structured prompt."
                        }
                    ]
                )
                
                if response.content and len(response.content) > 0:
                    content = response.content[0].text.strip()
                    if content:
                        try:
                            # Try to extract JSON from the response
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = content[json_start:json_end]
                                parsed = json.loads(json_str)
                                human_readable = parsed.get("human_readable", "")
                                elements = parsed.get("elements", {})
                                model_optimized = parsed.get("model_optimized", "")
                                
                                if human_readable:
                                    variants.append((human_readable, {
                                        "elements": elements,
                                        "model_optimized": model_optimized
                                    }))
                                    continue
                        except (json.JSONDecodeError, ValueError):
                            # Fallback if JSON parsing fails
                            pass
                        
                        # If we got here, either JSON parsing failed or the response wasn't in JSON format
                        variants.append((content, None))
            else:
                # Standard prompt sharpening
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
                        variants.append((text, None))
        
        logger.info("claude_generate_success", count=len(variants), model=ANTHROPIC_MODEL, structured=structured)
        return variants
        
    except Exception as e:
        logger.error("claude_generate_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")


async def score_variants(original: str, variants: List[Tuple[str, Optional[Dict[str, Any]]]]) -> List[VariantOut]:
    """Score and rank variants using embeddings."""
    if not openai_client:
        # Fallback: return unscored variants
        logger.warning("openai_key_missing", message="Cannot score variants without OpenAI key")
        return [
            VariantOut(
                text=text,
                source=source,
                score=0.5,
                similarity=0.5,
                diff=simple_diff(original, text),
                elements=CreativeElement(**metadata["elements"]) if metadata and "elements" in metadata else None,
                model_optimized=metadata["model_optimized"] if metadata and "model_optimized" in metadata else None
            )
            for (source, text), metadata in [(v[0], v[1]) for v in variants]
        ]
    
    try:
        # Get embeddings for original and all variants
        texts_to_embed = [original] + [text for (source, text), _ in variants]
        
        response = openai_client.embeddings.create(
            model=OPENAI_EMBED_MODEL,
            input=texts_to_embed
        )
        
        embeddings = [item.embedding for item in response.data]
        original_embedding = embeddings[0]
        variant_embeddings = embeddings[1:]
        
        # Score each variant
        scored_variants = []
        for ((source, text), metadata), embedding in zip(variants, variant_embeddings):
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
            
            # Handle structured elements if present
            elements = None
            model_optimized = None
            if metadata:
                if "elements" in metadata:
                    elements = CreativeElement(**metadata["elements"])
                if "model_optimized" in metadata:
                    model_optimized = metadata["model_optimized"]
            
            scored_variants.append(VariantOut(
                text=text,
                source=source,
                score=round(score, 4),
                similarity=round(similarity, 4),
                diff=simple_diff(original, text),
                elements=elements,
                model_optimized=model_optimized
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
                diff=simple_diff(original, text),
                elements=CreativeElement(**metadata["elements"]) if metadata and "elements" in metadata else None,
                model_optimized=metadata["model_optimized"] if metadata and "model_optimized" in metadata else None
            )
            for ((source, text), metadata) in variants
        ]


@router.post("/sharpen", response_model=SharpenResponse)
async def sharpen_prompt(request: SharpenRequest):
    """
    Sharpen a prompt using GPT-4o and/or Claude.
    
    Returns ranked variants with quality scores and diffs.
    Users can choose which model(s) to use via the 'model' parameter.
    
    When structured=True, the response will include deconstructed creative elements and an
    optimized version for AI models.
    
    Optional emphasis parameter allows focusing on specific layers:
    - descriptive: Focuses on nouns/adjectives for detailed description
    - dynamic: Focuses on verbs/motion for action-oriented prompts
    - cinematic: Focuses on camera + lighting + tone
    - conceptual: Focuses on theme, symbolism, emotional intent
    """
    logger.info(
        "sharpen_request",
        model=request.model,
        variants=request.variants,
        original_length=len(request.original),
        structured=request.structured,
        emphasis=request.emphasis
    )
    
    # Collect variants from requested models
    all_variants = []
    
    if request.model in ("gpt", "both"):
        try:
            # When using both models, request full count from each to ensure we get enough after deduplication
            # For single model, request exactly what's asked
            gpt_count = request.variants if request.model == "gpt" else request.variants
            gpt_variants = await generate_with_openai(
                request.original,
                gpt_count,
                request.temperature,
                request.max_tokens,
                structured=request.structured,
                emphasis=request.emphasis
            )
            all_variants.extend([("gpt", v[0], v[1]) for v in gpt_variants])
        except HTTPException as e:
            if request.model == "gpt":
                raise  # If GPT-only requested and it fails, propagate error
            logger.warning("gpt_fallback", error=str(e))
    
    if request.model in ("claude", "both"):
        try:
            # Claude makes sequential calls, so limit count to avoid timeouts
            # When using both models, cap at 3 variants from Claude
            # For single model, request exactly what's asked
            if request.model == "claude":
                claude_count = request.variants
            else:
                # Using "both" - limit Claude to 3 to avoid timeout (GPT provides the rest)
                claude_count = min(3, request.variants)
            
            claude_variants = await generate_with_claude(
                request.original,
                claude_count,
                request.temperature,
                request.max_tokens,
                structured=request.structured,
                emphasis=request.emphasis
            )
            all_variants.extend([("claude", v[0], v[1]) for v in claude_variants])
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
    for source, text, metadata in all_variants:
        text_normalized = text.strip().lower()
        if text_normalized not in seen_texts:
            seen_texts.add(text_normalized)
            unique_variants.append(((source, text), metadata))
    
    # Score and rank
    scored_variants = await score_variants(request.original, unique_variants)
    
    # Limit to requested number
    final_variants = scored_variants[:request.variants]
    
    logger.info(
        "sharpen_success",
        total_variants=len(final_variants),
        top_score=final_variants[0].score if final_variants else 0,
        structured=request.structured
    )
    
    return SharpenResponse(
        original=request.original,
        variants=final_variants
    )


@router.get("/health")
async def health_check():
    """Check availability of LLM providers."""
    return {
        "openai_available": bool(openai_client),
        "openai_model": OPENAI_MODEL if openai_client else None,
        "claude_available": bool(anthropic_client),
        "claude_model": ANTHROPIC_MODEL if anthropic_client else None,
    }
