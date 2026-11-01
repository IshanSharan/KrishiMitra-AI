import streamlit as st
from datetime import date
import uuid
from backend.agents import run_krishimitra
from backend.intake import assess_question
from backend.voice import transcribe_farmer_audio
from backend.chat_store import create_chat, add_message, list_chats, get_messages, clear_messages
from backend.image_diagnosis import analyze_crop_image

st.set_page_config(page_title="KrishiMitra AI", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.stApp {background:#f7faf7;color:#1f2937}
header[data-testid="stHeader"] {background:rgba(0,0,0,0)}
.block-container {max-width:1050px;padding-top:1.7rem;padding-bottom:3rem}
.km-title {color:#166534;font-size:2.25rem;font-weight:800;margin:0}
.km-subtitle {color:#64748b;margin-top:.2rem}
.stChatMessage {border-radius:14px}
/* Make text typed into the chat composer clearly visible */
div[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #ffffff !important;
    background-color: #24252e !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #d1d5db !important;
    -webkit-text-fill-color: #d1d5db !important;
    opacity: 1 !important;
}
div[data-testid="stChatInput"] {
    background-color: #24252e !important;
    border: 1px solid #64748b !important;
    border-radius: 12px !important;
}
section[data-testid="stSidebar"] {background:#24252e}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label {color:white!important}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="km-title">🌱 KrishiMitra AI</p>', unsafe_allow_html=True)
st.markdown('<p class="km-subtitle">Your farming companion · Explain your problem, share details, get practical guidance.</p>', unsafe_allow_html=True)

# Persistent session state
for key, default in {
    "messages": [], "pending_problem": "", "pending_details": [],
    "processed_audio": None, "chat_id": str(uuid.uuid4()), "loaded_chat_id": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

crop_options = ["Rice", "Wheat", "Maize", "Potato", "Tomato", "Onion", "Mustard", "Gram", "Sugarcane", "Banana", "Mango", "Other"]
if st.session_state.loaded_chat_id is None:
    create_chat(st.session_state.chat_id)
    st.session_state.loaded_chat_id = st.session_state.chat_id

with st.sidebar:
    st.header("👨‍🌾 Farm Profile")
    city = st.text_input("📍 Location", value="Katihar, Bihar", key="profile_city")
    crop = st.selectbox("🌾 Main crop", crop_options, key="profile_crop")
    language = st.selectbox("🌐 Response language", ["Hindi", "English"], key="profile_language")
    st.divider()
    page = st.radio("Choose feature", ["💬 Ask KrishiMitra", "📅 Crop Schedule", "🧪 Soil Health Dashboard", "📷 Disease Detection"], key="active_page")
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
        chat_map = {f"{item['title']} · {item['updated_at'][5:16]} · {item['id'][:6]}": item['id'] for item in saved_chats}
        labels = list(chat_map.keys())
        current_label = next((label for label, cid in chat_map.items() if cid == st.session_state.chat_id), labels[0])
        chosen_label = st.selectbox("Previous conversations", labels, index=labels.index(current_label))
        chosen_id = chat_map[chosen_label]
        if chosen_id != st.session_state.chat_id:
            st.session_state.chat_id = chosen_id
            st.session_state.messages = get_messages(chosen_id)
            st.session_state.pending_problem = ""
            st.session_state.pending_details = []
            st.session_state.loaded_chat_id = chosen_id
            st.rerun()
    st.divider()
    st.subheader("🧪 Soil metrics (optional)")
    st.caption("Soil Health Card/lab report values enter karein. Unknown values blank chhodein.")
    soil_metrics = {
        "pH": st.text_input("pH", key="soil_ph", placeholder="e.g. 6.8"),
        "Nitrogen (N)": st.text_input("Nitrogen (N)", key="soil_n", placeholder="Report value + unit"),
        "Phosphorus (P)": st.text_input("Phosphorus (P)", key="soil_p", placeholder="Report value + unit"),
        "Potassium (K)": st.text_input("Potassium (K)", key="soil_k", placeholder="Report value + unit"),
        "Organic carbon (%)": st.text_input("Organic carbon (%)", key="soil_oc"),
        "Soil moisture (%)": st.text_input("Soil moisture (%)", key="soil_moisture"),
        "EC": st.text_input("EC (include unit)", key="soil_ec"),
    }
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_problem = ""
        st.session_state.pending_details = []
        st.session_state.processed_audio = None
        clear_messages(st.session_state.chat_id)
        st.rerun()
    st.caption("Weather · RAG knowledge · Soil guidance · Crop calendar")


def clean_soil(values):
    return {k: v for k, v in values.items() if v is not None and str(v).strip()}


def show_weather(result):
    weather = result.get("weather", {})
    current = weather.get("current", {})
    if current:
        with st.expander("🌦️ Current weather", expanded=False):
            st.caption(f"{weather.get('location', city)}, {weather.get('state', '')}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temperature", f"{current.get('temperature_2m', '—')} °C")
            c2.metric("Humidity", f"{current.get('relative_humidity_2m', '—')}%")
            c3.metric("Rainfall", f"{current.get('precipitation', '—')} mm")
            c4.metric("Wind", f"{current.get('wind_speed_10m', '—')} km/h")


if page == "💬 Ask KrishiMitra":
    st.info("Pehle apni problem batayein. KrishiMitra zaroori details poochega; details milne ke baad hi final advice dega.")

    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🌱"):
            st.write("Namaste! Aapki fasal mein kya problem hai? Jaise: 'Mere dhaan ke patte peele ho rahe hain.' Main pehle kuch zaroori details poochunga, phir salah dunga.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🌱" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    st.write("**🎙️ Voice question (optional)**")
    audio = st.audio_input("Record your farming question", key="farmer_audio")
    voice_col, hint_col = st.columns([1, 3])
    with voice_col:
        voice_send = st.button("Send voice", disabled=(audio is None), use_container_width=True)
    with hint_col:
        st.caption("Ya neeche message type karein. Voice ko text mein convert karke chat mein bheja jayega.")
    typed_question = st.chat_input("Apni farming problem ya follow-up detail type karein...")

    new_message = None
    if typed_question and typed_question.strip():
        new_message = typed_question.strip()
    elif voice_send and audio is not None:
        audio_bytes = audio.getvalue()
        audio_id = hash(audio_bytes)
        if st.session_state.processed_audio == audio_id:
            st.warning("Ye recording pehle process ho chuki hai. Nayi recording karein.")
        else:
            try:
                with st.spinner("Aapki voice ko text mein badal raha hoon..."):
                    new_message = transcribe_farmer_audio(audio_bytes, getattr(audio, "type", None) or "audio/wav", language)
                st.session_state.processed_audio = audio_id
            except Exception as exc:
                st.error(f"Voice process nahi ho payi: {exc}")

    if new_message:
        if not city.strip():
            st.error("Sidebar mein location enter karein.")
        else:
            st.session_state.messages.append({"role": "user", "content": new_message})
            add_message(st.session_state.chat_id, "user", new_message)
            with st.chat_message("user"):
                st.markdown(new_message)

            if st.session_state.pending_problem:
                st.session_state.pending_details.append(new_message)
                problem = st.session_state.pending_problem
                details = "\n".join(st.session_state.pending_details)
            else:
                problem = new_message
                details = ""
                st.session_state.pending_problem = problem
                st.session_state.pending_details = []

            recent_history = "\n".join(
                f"{m['role']}: {m['content']}" for m in st.session_state.messages[-8:-1]
            )
            try:
                with st.chat_message("assistant", avatar="🌱"):
                    with st.spinner("Aapki problem samajh raha hoon aur zaroori details check kar raha hoon..."):
                        intake = assess_question(
                            problem=problem, details=details, crop=crop,
                            location=city, language=language, history=recent_history
                        )

                    if intake["status"] == "ask":
                        clarification = intake["question"] or ("कृपया फसल की अवस्था और समस्या कब से है, बताइए।" if language == "Hindi" else "Please share the crop stage and when the problem started.")
                        st.markdown(clarification)
                        st.session_state.messages.append({"role": "assistant", "content": clarification})
                        add_message(st.session_state.chat_id, "assistant", clarification)
                    else:
                        combined_question = (
                            f"Farmer's original problem: {problem}\n\n"
                            f"Farmer's clarification/details: {details or 'No additional details'}\n\n"
                            f"Latest conversation context: {recent_history}"
                        )
                        with st.spinner("Weather aur agricultural knowledge check karke advice bana raha hoon..."):
                            result = run_krishimitra(
                                city=city.strip(), crop=crop, question=combined_question,
                                language=language, soil_metrics=clean_soil(soil_metrics)
                            )
                        show_weather(result)
                        answer = result.get("response", "Sorry, abhi answer generate nahi ho paya.")
                        st.markdown(answer)
                        st.caption("Fertilizer/pesticide ki exact dose local KVK ya agriculture officer se verify karein.")
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        add_message(st.session_state.chat_id, "assistant", answer)
                        st.session_state.pending_problem = ""
                        st.session_state.pending_details = []
            except Exception as exc:
                error_message = f"Request process nahi ho payi: {exc}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                add_message(st.session_state.chat_id, "assistant", error_message)

elif page == "📅 Crop Schedule":
    st.subheader("📅 Personalized Crop Schedule")
    st.write("Crop select karein aur sowing/transplanting date dein. KrishiMitra stage-wise calendar banayega. Agar variety ya season important hua, pehle clarification pooch sakta hai.")
    with st.form("schedule_form"):
        schedule_crop = st.selectbox("Crop", crop_options, index=crop_options.index(crop), key="schedule_crop")
        variety = st.text_input("Crop variety (if known)", placeholder="e.g. Swarna, MTU-1010")
        season = st.selectbox("Season", ["Kharif", "Rabi", "Zaid", "Not sure"], index=0)
        sowing_date = st.date_input("Sowing/transplanting date", value=date.today())
        current_stage = st.text_input("Current crop stage (optional)", placeholder="e.g. 20 days after transplanting")
        schedule_submit = st.form_submit_button("Generate crop schedule", use_container_width=True)

    if schedule_submit:
        if not city.strip():
            st.error("Please enter your location in the sidebar.")
        else:
            schedule_question = (
                "Create a personalized crop schedule for this farmer. Give a clear stage-wise calendar "
                "from the provided sowing/transplanting date through harvest. Include approximate dates "
                "only where locally and varietally reasonable; otherwise use days after sowing/transplanting. "
                "Cover field preparation if still relevant, irrigation, nutrient/soil checks, weed/pest monitoring, "
                "critical growth stages and harvest readiness. Do not invent exact fertilizer or pesticide doses.\n"
                f"Crop: {schedule_crop}\nVariety: {variety or 'Not known'}\nSeason: {season}\n"
                f"Sowing/transplanting date: {sowing_date}\nCurrent stage: {current_stage or 'Not provided'}."
            )
            try:
                with st.spinner("Weather aur agricultural references ke saath crop calendar bana raha hoon..."):
                    result = run_krishimitra(
                        city=city.strip(), crop=schedule_crop, question=schedule_question,
                        language=language, soil_metrics=clean_soil(soil_metrics),
                        sowing_date=str(sowing_date)
                    )
                show_weather(result)
                st.markdown(result.get("response", "Schedule generate nahi ho paya."))
            except Exception as exc:
                st.error(f"Schedule generate nahi ho paya: {exc}")


elif page == "🧪 Soil Health Dashboard":
    st.subheader("🧪 Soil Health Dashboard")
    st.write("Soil Health Card ya lab report ke values sidebar mein enter karein. Unknown values blank chhodein.")
    values = clean_soil(soil_metrics)
    if not values:
        st.info("Dashboard dekhne ke liye sidebar mein soil report ke values enter karein.")
    else:
        st.caption("Farmer-provided values · Lab-verified nahi maane jaate jab tak report confirm na ho.")
        cols = st.columns(3)
        for idx, (name, value) in enumerate(values.items()):
            cols[idx % 3].metric(name, value)
        st.divider()
        if st.button("Explain my soil report", use_container_width=True):
            soil_question = (
                "Explain these farmer-provided soil metrics in simple terms for the selected crop. "
                "Identify what each parameter generally indicates, what cannot be concluded without "
                "units/test method/crop stage, and what follow-up soil test or local expert advice is needed. "
                "Do not invent missing values or exact fertilizer doses. Soil values: " + str(values)
            )
            try:
                with st.spinner("Soil report ko samajh raha hoon..."):
                    result = run_krishimitra(city=city.strip(), crop=crop, question=soil_question,
                                             language=language, soil_metrics=values)
                show_weather(result)
                st.markdown(result.get("response", "Soil explanation generate nahi ho paya."))
            except Exception as exc:
                st.error(f"Soil explanation nahi ban paya: {exc}")
    st.warning("Soil metrics akelay fertilizer recommendation ke liye kaafi nahi hote. Crop stage, units, sampling method aur local recommendations bhi zaroori hain.")

elif page == "📷 Disease Detection":
    st.subheader("📷 Crop Disease / Symptom Detection")
    st.write("Fasal ya affected leaf ki clear photo upload karein. AI visible symptoms ke possible causes batayega; ye final diagnosis nahi hai.")
    uploaded_image = st.file_uploader("Upload crop/leaf image", type=["jpg", "jpeg", "png", "webp"], key="crop_image")
    farmer_note = st.text_area("Additional details (optional)", placeholder="Problem kab se hai? Kitne plants affected hain? Recent rain/irrigation?")
    if uploaded_image is not None:
        st.image(uploaded_image, caption="Uploaded crop image", use_container_width=True)
        if st.button("Analyze crop image", type="primary", use_container_width=True):
            try:
                with st.spinner("Image mein visible symptoms analyze kar raha hoon..."):
                    diagnosis = analyze_crop_image(
                        image_bytes=uploaded_image.getvalue(),
                        mime_type=uploaded_image.type or "image/jpeg",
                        crop=crop,
                        location=city,
                        language=language,
                        question=farmer_note
                    )
                st.markdown(diagnosis)
                st.caption("AI image triage is not a confirmed diagnosis. Chemical treatment se pehle local KVK/agriculture officer se verify karein.")
            except Exception as exc:
                st.error(f"Image analyze nahi ho payi: {exc}")
