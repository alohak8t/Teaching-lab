import os
import json
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Teaching Lab v2",
    page_icon="🧪",
    layout="wide",
)

MODEL = "gpt-5.6-terra"

DEFAULT_QUESTION = (
    "What does current research say about how college students evaluate "
    "the credibility of sources, and what should I change or emphasize "
    "when teaching source evaluation in an introductory public-speaking course?"
)

DEFAULT_CONTEXT = (
    "Introductory undergraduate public speaking. Students have already covered "
    "audience analysis, topic, general purpose, specific purpose, and central idea. "
    "Next they will work on gathering and evaluating sources and developing main points."
)


def get_api_key():
    key = os.getenv("OPENAI_API_KEY")

    if key:
        return key

    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


def get_client():
    return OpenAI(api_key=get_api_key())


def parse_json(text):
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]

    if cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return json.loads(cleaned.strip())


def count_searches(response):
    count = 0

    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) == "web_search_call":
            count += 1

    return count


def run_researcher(question, context):
    client = get_client()

    instructions = (
        "You are the Researcher in a public-speaking Teaching Lab. "
        "Investigate the user's pedagogical question using web search. "
        "Prefer peer-reviewed studies, systematic reviews, academic journals, "
        "universities, professional associations, government sources, and "
        "primary sources. Distinguish empirical findings from interpretation. "
        "Do not write the final teaching brief. Your job is to gather a small "
        "set of important claims that another model can verify. "
        "For every claim, give the strongest direct source you found. "
        "Return ONLY valid JSON, with no markdown fences."
    )

    prompt = (
        "QUESTION:\n"
        + question
        + "\n\nCLASS CONTEXT:\n"
        + context
        + "\n\nReturn this exact JSON structure:\n"
        + '{"research_summary":"short overview",'
        + '"claims":['
        + '{"claim":"specific factual claim",'
        + '"source_title":"title of source",'
        + '"source_url":"direct URL",'
        + '"why_it_matters":"why this matters for the teaching question"}'
        + "]}\n\n"
        + "Find approximately 5 to 8 consequential claims. "
        + "Use specific claims that could actually be checked against the source."
    )

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
        tools=[{"type": "web_search"}],
        tool_choice="auto",
    )

    return parse_json(response.output_text), response


def run_verifier(research):
    client = get_client()

    instructions = (
        "You are the Verifier in a research pipeline. "
        "You receive claims and citations from another AI. "
        "Independently check whether each cited source actually supports each claim. "
        "Use web search. Inspect the cited source when possible and search for "
        "corroborating or conflicting evidence when necessary. "
        "Do not reward a claim merely because the citation looks scholarly. "
        "Label every claim as SUPPORTED, PARTIAL, UNCERTAIN, or UNSUPPORTED. "
        "SUPPORTED means the cited evidence directly supports the substantive claim. "
        "PARTIAL means part of the claim is supported but wording, scope, population, "
        "causality, or strength is overstated. "
        "UNCERTAIN means you cannot verify it adequately. "
        "UNSUPPORTED means the available source does not support it or contradicts it. "
        "Return ONLY valid JSON, with no markdown fences."
    )

    prompt = (
        "VERIFY THESE RESEARCH CLAIMS:\n\n"
        + json.dumps(research["claims"], ensure_ascii=False)
        + "\n\nReturn this exact JSON structure:\n"
        + '{"verifications":['
        + '{"claim":"original claim",'
        + '"status":"SUPPORTED or PARTIAL or UNCERTAIN or UNSUPPORTED",'
        + '"explanation":"brief explanation of what the evidence really supports",'
        + '"source_title":"best verified source title",'
        + '"source_url":"best verified source URL"}'
        + "]}"
    )

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
        tools=[{"type": "web_search"}],
        tool_choice="auto",
    )

    return parse_json(response.output_text), response


def run_synthesizer(question, context, research, verification):
    client = get_client()

    instructions = (
        "You are the Synthesizer in a Public Speaking Teaching Lab. "
        "You receive research that has already gone through a verification stage. "
        "Write an intellectually serious but practical teaching brief. "
        "Base strong conclusions primarily on SUPPORTED claims. "
        "Use PARTIAL claims only with appropriate qualification. "
        "Clearly identify important uncertainty. "
        "Do not use UNSUPPORTED claims as evidence. "
        "Do not pretend that evidence from another educational domain directly proves "
        "an effect in public-speaking instruction. Distinguish evidence from pedagogical inference. "
        "The instructor prefers teaching that makes students think rather than slides "
        "that simply reveal every answer. "
        "Use clear markdown headings."
    )

    prompt = (
        "ORIGINAL QUESTION:\n"
        + question
        + "\n\nCLASS CONTEXT:\n"
        + context
        + "\n\nRESEARCHER SUMMARY:\n"
        + research["research_summary"]
        + "\n\nVERIFIED CLAIMS:\n"
        + json.dumps(verification["verifications"], ensure_ascii=False)
        + "\n\nWrite the final brief with these sections:\n"
        + "## Bottom line\n"
        + "## What the verified evidence suggests\n"
        + "## What remains uncertain\n"
        + "## Implications for teaching\n"
        + "## One classroom experiment\n"
        + "## Questions worth researching next\n"
        + "## Verified sources\n\n"
        + "For the source list, include the source title and URL."
    )

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
    )

    return response.output_text, response


st.title("🧪 Teaching Lab v2")

st.caption(
    "Researcher → Verifier → Synthesizer"
)

with st.sidebar:
    st.subheader("Architecture")

    st.code(
        "question\n"
        "   ↓\n"
        "RESEARCHER\n"
        "   ↓ claims + sources\n"
        "VERIFIER\n"
        "   ↓ checked claims\n"
        "SYNTHESIZER\n"
        "   ↓\n"
        "teaching brief"
    )

    st.markdown(
        "**New in v2**\n"
        "- Multi-step pipeline\n"
        "- Structured intermediate data\n"
        "- Independent verification pass\n"
        "- Evidence labels\n\n"
        "**Not yet**\n"
        "- Persistent memory\n"
        "- Database\n"
        "- Embeddings / RAG\n"
        "- Your course files\n"
        "- Autonomous agent loop"
    )

question = st.text_area(
    "Research question",
    value=DEFAULT_QUESTION,
    height=150,
)

context = st.text_area(
    "Class context",
    value=DEFAULT_CONTEXT,
    height=130,
)

if st.button(
    "Run research pipeline",
    type="primary",
    use_container_width=True,
):

    if not get_api_key():
        st.error("No OpenAI API key found in Streamlit Secrets.")
        st.stop()

    try:
        with st.spinner("1/3 Researcher is gathering evidence..."):
            research, researcher_response = run_researcher(
                question,
                context,
            )

        st.success(
            "Researcher finished: "
            + str(len(research["claims"]))
            + " claims collected."
        )

        with st.spinner("2/3 Verifier is checking the claims..."):
            verification, verifier_response = run_verifier(
                research
            )

        st.success("Verification complete.")

        with st.spinner("3/3 Synthesizer is building the teaching brief..."):
            final_brief, synthesizer_response = run_synthesizer(
                question,
                context,
                research,
                verification,
            )

    except Exception as exc:
        st.exception(exc)
        st.stop()

    st.divider()

    st.markdown(final_brief)

    st.divider()

    st.header("🔬 Verification layer")

    status_icons = {
        "SUPPORTED": "✅",
        "PARTIAL": "🟡",
        "UNCERTAIN": "❓",
        "UNSUPPORTED": "❌",
    }

    for item in verification["verifications"]:

        status = item.get(
            "status",
            "UNCERTAIN",
        ).upper()

        icon = status_icons.get(
            status,
            "❓",
        )

        with st.expander(
            icon + " " + status + " — " + item["claim"]
        ):

            st.write(item["explanation"])

            st.markdown(
                "**Verified source:** "
                + item["source_title"]
            )

            st.markdown(
                item["source_url"]
            )

    st.divider()

    st.header("⚙️ Engineering view")

    researcher_searches = count_searches(
        researcher_response
    )

    verifier_searches = count_searches(
        verifier_response
    )

    total_searches = (
        researcher_searches
        + verifier_searches
    )

    st.markdown(
        "**Researcher web searches:** "
        + str(researcher_searches)
    )

    st.markdown(
        "**Verifier web searches:** "
        + str(verifier_searches)
    )

    st.markdown(
        "**Total web searches:** "
        + str(total_searches)
    )

    st.code(
        "question\n"
        "   ↓\n"
        "researcher + web search\n"
        "   ↓ structured claims\n"
        "verifier + independent web search\n"
        "   ↓ verified claims\n"
        "synthesizer\n"
        "   ↓\n"
        "final teaching brief"
    )

    with st.expander(
        "See the Researcher's structured data"
    ):
        st.json(research)

    with st.expander(
        "See the Verifier's structured data"
    ):
        st.json(verification)
