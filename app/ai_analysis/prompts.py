"""Prompt templates for LLM-based land dispute analysis."""

SYSTEM_PROMPT = """You are a legal analyst specializing in Indian land and property disputes. 
You analyze legal notices, newspaper articles, and court orders related to land disputes 
and extract structured information from them.

Always respond in valid JSON format."""

EXTRACTION_PROMPT = """Analyze the following land dispute notice/article and extract structured information.

Source: {source_name}
Publish Date: {publish_date}

--- NOTICE TEXT ---
{notice_text}
--- END ---

Extract the following fields as JSON:
{{
    "dispute_type": "<type: boundary_dispute|title_dispute|encroachment|partition|sale_objection|mortgage_dispute|court_order|public_notice|other>",
    "location": "<full location including village, taluk, district, state if available>",
    "parties_involved": ["<party1 name>", "<party2 name>", ...],
    "property_identifiers": {{
        "survey_number": "<survey/khasra number if mentioned>",
        "property_number": "<property/khata number if mentioned>",
        "plot_details": "<any plot/site details>"
    }},
    "urgency_score": <1-10, where 10 is most urgent>,
    "status": "<active|resolved|monitoring>",
    "summary": "<2-3 sentence summary of the dispute>",
    "key_dates": ["<any important dates mentioned>"],
    "legal_references": ["<any case numbers, act references, section numbers>"]
}}

Scoring guidelines for urgency:
- 9-10: Active litigation, court hearing imminent, possession threat
- 7-8: Legal notice served, dispute escalating, multiple parties
- 5-6: Public notice for objections, ongoing investigation
- 3-4: Informational notice, resolved but recent
- 1-2: Historical/resolved, low relevance to current stakeholders
"""

CLASSIFICATION_PROMPT = """Analyze the following structured dispute information and classify its severity.

--- DISPUTE DATA ---
{dispute_data}
--- END ---

Determine if this dispute is highly critical. Reply in JSON:
{{
    "severity_category": "<critical|high|medium|low|informational>",
    "justification": "<brief reasoning>"
}}
"""

CLUSTERING_PROMPT = """Analyze the following two dispute descriptions and entities. 
Determine if they refer to the exact same underlying real estate dispute.

--- DISPUTE 1 ---
{dispute_1}

--- DISPUTE 2 ---
{dispute_2}
--- END ---

Reply in JSON:
{{
    "is_related": <true|false>,
    "confidence_score": <0-100>,
    "reasoning": "<brief reasoning>"
}}
"""
