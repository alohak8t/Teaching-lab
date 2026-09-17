import os
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Teaching Lab v1",
    page_icon="🔎",
    layout="wide",
)

MODEL = "gpt-5.6-terra"

SYSTEM_PROMPT = (
    "You are Teaching Lab v1, a research assistant for an experienced "
    "public-speaking instructor. Your job is to investigate teaching questions, "
    "not write a finished lecture or slide deck. Use web search when the question "
    "depends on empirical evidence, recent research, current guidance, or claims "
    "that should be verified. Prefer peer-reviewed research, universities, "
    "professional associations, government sources, and primary sources. "
    "Distinguish evidence from interpretation. Flag weak, mixed, old, indirect, "
    "or contested evidence. Cite factual claims from web research. "
    "Return a concise brief with these sections: Bottom line; What the evidence "
    "suggests; What is less certain; Implications for teaching; One classroom "
    "experiment; Questions worth researching next; Sources."
)

DEFAULT_QUESTION = (
    "What does current research say about how college students evaluate the "
    "credibility of sources, and what should I change or emphasize when teaching "
    "source evaluation in an introductory public-speaking course?"
)

def get_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None

def run_research(question, context):
    client = OpenAI(api_key=get_api_key())

    user_input = (
        "RESEARCH QUESTION:\n"
        + question
        + "\n\nCLASS CONTEXT:\n"
        + context
        + "\n\nInvestigate this question. Search the web when appropriate. "
        + "Synthesize the evidence and distinguish strong findings from uncertainty."
    )

    return client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_input,
        tools=[{"type": "web_search"}],
        tool_choice="auto",
    )

def count_searches(response):
    count = 0
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) == "web_search_call":
            count += 1
    return count

st.title("🔎 Teaching Lab v1")
st.caption("Build 2: the model now has one external tool — web search.")

with st.sidebar:
    st.subheader("Architecture")
    st.code(
        "question\n"
        "  ↓\n"
        "model\n"
        "  ↓ decides\n"
        "web search\n"
        "  ↓\n"
        "evidence\n"
        "  ↓\n"
        "model\n"
        "  ↓\n"
        "research brief"
    )

    st.markdown(
        "**New in v1**\n"
        "- Web search\n"
        "- Model chooses whether to search\n"
        "- Evidence feeds back into the answer\n\n"
        "**Not yet**\n"
        "- Persistent memory\n"
        "- Saved research database\n"
        "- File tools\n"
        "- Agent loop\n"
        "- Multiple agents"
    )

question = st.text_area(
    "Research question",
    value=DEFAULT_QUESTION,
    height=150,
)

context = st.text_area(
    "Class context",
    value=(
        "Introductory undergraduate public speaking. Students have covered "
        "audience analysis, topic, general purpose, specific purpose, and central idea. "
        "Next they will work on gathering and evaluating sources and developing main points."
    ),
    height=140,
)

if st.button("Research this", type="primary", use_container_width=True):

    if not get_api_key():
        st.error("No OpenAI API key found in Streamlit Secrets.")
        st.stop()

    with st.spinner("Researching..."):
        try:
            response = run_research(question, context)
        except Exception as exc:
            st.exception(exc)
            st.stop()

    st.markdown(response.output_text)

    st.divider()
    st.subheader("🔬 Engineering view")

    searches = count_searches(response)

    if searches:
        st.success(f"The model used web search {searches} time(s).")
    else:
        st.info("No web search was used for this run.")

    st.markdown(
        "**What changed from v0?**\n\n"
        "v0: `question → model → answer`\n\n"
        "v1: `question → model → search → evidence → model → answer`\n\n"
        "The key addition is:\n\n"
        '`tools=[{"type": "web_search"}]`'
    )
