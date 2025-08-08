import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Register Arial Unicode font with a specific name
#font_path = "C:/Windows/Fonts/arialuni.ttf"  # Ensure this path is correct
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
st.set_page_config(layout="wide")

# Function to load words from CSV
@st.cache_data
def lade_woerter(csv_datei):
    return pd.read_csv(csv_datei)

# Function to generate PDF using ReportLab
def generate_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Set font and size to the registered font name
    c.setFont("ArialUnicode", 12)

    # Title
    c.drawString(100, 750, "Übungsblatt – Chinesische Schriftzeichen")

    # Starting position for the content
    y_position = 700

    for _, row in df.iterrows():
        # Draw symbol, pronunciation, and meaning
        line = f"{row['zeichen']} [{row['aussprache']}] – {row['bedeutung']}"
        c.drawString(100, y_position, line)

        # Draw empty boxes for practice
        box_y_position = y_position - 20
        box_width = 50
        box_height = 30
        box_spacing = 60  # Horizontal spacing between boxes

        # Draw multiple boxes horizontally
        for i in range(3):  # Create 3 empty boxes for practice
            box_x_position = 100 + i * box_spacing
            c.rect(box_x_position, box_y_position, box_width, box_height, stroke=1, fill=0)

        y_position -= 80  # Adjust vertical position for next entry

    c.save()
    buffer.seek(0)
    return buffer

st.title("📚 Chinesisch Übungsblätter Generator")

# File upload
csv_datei = st.file_uploader("📤 Lade deine CSV-Datei hoch", type=["csv"])

if csv_datei:
    df = lade_woerter(csv_datei)
    st.success("Datei erfolgreich geladen! ✅")
    st.dataframe(df)

    # Filter options
    kapitel = st.multiselect("📘 Kapitel auswählen", sorted(df["kapitel"].unique()))
    aussprache = st.text_input("🔤 Filter: Aussprache ohne Ton (z. B. 'hao')")
    grammatik = st.multiselect("🧠 Grammatikalische Kategorie wählen", sorted(df["grammatik"].dropna().unique()))
#    kategorie = st.multiselect("📂 Wort-Kategorie wählen", df["kategorie"].value_counts().index.tolist())
    hsk = st.multiselect("📊 HSK-Niveau auswählen", sorted(df["HSK"].dropna().unique()))
    # --- Kategorien zusammenführen ---
    df["alle_tags"] = df[["kategorie 1", "kategorie 2", "kategorie 3"]] \
        .fillna("") \
        .agg("|".join, axis=1) \
        .str.split("|")
    alle_tags_einzigartig = sorted({tag for tags in df["alle_tags"] for tag in tags if tag})
    tags_filter = st.multiselect("🏷️ Tags auswählen (aus allen Kategorien)", alle_tags_einzigartig)

    # Filter data
    gefiltert = df.copy()
    if kapitel:
        gefiltert = gefiltert[gefiltert["kapitel"].isin(kapitel)]
    if aussprache:
        gefiltert = gefiltert[gefiltert["aussprache_ohne_ton"].str.lower() == aussprache.lower()]
    if grammatik:
        gefiltert = gefiltert[gefiltert["grammatik"].isin(grammatik)]
#    if kategorie:
#        gefiltert = gefiltert[gefiltert["kategorie"].isin(kategorie)]
    if tags_filter:
        gefiltert = gefiltert[gefiltert["alle_tags"].apply(lambda tag_liste: any(tag in tag_liste for tag in tags_filter))]

    st.write(f"Gefundene Wörter: {len(gefiltert)}")
    st.dataframe(gefiltert)

    if not gefiltert.empty:
        if st.button("📄 PDF generieren"):
            pdf_bytes = generate_pdf(gefiltert)
            st.download_button(
                label="📥 PDF herunterladen",
                data=pdf_bytes,
                file_name="uebungsblatt.pdf",
                mime="application/pdf"
            )


