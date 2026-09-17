import os
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Teaching Lab v1",
    page_icon="🔎",
    layout="wide",
)

MODEL = "gpt-5.6-terra"

SYSTEM_PROMPT = """
You are Teaching Lab v1, a research assistant for an experienced public-speaking instructor.

Your job is not to write a finished lecture or slide deck.
Your job is to investigate a teaching question and help the instructor decide what is worth teaching.

You have access to web search.

Use web search when the question depends on:
- empirical evidence
- recent research
- current guidance
- claims that should be verified

When you research:
- Prefer peer-reviewed research, universities, professional associations,
  government sources, and primary sources when available.
- Distinguish evidence from interpretation.
- Do not turn conventional textbook advice into "research findings"
  unless evidence supports it.
- Flag weak, mixed, old, indirect, or contested evidence.
- Preserve room for the instructor to explain, question, and facilitate.
- Cite factual claims that came from web research.

Return a concise research brief with these headings:

## Bottom line
## What the evidence suggests
## What is less certain
## Implications for teaching
## One classroom experiment
## Questions worth researching next
## Sources
"""

DEFAULT_QUESTION = """
What does current research say about how college students evaluate
the credibility of sources, and what should I change or emphasize
when teaching source evaluation in an introductory public-speaking course?
"""

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

    user_input = f"""
RESEARCH QUESTION:

{question}

CLASS CONTEXT:

{context}

Investigate this question.

Search the web when appropriate.

Synthesize rather than merely listing sources.

Make clear what is well supported versus what remains uncertain.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_input,
        tools=[
            {
                "type": "web_search"
            }
        ],
        tool_choice="auto",
    )

    return response


def inspect_tool_use(response):

    events = []

    for item in response.output:

        if getattr(item, "type", None) == "web_search_call":

            events.append(
                {
                    "type": "web_search_call",
                    "status": getattr(item, "status", "unknown"),
                }
            )

    return events


st.title("🔎 Teaching Lab v1")

st.caption(
    "Build 2: the model now has one tool — web search."
)

with st.sidebar:

    st.subheader("Architecture")

    st.code(
        """
question
   ↓
model
   ↓ decides
web search
   ↓
evidence
   ↓
model
   ↓
research brief
"""
    )

    st.markdown(
        """
### New in v1

- Web search tool
- Model decides whether to use it
- Evidence can affect the answer
- Visible tool-event inspection

### Still missing

- Persistent memory
- Saved research database
- File tools
- Agent loop
- Multiple agents
"""
    )

    st.divider()

    st.caption(f"Model: {MODEL}")


question = st.text_area(
    "Research question",
    value=DEFAULT_QUESTION,
    height=150,
)

context = st.text_area(
    "Class context",
    value="""
Introductory undergraduate public speaking.

Students have already covered:
audience analysis, topic, general purpose,
specific purpose, and central idea.

Next they will work on gathering and evaluating
sources and developing main points.
""",
    height=150,
)


if st.button(
    "Research this",
    type="primary",
    use_container_width=True
):

    if not get_api_key():

        st.error(
            """
No OpenAI API key was found.

We will add this securely when we deploy the app.
"""
        )

        st.stop()

    if not question.strip():

        st.warning(
            "Enter a research question."
        )

        st.stop()

    with st.spinner(
        "The model may decide to search the web..."
    ):

        try:

            response = run_research(
                question,
                context
            )

        except Exception as exc:

            st.exception(exc)

            st.stop()

    st.success(
        "Research complete."
    )

    st.markdown(
        response.output_text
    )

    events = inspect_tool_use(
        response
    )

    st.divider()

    st.subheader(
        "🔬 Engineering view"
    )

    if events:

        st.success(
            f"The model used web search {len(events)} time(s)."
        )

        for i, event in enumerate(
            events,
            start=1
        ):

            with st.expander(
                f"Tool event {i}: web search"
            ):

                st.json(event)

    else:

        st.info(
            """
No web-search event appeared in this run.

Because tool_choice="auto",
the model is allowed to decide
that search is unnecessary.
"""
        )

    with st.expander(
        "What changed from v0?"
    ):

        st.markdown(
            """
In **v0**:

`question → model → answer`

In **v1**:

`question → model → search → evidence → model → answer`

The important new code is:

```python
tools=[{"type": "web_search"}]
