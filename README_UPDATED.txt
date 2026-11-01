KRISHIMITRA AI - ENHANCED FARMER ASSISTANT

FEATURES
- Chatbot asks targeted clarification questions before giving a final advisory.
- Maintains recent conversation context during the active conversation.
- Saves chat sessions and messages in a local SQLite database (created automatically as
  krishimitra_chat.db in the project root). Chat history can be reopened from the sidebar.
- Farmer can ask by typing or recording voice; voice is transcribed to text.
- Optional soil metrics: pH, N, P, K, organic carbon, moisture and EC.
- Soil Health Dashboard displays supplied values and can ask Gemini to explain them.
- Separate Crop Schedule page creates a stage-wise calendar using crop, location,
  season, variety and sowing/transplanting date.
- Disease Detection page accepts a crop/leaf photo and returns possible visible symptoms
  and causes. This is image triage, not a confirmed diagnosis.
- Existing Gemini, Weather, LangGraph and RAG workflow retained.
- Existing regional safeguards retained: Assam PoP documents are not treated as Bihar advice.

SETUP (Windows PowerShell)
1. Extract the ZIP and open the krishi_1 folder in VS Code.
2. Create and activate a virtual environment:
   python -m venv .venv
   .venv\Scripts\Activate.ps1
3. Install dependencies:
   pip install -r requirements.txt
4. Create/copy .env in the project root with:
   GEMINI_API_KEY=your_actual_api_key
5. Start:
   streamlit run app.py

NOTES
- Never share your .env file or API key.
- Chat history is stored locally in krishimitra_chat.db. Back up this file if you want
  to preserve chats when moving the project. Do not commit it if it contains private data.
- Chat history persistence does not currently restore an in-progress clarification state
  after a browser/server restart; completed messages remain available.
- Unknown soil metrics should be left blank. Values are farmer-provided, not verified.
- Crop calendar dates are estimates and depend on variety, local season, weather and
  official agricultural recommendations.
- Image analysis suggests possible causes only. Confirm with local KVK/agriculture officer
  before applying pesticides or other chemical treatments.
- Voice transcription uses the configured Gemini model. If the API rejects audio, text chat
  remains available and a compatible speech-to-text model may be required.
