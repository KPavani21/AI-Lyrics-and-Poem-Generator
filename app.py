
import streamlit as st
import google.generativeai as genai
import html
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

from database import (
    initialize_db,
    save_content,
    get_history,
    get_favourites,
    delete_content,
    toggle_favourite
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Melody Studio | AI Lyrics & Poetry",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# API CONFIGURATION
# --------------------------------------------------

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error(
        "Gemini API key not found. Add GEMINI_API_KEY "
        "to .streamlit/secrets.toml"
    )
    st.stop()

model = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

initialize_db()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "generated_text": "",
    "current_details": {},
    "translated_text": "",
    "translated_language": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --------------------------------------------------
# THEME
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🎼 Melody Studio")
    st.caption("Your personal AI songwriting space")
    st.divider()

    dark_mode = st.toggle("Dark appearance", value=False)

if dark_mode:
    bg = "#171923"
    surface = "#222534"
    text = "#F5F2F7"
    muted = "#B8B3C4"
    border = "#39394A"
    input_bg = "#252838"
else:
    bg = "#FAF8F5"
    surface = "#FFFFFF"
    text = "#292735"
    muted = "#777383"
    border = "#EAE5E9"
    input_bg = "#FFFFFF"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {bg};
        color: {text};
    }}

    [data-testid="stSidebar"] {{
        background: {surface};
        border-right: 1px solid {border};
    }}

    h1, h2, h3, h4, p, label, span {{
        color: {text};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {{
        background: {input_bg};
        color: {text};
        border-radius: 12px;
        border: 1px solid {border};
    }}

    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
        background: {input_bg};
        border-radius: 10px;
        border-color: {border};
    }}

    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 11px;
        min-height: 43px;
        font-weight: 600;
        border: 1px solid {border};
        transition: all 0.2s ease;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        border-color: #A68BC7;
        transform: translateY(-1px);
    }}

    div[data-testid="stButton"] button[kind="primary"] {{
        background: #8170A8;
        color: white;
        border: none;
    }}

    .hero {{
        background: linear-gradient(
            115deg,
            #F1EAF5 0%,
            #F8EEE9 55%,
            #F8F3ED 100%
        );
        border: 1px solid #E9DFE9;
        border-radius: 22px;
        padding: 30px;
        margin-bottom: 24px;
        color: #30283A;
    }}

    .hero h1 {{
        color: #30283A !important;
        font-size: 2.35rem;
        margin: 5px 0 8px 0;
        letter-spacing: -1px;
    }}

    .hero p {{
        color: #706477 !important;
        margin-bottom: 0;
        font-size: 1rem;
    }}

    .eyebrow {{
        color: #89739C !important;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    .wave {{
        display: flex;
        align-items: center;
        gap: 4px;
        height: 48px;
        margin-top: 18px;
    }}

    .wave span {{
        display: block;
        width: 4px;
        border-radius: 8px;
        background: #9B82B4;
        opacity: 0.8;
    }}

    .wave span:nth-child(1), .wave span:nth-child(9) {{height: 12px;}}
    .wave span:nth-child(2), .wave span:nth-child(8) {{height: 22px;}}
    .wave span:nth-child(3), .wave span:nth-child(7) {{height: 32px;}}
    .wave span:nth-child(4), .wave span:nth-child(6) {{height: 19px;}}
    .wave span:nth-child(5) {{height: 42px;}}

    .section-kicker {{
        color: #9B82B4;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    .creation-card {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 18px;
        padding: 22px;
        margin: 12px 0;
    }}

    .creation-label {{
        color: #9B82B4 !important;
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        font-weight: 700;
        text-transform: uppercase;
    }}

    .small-note {{
        color: {muted} !important;
        font-size: 0.85rem;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 9px;
        padding: 10px 16px;
    }}

    @media (max-width: 700px) {{
        .hero {{padding: 22px;}}
        .hero h1 {{font-size: 1.8rem;}}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# AI FUNCTION
# --------------------------------------------------

def generate_ai_content(prompt):
    try:
        response = model.generate_content(prompt)

        if not response.text:
            st.error("AI returned an empty response. Please try again.")
            return None

        return response.text.strip()

    except Exception as error:
        st.error(f"Generation failed: {error}")
        return None

# --------------------------------------------------
# PDF FUNCTION
# --------------------------------------------------

def create_pdf(content, title):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    heading = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#76618E"),
        fontSize=19,
        spaceAfter=20
    )

    body = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=17,
        spaceAfter=8
    )

    story = [Paragraph(html.escape(title), heading)]

    for line in content.split("\n"):
        safe_line = html.escape(line) if line.strip() else "&#160;"
        story.append(Paragraph(safe_line, body))

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --------------------------------------------------
# SAVE GENERATED CONTENT
# --------------------------------------------------

def save_generated_content(content):
    details = st.session_state.current_details

    save_content(
        details.get("choice", "Poem"),
        details.get("theme", ""),
        details.get("language", "English"),
        details.get("style", ""),
        content
    )

# --------------------------------------------------
# HERO HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Your personal creative space</div>
        <h1>Every feeling has a melody. ♫</h1>
        <p>
            Turn your thoughts, emotions and little moments
            into beautiful poems and song lyrics with AI.
        </p>
        <div class="wave">
            <span></span><span></span><span></span>
            <span></span><span></span><span></span>
            <span></span><span></span><span></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# SIDEBAR CREATION SETTINGS
# --------------------------------------------------

with st.sidebar:
    st.markdown("### ✍️ Creation settings")

    theme = st.text_input(
        "What's on your mind?",
        placeholder="Love, rain, friendship..."
    )

    choice = st.radio(
        "Create",
        ["Song Lyrics", "Poem"],
        horizontal=True
    )

    style = st.selectbox(
        "Writing style",
        [
            "Romantic", "Sad", "Motivational", "Happy",
            "Devotional", "Friendship", "Nature", "Rap"
        ]
    )

    language = st.selectbox(
        "Language",
        ["English", "Telugu", "Hindi"]
    )

    genre = st.selectbox(
        "Music genre",
        ["Melody", "Pop", "Rock", "Folk", "Rap"]
    )

    tone = st.selectbox(
        "Mood / Tone",
        [
            "Emotional", "Simple", "Creative",
            "Inspirational", "Funny", "Deep"
        ]
    )

    length = st.select_slider(
        "Creation length",
        options=["Short", "Medium", "Long"],
        value="Medium"
    )

    st.divider()

    generate_clicked = st.button(
        "♫ Create my masterpiece",
        type="primary",
        use_container_width=True
    )

    st.caption("Powered by Google Gemini AI")

# --------------------------------------------------
# MAIN CREATION AREA
# --------------------------------------------------

left, right = st.columns([1.5, 1])

with left:
    st.markdown("### Create something meaningful")
    st.markdown(
        '<p class="small-note">A feeling, a memory, a story — '
        'start with just one idea.</p>',
        unsafe_allow_html=True
    )

with right:
    st.markdown(
        '<p style="text-align:right; color:#9B82B4; '
        'font-size:0.85rem;">♫ WRITE • FEEL • CREATE</p>',
        unsafe_allow_html=True
    )

# --------------------------------------------------
# GENERATE CONTENT
# --------------------------------------------------

if generate_clicked:
    if not theme.strip():
        st.warning("Please enter a theme or emotion in the sidebar.")
    else:
        if choice == "Song Lyrics":
            format_instruction = (
                "Structure the song with a suitable title, verses, "
                "a memorable chorus, and an optional bridge. "
                "Make the lyrics sound natural and singable."
            )
        else:
            format_instruction = (
                "Write a meaningful poem with a suitable title, "
                "beautiful imagery and a natural poetic flow."
            )

        prompt = f"""
        Write an original {choice.lower()} about: {theme}.

        Language: {language}
        Writing style: {style}
        Genre: {genre}
        Mood: {tone}
        Length: {length}

        Requirements:
        - {format_instruction}
        - Make it original, creative and emotionally engaging.
        - Use natural language.
        - Match the selected mood and genre.
        - Return only the creative work, without an introduction.
        """

        with st.spinner("Composing your creation... ♫"):
            result = generate_ai_content(prompt)

        if result:
            st.session_state.generated_text = result
            st.session_state.translated_text = ""

            st.session_state.current_details = {
                "theme": theme,
                "choice": choice,
                "style": style,
                "language": language,
                "genre": genre,
                "tone": tone,
                "length": length
            }

            save_generated_content(result)
            st.success("Your creation is ready!")

# --------------------------------------------------
# DISPLAY CREATION
# --------------------------------------------------

if st.session_state.generated_text:
    content = st.session_state.generated_text
    details = st.session_state.current_details

    st.divider()

    st.markdown(
        '<div class="section-kicker">Your original creation</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"## 🎙️ {details.get('choice', 'Your Creation')}"
    )

    st.markdown(
        f'<p class="small-note">♫ {details.get("theme", "")} '
        f'&nbsp; • &nbsp; {details.get("style", "")} '
        f'&nbsp; • &nbsp; {details.get("language", "")}</p>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.text_area(
            "Your lyrics / poem",
            value=content,
            height=390,
            key="main_creation_editor"
        )

    txt_col, pdf_col, fav_col = st.columns(3)

    with txt_col:
        st.download_button(
            "↓ Download TXT",
            data=content,
            file_name="Melody_Studio_Creation.txt",
            mime="text/plain",
            use_container_width=True
        )

    with pdf_col:
        pdf_data = create_pdf(content, "Melody Studio")
        st.download_button(
            "↓ Download PDF",
            data=pdf_data,
            file_name="Melody_Studio_Creation.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with fav_col:
        if st.button("♡ Save to favourites", use_container_width=True):
            save_content(
                details.get("choice", "Poem"),
                details.get("theme", ""),
                details.get("language", "English"),
                details.get("style", ""),
                content,
                favourite=True
            )
            st.success("Saved to your favourites!")

    # --------------------------------------------------
    # IMPROVE AND REGENERATE
    # --------------------------------------------------

    st.divider()
    st.markdown("### ✨ Refine your creation")
    st.caption(
        "Give your writing a fresh direction or polish the words."
    )

    improve_col, regenerate_col = st.columns(2)

    with improve_col:
        if st.button("✧ Improve writing", use_container_width=True):
            with st.spinner("Refining your words..."):
                improved = generate_ai_content(
                    "Improve the following creative work. Preserve "
                    "its original meaning, language and emotion. "
                    "Improve vocabulary, rhythm, flow, imagery and "
                    "creativity. Return only the improved version:\n\n"
                    + content
                )

            if improved:
                st.session_state.generated_text = improved
                save_generated_content(improved)
                st.rerun()

    with regenerate_col:
        if st.button("⟳ Create another version", use_container_width=True):
            with st.spinner("Composing another version..."):
                regenerated = generate_ai_content(
                    f"Write a fresh and distinct {details.get('choice', 'poem')} "
                    f"about {details.get('theme', '')}. "
                    f"Language: {details.get('language', 'English')}. "
                    f"Style: {details.get('style', '')}. "
                    f"Genre: {details.get('genre', '')}. "
                    "Make it original and emotionally engaging. "
                    "Return only the creative work."
                )

            if regenerated:
                st.session_state.generated_text = regenerated
                st.session_state.translated_text = ""
                save_generated_content(regenerated)
                st.rerun()

    # --------------------------------------------------
    # TRANSLATION
    # --------------------------------------------------

    st.divider()
    st.markdown("### 🌍 Translate your creation")

    translate_col, translate_button_col = st.columns([2, 1])

    with translate_col:
        target_language = st.selectbox(
            "Choose translation language",
            ["Telugu", "English", "Hindi"],
            key="target_language"
        )

    with translate_button_col:
        st.write("")
        st.write("")
        translate_clicked = st.button(
            "Translate",
            use_container_width=True
        )

    if translate_clicked:
        with st.spinner("Translating your creation..."):
            translated = generate_ai_content(
                f"Translate this creative work into {target_language}. "
                "Preserve its meaning, emotions, poetic quality and "
                "structure. Return only the translation:\n\n"
                + content
            )

        if translated:
            st.session_state.translated_text = translated
            st.session_state.translated_language = target_language

    if st.session_state.translated_text:
        st.markdown(
            f"#### Translation — {st.session_state.translated_language}"
        )

        st.text_area(
            "Translated creation",
            value=st.session_state.translated_text,
            height=250,
            key="translation_display"
        )

        st.download_button(
            "↓ Download translation",
            data=st.session_state.translated_text,
            file_name="Melody_Studio_Translation.txt",
            mime="text/plain"
        )

else:
    st.markdown(
        """
        <div class="creation-card">
            <div class="creation-label">The blank page</div>
            <h3>Every great song begins with a feeling.</h3>
            <p style="color:#8B8491;">
                Add your theme and choose your creative style
                from the sidebar. Your next poem or song is
                waiting to be written.
            </p>
            <div style="font-size:32px; color:#A58BB8;">
                ♫  ♪  ♬  ♩
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --------------------------------------------------
# LIBRARY: HISTORY AND FAVOURITES
# --------------------------------------------------

st.divider()

st.markdown("## 📚 Your creative library")
st.caption("Revisit the words and melodies you've created.")

history_tab, favourites_tab = st.tabs(
    ["♫ History", "♡ Favourites"]
)

with history_tab:
    history = get_history()

    if history:
        for item in history:
            with st.expander(
                f"{item[1]}  ·  {item[2]}  ·  {item[6]}"
            ):
                st.write(item[5])

                if st.button(
                    "Delete from history",
                    key=f"history_delete_{item[0]}"
                ):
                    delete_content(item[0])
                    st.rerun()
    else:
        st.info("Your creations will appear here after you generate them.")

with favourites_tab:
    favourites = get_favourites()

    if favourites:
        for item in favourites:
            with st.expander(
                f"{item[1]}  ·  {item[2]}  ·  {item[6]}"
            ):
                st.write(item[5])

                if st.button(
                    "Remove from favourites",
                    key=f"favourite_delete_{item[0]}"
                ):
                    toggle_favourite(item[0], False)
                    st.rerun()
    else:
        st.info("Your favourite creations will appear here.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    """
    <div style="text-align:center; padding:15px 0;">
        <div style="font-size:23px; color:#9B82B4;">♫</div>
        <p style="color:#898391; font-size:0.85rem;">
            Made with creativity by Pavz
            <br>
            A little music. A lot of emotion.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
