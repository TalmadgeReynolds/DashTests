import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

def synthesize_answer(results, query, user_profile=None, context_boost=None):
    """
    Generate a synthesized, insightful, and action-oriented answer from top TED talk results.
    
    Args:
        results (list): Search results, each with 'title', 'speaker', 'description', 'content', 'views'
        query (str): The user's original question
        user_profile (dict, optional): Personalization (e.g., roles, interests, history)
        context_boost (str, optional): Custom narrative context or hook for framing (e.g., "performance trends", "editor accountability")

    Returns:
        str: A well-crafted prompt ready for completion by an LLM.
    """
    if not results:
        return "No relevant results were found to synthesize a response."

    # Optional personalization layer
    role_context = ""
    if user_profile:
        if user_profile.get("role") == "Editor":
            role_context = "Focus on insights relevant to editing decisions and clip structuring."
        elif user_profile.get("role") == "Producer":
            role_context = "Focus on production pacing, storytelling, and audience retention."
        elif user_profile.get("role") == "Admin":
            role_context = "Highlight patterns, performance metrics, and decision-making insights."

    # Extract and prioritize top content
    top_content = sorted(
        [{
            'title': r['title'],
            'speaker': r['speaker'],
            'description': r.get('description', ''),
            'content': r.get('content', ''),
            'views': r.get('views', 0)
        } for r in results[:10]], 
        key=lambda x: x['views'], reverse=True
    )

    # Prep combined source material for LLM summarization
    combined_insights = "\n\n".join([
        f"Talk: {c['title']}\nSpeaker: {c['speaker']}\n{c['content']}"
        for c in top_content
    ])

    # Limit combined insights to ~8000 tokens (approximate)
    max_chars = 32000  # rough estimate of 8000 tokens
    if len(combined_insights) > max_chars:
        combined_insights = combined_insights[:max_chars] + "...[content truncated]"

    # Smart context tagging (expandable with AI later)
    if context_boost:
        context_hint = f"\nContextual Focus: {context_boost.strip()}"
    else:
        context_hint = ""

    # SYSTEM message that guides the LLM tone, depth, and purpose
    system_message = f"""You are a domain-expert AI that synthesizes deep, multi-perspective insights from TED talks.
{role_context}
{context_hint}

Your mission:
- Extract the most compelling, nuanced ideas
- Cross-reference themes across multiple speakers
- Detect contradictions or consensus
- highlight themes & concepts that cross multiple studies or fields
- Include named examples, data points, or quotes
- Present your findings in an engaging, analytical style for a knowledgeable audience
"""

    # Prompt template with restructured guidelines
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"""{system_message}

RESPONSE FORMAT REQUIREMENTS (MANDATORY):
1. Multi-perspective analysis: Compare and contrast viewpoints from different speakers
2. Evidence-based: Include at least 3 specific quotes or examples (with speaker attribution)
3. Analytical depth: Go beyond summary to implications and applications
4. Structure: 10-12 sentences of clear, confident analysis
5. Follow-up: End with exactly 2 recommended follow-up questions

You MUST follow these requirements in your response."""),
        
        ("human", f"""Question: "{query}"

Source Material:
{combined_insights}

Remember to identify shared/diverging ideas, use specific examples, analyze (don't just summarize), 
and maintain a clear, confident tone throughout your response.""")
    ])
    
    try:
        # Create the chat model
        chat = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.3)
        
        # Format the messages before invoking the model
        messages = prompt_template.format_messages(
            query=query,
            combined_insights=combined_insights
        )
        
        # Now pass the formatted messages to invoke()
        response = chat.invoke(messages)
        
        content = response.content.strip()
        if not content:
            return "Unable to generate insights from the provided talks."
        return content
    except Exception as e:
        logging.error(f"Answer synthesis failed: {str(e)}")
        return "I encountered an issue while analyzing the TED talks. Please try again."