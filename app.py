
import streamlit as st
from datetime import date
import uuid

from backend.agents import run_krishimitra
from backend.intake import assess_question
from backend.voice import transcribe_farmer_audio
from backend.chat_store import (
    create_chat,
    add_message,
    list_chats,
    get_messages,
    clear_messages
)
from backend.image_diagnosis import analyze_crop_image


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="KrishiMitra AI",
    page_icon="🌱",
    layout="wide"
)


# ==================================================
# COMPLETE LIGHT THEME
# ==================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    background-color: #f8faf8 !important;
    color: #26352c !important;
}

header[data-testid="stHeader"] {
    background-color: #f8faf8 !important;
}

.block-container {
    max-width: 1150px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}

/* Header */
.km-title {
    color: #166534 !important;
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 0;
}

.km-subtitle {
    color: #64748b !important;
    font-size: 1rem;
    margin-top: 5px;
}

/* Main text */
.main .stMarkdown,
.main .stMarkdown p,
.main .stMarkdown li,
.main label {
    color: #26352c !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #edf7ef !important;
    border-right: 1px solid #d9e9dc !important;
}

section[data-testid="stSidebar"] * {
    color: #26352c !important;
}

/* Sidebar inputs */
section[data-testid="stSidebar"] input {
    background-color: #ffffff !important;
    color: #26352c !important;
    -webkit-text-fill-color: #26352c !important;
    border: 1px solid #cbdccc !important;
}

section[data-testid="stSidebar"] input::placeholder {
    color: #84958a !important;
    -webkit-text-fill-color: #84958a !important;
}

/* Main input fields */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #26352c !important;
    -webkit-text-fill-color: #26352c !important;
    border: 1px solid #cbdccc !important;
    border-radius: 9px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #84958a !important;
    -webkit-text-fill-color: #84958a !important;
}

/* Input labels */
.stTextInput label,
.stNumberInput label,
.stTextArea label,
.stSelectbox label,
.stDateInput label,
.stFileUploader label {
    color: #26352c !important;
    font-weight: 600 !important;
}

/* Select boxes */
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #26352c !important;
    border-color: #cbdccc !important;
}

.stSelectbox div[data-baseweb="select"] span {
    color: #26352c !important;
}

/* Radio buttons */
.stRadio label,
.stCheckbox label {
    color: #26352c !important;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    padding: 14px 18px !important;
}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] li,
div[data-testid="stAlert"] strong {
    color: #26352c !important;
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
}

div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] strong,
div[data-testid="stChatMessage"] h1,
div[data-testid="stChatMessage"] h2,
div[data-testid="stChatMessage"] h3 {
    color: #26352c !important;
}

/* Chat composer */
div[data-testid="stChatInput"] {
    background-color: #ffffff !important;
    border: 1px solid #cbdccc !important;
    border-radius: 16px !important;
}

div[data-testid="stChatInput"] textarea {
    background-color: #ffffff !important;
    color: #26352c !important;
    -webkit-text-fill-color: #26352c !important;
    caret-color: #166534 !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #84958a !important;
    -webkit-text-fill-color: #84958a !important;
    opacity: 1 !important;
}

div[data-testid="stChatInput"] button {
    color: #166534 !important;
}

/* Buttons */
.stButton button,
.stFormSubmitButton button {
    background-color: #15803d !important;
    color: #ffffff !important;
    border: 1px solid #15803d !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: 0.2s ease;
}

.stButton button:hover,
.stFormSubmitButton button:hover {
    background-color: #166534 !important;
    border-color: #166534 !important;
    color: #ffffff !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #dce9de !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"] {
    color: #26352c !important;
}

/* Expanders */
div[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid #dce9de !important;
    border-radius: 12px !important;
}

div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary span {
    color: #26352c !important;
}

/* Forms */
div[data-testid="stForm"] {
    background-color: #ffffff !important;
    border: 1px solid #dce9de !important;
    border-radius: 14px !important;
    padding: 20px !important;
}

/* Dividers */
hr {
    border-color: #dce9de !important;
}

/* Captions */
[data-testid="stCaptionContainer"] {
    color: #64748b !important;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# HEADER
# ==================================================

st.markdown(
    '<p class="km-title">🌱 KrishiMitra AI</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="km-subtitle">Your farming companion · '
    'Explain your problem, share details, get practical guidance.</p>',
    unsafe_allow_html=True
)


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "messages": [],
    "pending_problem": "",
    "pending_details": [],
    "chat_id": str(uuid.uuid4()),
    "loaded_chat_id": None,
    "soil_ph": "",
    "soil_n": "",
    "soil_p": "",
    "soil_k": "",
    "soil_oc": "",
    "soil_moisture": "",
    "soil_ec": ""
}

for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


crop_options = [
    "Rice",
    "Wheat",
    "Maize",
    "Potato",
    "Tomato",
    "Onion",
    "Mustard",
    "Gram",
    "Sugarcane",
    "Banana",
    "Mango",
    "Other"
]

if st.session_state.loaded_chat_id is None:
    create_chat(st.session_state.chat_id)
    st.session_state.loaded_chat_id = st.session_state.chat_id


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def clean_soil(values):
    return {
        key: value
        for key, value in values.items()
        if value is not None and str(value).strip()
    }


def get_soil_metrics():
    return clean_soil({
        "pH": st.session_state.get("soil_ph", ""),
        "Nitrogen (N)": st.session_state.get("soil_n", ""),
        "Phosphorus (P)": st.session_state.get("soil_p", ""),
        "Potassium (K)": st.session_state.get("soil_k", ""),
        "Organic carbon (%)": st.session_state.get("soil_oc", ""),
        "Soil moisture (%)": st.session_state.get("soil_moisture", ""),
        "EC": st.session_state.get("soil_ec", "")
    })


def show_weather(result):
    weather = result.get("weather", {})
    current = weather.get("current", {})

    if current:
        with st.expander("🌦️ Current weather", expanded=False):

            st.caption(
                f"{weather.get('location', city)}, "
                f"{weather.get('state', '')}"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Temperature",
                f"{current.get('temperature_2m', '—')} °C"
            )

            c2.metric(
                "Humidity",
                f"{current.get('relative_humidity_2m', '—')}%"
            )

            c3.metric(
                "Rainfall",
                f"{current.get('precipitation', '—')} mm"
            )

            c4.metric(
                "Wind",
                f"{current.get('wind_speed_10m', '—')} km/h"
            )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.header("👨‍🌾 Farm Profile")

    city = st.text_input(
        "📍 Location",
        value="Katihar, Bihar",
        key="profile_city"
    )

    crop = st.selectbox(
        "🌾 Main crop",
        crop_options,
        key="profile_crop"
    )

    language = st.selectbox(
        "🌐 Response language",
        ["Hindi", "English"],
        key="profile_language"
    )

    st.divider()

    page = st.radio(
        "Choose feature",
        [
            "💬 Ask KrishiMitra",
            "📅 Crop Schedule",
            "🧪 Soil Health Dashboard",
            "📷 Disease Detection"
        ],
        key="active_page"
    )

    st.divider()

    st.subheader("🗂️ Chat history")

    if st.button("＋ New chat", use_container_width=True):

        st.session_state.chat_id = str(uuid.uuid4())

        create_chat(st.session_state.chat_id)

        st.session_state.messages = []
        st.session_state.pending_problem = ""
        st.session_state.pending_details = []

        st.session_state.loaded_chat_id = st.session_state.chat_id

        st.rerun()

    saved_chats = list_chats()

    if saved_chats:

        chat_map = {
            f"{item['title']} · {item['updated_at'][5:16]} · {item['id'][:6]}":
            item["id"]
            for item in saved_chats
        }

        labels = list(chat_map.keys())

        current_label = next(
            (
                label for label, cid in chat_map.items()
                if cid == st.session_state.chat_id
            ),
            labels[0]
        )

        chosen_label = st.selectbox(
            "Previous conversations",
            labels,
            index=labels.index(current_label)
        )

        chosen_id = chat_map[chosen_label]

        if chosen_id != st.session_state.chat_id:

            st.session_state.chat_id = chosen_id
            st.session_state.messages = get_messages(chosen_id)

            st.session_state.pending_problem = ""
            st.session_state.pending_details = []

            st.session_state.loaded_chat_id = chosen_id

            st.rerun()

    st.divider()

    st.caption(
        "🌱 Soil values enter karne ke liye "
        "Soil Health Dashboard open karein."
    )

    if st.button("🗑️ Clear chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.pending_problem = ""
        st.session_state.pending_details = []

        clear_messages(st.session_state.chat_id)

        st.rerun()

    st.caption("Weather · RAG knowledge · Soil guidance · Crop calendar")


# Current soil values
soil_metrics = get_soil_metrics()


# ==================================================
# ASK KRISHIMITRA
# ==================================================

if page == "💬 Ask KrishiMitra":

    st.info(
        "Pehle apni problem batayein. KrishiMitra zaroori details "
        "poochega; details milne ke baad hi final advice dega."
    )

    if not st.session_state.messages:

        with st.chat_message("assistant", avatar="🌱"):
            st.write(
                "Namaste! Aapki fasal mein kya problem hai? "
                "Jaise: 'Mere dhaan ke patte peele ho rahe hain.' "
                "Main pehle kuch zaroori details poochunga, phir salah dunga."
            )

    # Display conversation
    for msg in st.session_state.messages:

        with st.chat_message(
            msg["role"],
            avatar="🌱" if msg["role"] == "assistant" else None
        ):
            st.markdown(msg["content"])

    # Integrated text and audio input
    prompt = st.chat_input(
        "Apni farming problem type karein...",
        accept_audio=True,
        audio_sample_rate=16000,
        key="farmer_chat_input"
    )

    new_message = None

    if prompt is not None:

        if prompt.text and prompt.text.strip():
            new_message = prompt.text.strip()

        elif prompt.audio is not None:

            try:
                audio_bytes = prompt.audio.getvalue()

                with st.spinner("🎙️ Voice ko text mein convert kar raha hoon..."):

                    new_message = transcribe_farmer_audio(
                        audio_bytes,
                        prompt.audio.type or "audio/wav",
                        language
                    )

                if new_message:
                    new_message = new_message.strip()
                else:
                    st.warning("Voice se text nahi mil paya. Dobara try karein.")

            except Exception as exc:
                st.error(f"Voice process nahi ho payi: {exc}")

    # Process user input
    if new_message:

        if not city.strip():
            st.error("Sidebar mein location enter karein.")

        else:

            st.session_state.messages.append({
                "role": "user",
                "content": new_message
            })

            add_message(
                st.session_state.chat_id,
                "user",
                new_message
            )

            with st.chat_message("user"):
                st.markdown(new_message)

            if st.session_state.pending_problem:

                st.session_state.pending_details.append(new_message)

                problem = st.session_state.pending_problem

                details = "\n".join(
                    st.session_state.pending_details
                )

            else:

                problem = new_message
                details = ""

                st.session_state.pending_problem = problem
                st.session_state.pending_details = []

            recent_history = "\n".join(
                f"{m['role']}: {m['content']}"
                for m in st.session_state.messages[-8:-1]
            )

            try:

                with st.chat_message("assistant", avatar="🌱"):

                    with st.spinner(
                        "Aapki problem samajh raha hoon..."
                    ):

                        intake = assess_question(
                            problem=problem,
                            details=details,
                            crop=crop,
                            location=city,
                            language=language,
                            history=recent_history
                        )

                    if intake["status"] == "ask":

                        clarification = intake["question"] or (
                            "कृपया फसल की अवस्था और समस्या कब से है, बताइए।"
                            if language == "Hindi"
                            else "Please share the crop stage and when the problem started."
                        )

                        st.markdown(clarification)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": clarification
                        })

                        add_message(
                            st.session_state.chat_id,
                            "assistant",
                            clarification
                        )

                    else:

                        combined_question = (
                            f"Farmer's original problem: {problem}\n\n"
                            f"Farmer's clarification/details: "
                            f"{details or 'No additional details'}\n\n"
                            f"Latest conversation context: {recent_history}"
                        )

                        with st.spinner(
                            "Weather aur agricultural knowledge check kar raha hoon..."
                        ):

                            result = run_krishimitra(
                                city=city.strip(),
                                crop=crop,
                                question=combined_question,
                                language=language,
                                soil_metrics=soil_metrics
                            )

                        show_weather(result)

                        answer = result.get(
                            "response",
                            "Sorry, abhi answer generate nahi ho paya."
                        )

                        st.markdown(answer)

                        st.caption(
                            "Fertilizer/pesticide ki exact dose local "
                            "KVK ya agriculture officer se verify karein."
                        )

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })

                        add_message(
                            st.session_state.chat_id,
                            "assistant",
                            answer
                        )

                        st.session_state.pending_problem = ""
                        st.session_state.pending_details = []

            except Exception as exc:

                error_message = f"Request process nahi ho payi: {exc}"

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

                add_message(
                    st.session_state.chat_id,
                    "assistant",
                    error_message
                )


# ==================================================
# CROP SCHEDULE
# ==================================================

elif page == "📅 Crop Schedule":

    st.subheader("📅 Personalized Crop Schedule")

    st.write(
        "Crop select karein aur sowing/transplanting date dein. "
        "KrishiMitra stage-wise calendar banayega."
    )

    with st.form("schedule_form"):

        schedule_crop = st.selectbox(
            "Crop",
            crop_options,
            index=crop_options.index(crop),
            key="schedule_crop"
        )

        variety = st.text_input(
            "Crop variety (if known)",
            placeholder="e.g. Swarna, MTU-1010"
        )

        season = st.selectbox(
            "Season",
            ["Kharif", "Rabi", "Zaid", "Not sure"]
        )

        sowing_date = st.date_input(
            "Sowing/transplanting date",
            value=date.today()
        )

        current_stage = st.text_input(
            "Current crop stage (optional)",
            placeholder="e.g. 20 days after transplanting"
        )

        schedule_submit = st.form_submit_button(
            "Generate crop schedule",
            use_container_width=True
        )

    if schedule_submit:

        if not city.strip():
            st.error("Please enter your location in the sidebar.")

        else:

            schedule_question = (
                "Create a personalized crop schedule for this farmer. "
                "Give a clear stage-wise calendar from the provided "
                "sowing/transplanting date through harvest. "
                "Use days after sowing/transplanting where exact dates "
                "are not locally reliable. Include irrigation, nutrient "
                "checks, weed/pest monitoring, critical growth stages "
                "and harvest readiness. Do not invent exact chemical doses.\n"
                f"Crop: {schedule_crop}\n"
                f"Variety: {variety or 'Not known'}\n"
                f"Season: {season}\n"
                f"Sowing/transplanting date: {sowing_date}\n"
                f"Current stage: {current_stage or 'Not provided'}."
            )

            try:

                with st.spinner("Crop calendar bana raha hoon..."):

                    result = run_krishimitra(
                        city=city.strip(),
                        crop=schedule_crop,
                        question=schedule_question,
                        language=language,
                        soil_metrics=soil_metrics,
                        sowing_date=str(sowing_date)
                    )

                show_weather(result)

                st.markdown(
                    result.get(
                        "response",
                        "Schedule generate nahi ho paya."
                    )
                )

            except Exception as exc:
                st.error(f"Schedule generate nahi ho paya: {exc}")


# ==================================================
# SOIL HEALTH DASHBOARD
# ==================================================

elif page == "🧪 Soil Health Dashboard":

    st.subheader("🧪 Soil Health Dashboard")

    st.write(
        "Apni Soil Health Card ya laboratory report ke values "
        "neeche enter karein. Unknown values blank chhod sakte hain."
    )

    st.divider()

    st.markdown("### 🌱 Basic soil properties")

    st.caption(
        "Report mein diye gaye values aur units hi enter karein. "
        "Andaza lagakar values mat bharein."
    )

    # Soil input form
    with st.form("soil_input_form"):

        col1, col2 = st.columns(2)

        with col1:

            st.text_input(
                "Soil pH",
                key="soil_ph",
                placeholder="Example: 6.8",
                help="Soil Health Card mein diya gaya pH value."
            )

            st.text_input(
                "Nitrogen (N)",
                key="soil_n",
                placeholder="Example: 280 kg/ha"
            )

            st.text_input(
                "Phosphorus (P)",
                key="soil_p",
                placeholder="Example: 22 kg/ha"
            )

            st.text_input(
                "Potassium (K)",
                key="soil_k",
                placeholder="Example: 180 kg/ha"
            )

        with col2:

            st.text_input(
                "Organic Carbon (%)",
                key="soil_oc",
                placeholder="Example: 0.65"
            )

            st.text_input(
                "Soil Moisture (%)",
                key="soil_moisture",
                placeholder="Example: 35"
            )

            st.text_input(
                "Electrical Conductivity (EC)",
                key="soil_ec",
                placeholder="Example: 0.4 dS/m"
            )

        submitted = st.form_submit_button(
            "💾 Save Soil Details",
            type="primary",
            use_container_width=True
        )

    if submitted:

        saved_values = get_soil_metrics()

        if saved_values:
            st.success("Soil details saved successfully!")
        else:
            st.warning("Abhi koi soil value enter nahi ki gayi hai.")

    st.divider()

    # Soil overview
    values = get_soil_metrics()

    st.markdown("### 📊 Your Soil Overview")

    if not values:

        st.info(
            "Abhi koi soil data available nahi hai. "
            "Upar form mein apne soil report ke values enter karein."
        )

    else:

        st.caption(
            "Saved farmer-provided values. "
            "Ye laboratory verification ka substitute nahi hain."
        )

        metric_columns = st.columns(3)

        for idx, (name, value) in enumerate(values.items()):

            with metric_columns[idx % 3]:
                st.metric(
                    label=name,
                    value=value
                )

        st.divider()

        st.markdown("### 🤖 AI Soil Report Analysis")

        st.write(
            "KrishiMitra tumhare soil parameters ko selected crop "
            "aur location ke context mein explain karega."
        )

        if st.button(
            "🔍 Analyze My Soil",
            type="primary",
            use_container_width=True
        ):

            soil_question = (
                "Explain these farmer-provided soil metrics in simple "
                "terms for the selected crop. Identify what each "
                "parameter generally indicates, what cannot be "
                "concluded without units/test method/crop stage, "
                "and what follow-up soil test or local expert advice "
                "is needed. Do not invent missing values or exact "
                "fertilizer doses.\n"
                f"Crop: {crop}\n"
                f"Location: {city}\n"
                f"Soil values: {values}"
            )

            try:

                with st.spinner(
                    "🌱 KrishiMitra tumhari soil report analyze kar raha hai..."
                ):

                    result = run_krishimitra(
                        city=city.strip(),
                        crop=crop,
                        question=soil_question,
                        language=language,
                        soil_metrics=values
                    )

                show_weather(result)

                st.markdown("### 📋 Soil Analysis Result")

                st.markdown(
                    result.get(
                        "response",
                        "Soil explanation generate nahi ho paya."
                    )
                )

            except Exception as exc:
                st.error(f"Soil analysis nahi ho paya: {exc}")

    st.divider()

    st.warning(
        "Important: Soil metrics akelay fertilizer recommendation "
        "ke liye kaafi nahi hote. Crop stage, units, sampling method "
        "aur local recommendations bhi zaroori hain."
    )


# ==================================================
# DISEASE DETECTION
# ==================================================

elif page == "📷 Disease Detection":

    st.subheader("📷 Crop Disease / Symptom Detection")

    st.write(
        "Fasal ya affected leaf ki clear photo upload karein. "
        "AI visible symptoms ke possible causes batayega; "
        "ye final diagnosis nahi hai."
    )

    uploaded_image = st.file_uploader(
        "Upload crop/leaf image",
        type=["jpg", "jpeg", "png", "webp"],
        key="crop_image"
    )

    farmer_note = st.text_area(
        "Additional details (optional)",
        placeholder="Problem kab se hai? Kitne plants affected hain? Recent rain/irrigation?"
    )

    if uploaded_image is not None:

        st.image(
            uploaded_image,
            caption="Uploaded crop image",
            use_container_width=True
        )

        if st.button(
            "🔍 Analyze crop image",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Image mein visible symptoms analyze kar raha hoon..."
                ):

                    diagnosis = analyze_crop_image(
                        image_bytes=uploaded_image.getvalue(),
                        mime_type=uploaded_image.type or "image/jpeg",
                        crop=crop,
                        location=city,
                        language=language,
                        question=farmer_note
                    )

                st.markdown(diagnosis)

                st.caption(
                    "AI image triage is not a confirmed diagnosis. "
                    "Chemical treatment se pehle local KVK/agriculture officer se verify karein."
                )

            except Exception as exc:
                st.error(f"Image analyze nahi ho payi: {exc}")
