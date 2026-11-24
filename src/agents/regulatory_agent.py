from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.config import settings
from src.state import ComplianceState
from src.rag_engine import HybridComplianceRetriever

# Initialize RAG retriever
retriever = HybridComplianceRetriever()

llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name=settings.GROQ_MODEL,
    temperature=0.0
)

REGULATORY_PROMPT = ChatPromptTemplate.from_template("""
You are a Senior Regulatory Compliance Officer specializing in UAE Central Bank (CBUAE), DIFC, and ADGM statutory frameworks.

TRANSACTION DETAILS:
- Entity Name: {entity_name}
- Origin Country: {country}
- Transaction Amount (USD): ${amount}
- Dossier Notes: {dossier}

RELEVANT UAE REGULATORY CLAUSES RETRIEVED:
{regulatory_context}

YOUR TASK:
Examine if this transaction violates any UAE AML laws, thresholds, shell company prohibitions, or beneficial ownership mandates.
Cite the exact regulatory section when pointing out infractions.

Output your detailed findings as concise, bulleted factual statements.
""")

def regulatory_auditor_node(state: ComplianceState) -> dict:
    """Evaluates transaction dossier against UAE regulatory rules via Hybrid RAG."""
    query = f"AML thresholds, shell companies, and jurisdiction rules for {state['entity_name']} from {state['country_of_origin']}"
    
    # Query hybrid retrieval engine
    rag_matches = retriever.hybrid_search(query, top_k=2)
    context_str = "\n\n".join([m["content"] for m in rag_matches])
    
    chain = REGULATORY_PROMPT | llm
    response = chain.invoke({
        "entity_name": state["entity_name"],
        "country": state["country_of_origin"],
        "amount": state["transaction_amount_usd"],
        "dossier": state["raw_dossier_text"],
        "regulatory_context": context_str
    })
    
    finding = f"[REGULATORY AUDIT]: {response.content.strip()}"
    return {
        "regulatory_findings": [finding],
        "audit_trail": ["Regulatory RAG Auditor completed verification against CBUAE/DIFC rules."]
    }
