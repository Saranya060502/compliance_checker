from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from gdpr_categories import GDPR_CATEGORIES
import os
from dotenv import load_dotenv

load_dotenv()

def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return splitter.split_text(text)


def match_categories(chunks: list[str]) -> dict:
    """Match policy chunks to GDPR categories using keyword matching (no embedding cost)."""
    found = {cat: [] for cat in GDPR_CATEGORIES}

    for chunk in chunks:
        chunk_lower = chunk.lower()
        for category, info in GDPR_CATEGORIES.items():
            for keyword in info["keywords"]:
                if keyword.lower() in chunk_lower:
                    found[category].append(chunk)
                    break

    return found


def analyze_with_llm(policy_text: str, matched: dict) -> dict:
    """Use Groq LLM to analyze compliance for each category."""
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

    results = {}

    for category, chunks in matched.items():
        gdpr_info = GDPR_CATEGORIES[category]

        if chunks:
            context = "\n".join(chunks[:3])  # top 3 relevant chunks
            prompt = f"""You are a GDPR compliance expert.

GDPR Category: {category}
GDPR Articles: {gdpr_info['gdpr_article']}
What it covers: {gdpr_info['description']}

Relevant policy text:
{context}

Based on the policy text above, assess:
1. Is this category COMPLIANT, PARTIAL, or NON-COMPLIANT?
2. In 1-2 sentences, explain why.
3. If gaps exist, what specifically is missing?

Respond in this exact format:
STATUS: [COMPLIANT/PARTIAL/NON-COMPLIANT]
EXPLANATION: [your explanation]
GAP: [what is missing, or 'None']"""

        else:
            prompt = f"""You are a GDPR compliance expert.

GDPR Category: {category}
GDPR Articles: {gdpr_info['gdpr_article']}
What it covers: {gdpr_info['description']}

The privacy policy provided does NOT appear to mention this category at all.

Respond in this exact format:
STATUS: NON-COMPLIANT
EXPLANATION: No mention of {category.lower()} found in the policy.
GAP: Policy must address {gdpr_info['description']} per {gdpr_info['gdpr_article']}."""

        messages = [
            SystemMessage(content="You are a GDPR compliance expert. Be concise and precise."),
            HumanMessage(content=prompt)
        ]

        response = llm.invoke(messages)
        results[category] = parse_response(response.content, category)

    return results


def parse_response(text: str, category: str) -> dict:
    """Parse LLM response into structured format."""
    lines = text.strip().split("\n")
    result = {"status": "UNKNOWN", "explanation": "", "gap": "None", "category": category}

    for line in lines:
        if line.startswith("STATUS:"):
            result["status"] = line.replace("STATUS:", "").strip()
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.replace("EXPLANATION:", "").strip()
        elif line.startswith("GAP:"):
            result["gap"] = line.replace("GAP:", "").strip()

    return result


def calculate_score(results: dict) -> int:
    """Calculate overall compliance score out of 100."""
    scores = {"COMPLIANT": 10, "PARTIAL": 5, "NON-COMPLIANT": 0, "UNKNOWN": 0}
    total = sum(scores.get(v["status"], 0) for v in results.values())
    max_score = len(results) * 10
    return int((total / max_score) * 100)


def run_compliance_check(policy_text: str) -> dict:
    """Main function to run the full pipeline."""
    chunks = chunk_text(policy_text)
    matched = match_categories(chunks)
    results = analyze_with_llm(policy_text, matched)
    score = calculate_score(results)

    return {
        "score": score,
        "results": results,
        "total_chunks": len(chunks)
    }