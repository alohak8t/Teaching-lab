import json
import os
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Teaching Lab v0",
    page_icon="🧪",
    layout="wide",
)

MODEL = "gpt-5.6-terra"

SYSTEM_PROMPT = """
You are the first, deliberately non-agentic version of a Public Speaking Teaching Lab.

Your job is to help an experienced public-speaking instructor THINK about a teaching topic.
You are NOT doing live research in this version. Do not claim that you searched the web,
read current papers, or verified recent evidence.

Separate established/common teaching practice from questions that require evidence.
Be intellectually serious, concise, skeptical of clichés, and useful for undergraduate
introductory public-speaking instruction.

Important teaching preference:
- Do not turn the response into a finished lecture or slide deck.
- Preserve room for the instructor to explain, question, and facilitate.
- Prefer provocative questions, distinctions, and teachable tensions over walls of content.
"""

TEACHING_BRIEF_SCHEMA = {
    "type": "json_schema",
    "name": "teaching_brief",
    "description": "A structured preliminary teaching brief that does not pretend to be live research.",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "framing": {"type": "string"},
            "conventional_wisdom": {
                "type": "array",
                "items": {"type": "string"}
            },
            "questions_for_evidence": {
                "type": "array",
                "items": {"type": "string"}
            },
            "potential_misconceptions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "teaching_possibilities": {
                "type": "array",
                "items": {"type": "string"}
            },
            "research_agenda": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": [
            "topic",
            "framing",
            "conventional_wisdom",
            "questions_for_evidence",
            "potential_misconceptions",
            "teaching_possibilities",
            "research_agenda"
        ],
        "additionalProperties": False
    }
}

def get_api_key():
    # Local environment variable first.
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key

    # Streamlit secrets second.
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None

def build_teaching_brief(topic: str, investigation: str, class_context: str):
    client = OpenAI(api_key=get_api_key())

    user_prompt = f"""
TOPIC:
{topic}

WHAT I WANT TO INVESTIGATE:
{investigation}

CLASS CONTEXT:
{class_context if class_context.strip() else "Introductory undergraduate public speaking."}

Create a preliminary teaching brief.

Remember: this version has no research tools. If a claim would need current or empirical
verification, turn it into a question for evidence rather than presenting it as verified fact.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        text={"format": TEACHING_BRIEF_SCHEMA},
    )

    return json.loads(response.output_text)

def render_list(items):
    for item in items:
        st.markdown(f"- {item}")

st.title("🧪 Teaching Lab v0")
st.caption("Build 1: model + prompt + structured output. No search. No memory. No agent loop.")

with st.sidebar:
    st.subheader("What exists in v0")
    st.markdown("""
**Yes**
- A web interface
- A model API call
- Application instructions
- Structured JSON output

**Not yet**
- Web search
- Source reading
- Memory
- Tools
- Agent loop
- Multiple agents
    """)
    st.divider()
    st.caption(f"Model: {MODEL}")

topic = st.text_input(
    "Teaching topic",
    value="Public speaking anxiety",
    placeholder="e.g. audience analysis, informative speaking, nonverbal communication",
)

investigation = st.text_area(
    "What do you want to investigate?",
    value="How should I teach this to introductory public-speaking students?",
    height=100,
)

class_context = st.text_area(
    "Optional class context",
    value="Students are preparing their first informative speech. I want activities that make them think rather than slides that give away every answer.",
    height=100,
)

run = st.button("Generate teaching brief", type="primary", use_container_width=True)

if run:
    if not get_api_key():
        st.error(
            "No OpenAI API key was found. Add OPENAI_API_KEY as an environment variable "
            "or in .streamlit/secrets.toml."
        )
        st.stop()

    if not topic.strip() or not investigation.strip():
        st.warning("Add a topic and a question to investigate.")
        st.stop()

    with st.spinner("Thinking..."):
        try:
            brief = build_teaching_brief(topic, investigation, class_context)
        except Exception as exc:
            st.exception(exc)
            st.stop()

    st.success("Teaching brief generated.")

    st.subheader(brief["topic"])
    st.write(brief["framing"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 1. Conventional teaching wisdom")
        render_list(brief["conventional_wisdom"])

        st.markdown("### 2. Questions for the evidence")
        render_list(brief["questions_for_evidence"])

        st.markdown("### 3. Potential misconceptions")
        render_list(brief["potential_misconceptions"])

    with col2:
        st.markdown("### 4. Teaching possibilities")
        render_list(brief["teaching_possibilities"])

        st.markdown("### 5. Research agenda")
        render_list(brief["research_agenda"])

    with st.expander("See the structured data the app received"):
        st.json(brief)

    st.info(
        "Engineering note: the model did not choose any action here. "
        "The application sent one request and displayed one structured response. "
        "That is why v0 is an AI app, not an agent."
    )
