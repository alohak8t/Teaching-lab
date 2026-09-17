# Teaching Lab v0

This is the first deliberately simple version of the Public Speaking Teaching Lab.

## What it teaches

The full flow is:

`browser form → Python function → OpenAI Responses API → structured JSON → Streamlit display`

This version has **no web search, no memory, no tools, and no agent loop**.

That is intentional: Build 2 will add a search tool so the architectural change is visible.

## Run locally

1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Install dependencies:

   `pip install -r requirements.txt`

4. Set your API key.

   macOS/Linux:
   `export OPENAI_API_KEY="your_key_here"`

   Or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   and put the key there.

5. Run:

   `streamlit run app.py`

Streamlit will open the app in your browser.

## The five pieces to notice

1. **UI** — Streamlit collects the topic, investigation question, and class context.
2. **System instructions** — application-level behavior, not a casual user prompt.
3. **API call** — `client.responses.create(...)` sends the request to the model.
4. **JSON schema** — constrains the response into predictable fields.
5. **Rendering** — the app takes those fields and decides how to display them.

## Build 2

Next, add web search. The model will be able to decide when current evidence is needed,
use a search tool, inspect the results, and then produce the teaching brief.
