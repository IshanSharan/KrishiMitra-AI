
from rag.retriever import retrieve_documents
from backend.llm import generate_response


def ask_krishimitra(
    crop,
    location,
    weather,
    question,
    language="Hindi",
    soil_metrics=None,
    sowing_date=None
):

    print("\nSearching agricultural knowledge base...")

    # ==================================
    # STEP 1: LOCATION-AWARE RETRIEVAL
    # ==================================

    documents = retrieve_documents(
        question=question,
        location=location,
        crop=crop,
        k=4
    )

    print(f"Retrieved documents: {len(documents)}")

    # ==================================
    # STEP 2: FILTER AND PREPARE CONTEXT
    # ==================================

    context = ""
    usable_documents = []

    is_assam = "assam" in location.lower()

    for doc in documents:

        metadata = doc.metadata

        source = metadata.get(
            "document_name",
            metadata.get("source", "Unknown")
        )

        page = metadata.get("page", "Unknown")
        state = metadata.get("state", "Unknown")

        region_scope = metadata.get(
            "region_scope",
            "unknown"
        )

        if region_scope == "assam" and not is_assam:
            continue

        usable_documents.append(doc)

        context += f"""
DOCUMENT {len(usable_documents)}

Source: {source}
Page: {page}
State: {state}
Regional Scope: {region_scope}

Content:
{doc.page_content}

--------------------------------
"""

    # ==================================
    # STEP 3: PREPARE WEATHER DETAILS
    # ==================================

    if weather:

        current = weather.get("current", {})
        daily = weather.get("daily", {})

        weather_details = f"""
Temperature: {current.get('temperature_2m', 'Unavailable')} °C
Humidity: {current.get('relative_humidity_2m', 'Unavailable')} %
Current Rainfall: {current.get('precipitation', 'Unavailable')} mm
Wind Speed: {current.get('wind_speed_10m', 'Unavailable')} km/h
Daily Rainfall Forecast: {daily.get('precipitation_sum', 'Unavailable')} mm
Rain Probability: {daily.get('precipitation_probability_max', 'Unavailable')} %
"""

    else:

        weather_details = "Weather information unavailable."

    # ==================================
    # STEP 4: KNOWLEDGE SOURCE STATUS
    # ==================================

    if usable_documents:

        knowledge_status = """
Candidate documents have been retrieved.

Use their information only when it is relevant
to the farmer's question and regionally applicable.

Check the crop, topic and geographical context.
Do not force irrelevant information into the answer.
"""

    else:

        knowledge_status = """
No relevant and regionally applicable document was found.

You MUST STILL GENERATE A USEFUL AGRICULTURAL ANSWER.

Use general agricultural knowledge, considering the crop,
location, farmer's question and available weather.

Do not claim that general knowledge came from the
knowledge base or an official agricultural source.
"""

    # ==================================
    # STEP 5: PREPARE SOIL AND SCHEDULING DATA
    # ==================================

    soil_metrics = soil_metrics or {}
    supplied_soil = {
        key: value for key, value in soil_metrics.items()
        if value is not None and str(value).strip() != ""
    }
    soil_details = (
        "\\n".join(f"{key}: {value}" for key, value in supplied_soil.items())
        if supplied_soil else "Not provided by farmer."
    )
    sowing_details = sowing_date or "Not provided"

    prompt = f"""
You are KrishiMitra AI, a personalized agricultural
advisory assistant for farmers across India.

Your goal is to provide accurate, practical and
easy-to-understand farming advice.

========================================
FARMER DETAILS
========================================

Location: {location}
Crop: {crop}
Preferred Language: {language}
Sowing Date: {sowing_details}

Soil Metrics supplied by farmer:
{soil_details}

========================================
CURRENT WEATHER
========================================

{weather_details}

========================================
FARMER'S QUESTION
========================================

{question}

========================================
RETRIEVED AGRICULTURAL KNOWLEDGE
========================================

{context if context else "No applicable document context available."}

========================================
KNOWLEDGE SOURCE STATUS
========================================

{knowledge_status}

========================================
PERSONALIZATION RULES
========================================

1. Understand the farmer's exact problem.

2. Consider the farmer's crop, location and available weather.

3. Give practical actions, not textbook explanations.

4. Explain why an important recommendation is useful.

5. Avoid repetitive and generic advice.

6. Do not assume soil type, crop age, crop stage or
   local pest prevalence from the city name alone.

7. The intake stage has already collected essential details.
   If one critical detail is still missing, ask it before giving risky advice;
   otherwise answer the farmer directly.
8. Treat soil values as farmer-provided data, not lab-verified facts.
9. Interpret pH, NPK, organic carbon, moisture and EC cautiously.
10. Never invent missing soil values or fertilizer doses.
11. If asked for crop scheduling, create a practical stage-wise
    calendar using the sowing date, crop and location. Use actual
    dates only when supported; otherwise label timings as approximate.
    Account for local season and variety; ask for variety if essential.

8. Use relevant documents as the primary reference.

9. If documents do not contain the required information,
   use general agricultural knowledge.

10. Clearly distinguish general guidance from verified
    location-specific recommendations.

========================================
REGIONAL KNOWLEDGE RULES
========================================

1. The three Package of Practice documents are specific
   to Assam.

2. Use Assam-specific recommendations as verified references
   only for farmers located in Assam.

3. Never apply Assam-specific recommendations to Bihar,
   Punjab, Rajasthan, Maharashtra or other states.

4. Check the actual content and regional applicability
   of the ICAR advisory before using its recommendations.

5. Do not assume every ICAR recommendation applies
   throughout India.

6. Never invent local research or government recommendations.

========================================
SAFETY AND ACCURACY RULES
========================================

1. Never invent fertilizer doses, pesticide quantities,
   chemical concentrations or spraying schedules.

2. Give exact chemical recommendations only when supported
   by reliable and regionally applicable information.

3. Otherwise, recommend checking the product label and
   consulting the local KVK or agriculture department.

4. Never diagnose a crop disease with certainty from
   insufficient information.

5. Never invent statistics, schemes or official sources.

6. Never claim that a recommendation came from a document
   unless that document actually supports it.

========================================
SHORT ANSWER RULES
========================================

1. Answer entirely in {language}.

2. Keep the answer between 80 and 120 words whenever
   the question can be answered safely within that limit.

3. Be direct. Start with the actual answer.

4. Give only 2-4 important practical recommendations.

5. Avoid long introductions, unnecessary headings
   and textbook explanations.

6. Mention weather only when it affects the recommendation.

7. Do not end with a follow-up question unless one critical detail
   is genuinely required for safety or accuracy.

8. Accuracy and safety are more important than the word limit.
   If necessary, use a few extra words to explain an important
   precaution.

========================================
RESPONSE FORMAT
========================================

Use this structure naturally:

- Direct answer.
- 2-4 practical recommendations.
- One important precaution, if needed.
- One follow-up question, only if necessary.
- Brief source note at the end.

If applicable documents were used:
Mention the document name and page number.

If no applicable document was used:
Briefly mention that the guidance is based on general
agricultural knowledge, not verified local documentation.

Do not include empty sections.

Now generate the advisory.
"""

    # ==================================
    # STEP 6: GENERATE RESPONSE
    # ==================================

    print("\nGenerating personalized advisory using Gemini...")

    response = generate_response(prompt)

    return response
