import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from io import BytesIO
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import requests
# Register Arial Unicode font with a specific name
#font_path = "C:/Windows/Fonts/arialuni.ttf"  # Ensure this path is correct
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
pdfmetrics.registerFont(TTFont('NotoSansCJK', 'NotoSansCJK-Regular.ttf'))
st.set_page_config(layout="wide")
if "df" not in st.session_state:
    st.session_state.df = None
# Function to load words from CSV
@st.cache_data
def lade_woerter(csv_datei):
    return pd.read_csv(csv_datei, encoding="utf-8")

# Function to load file from GitHub
def load_file_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# Function to generate PDF using ReportLab
def generate_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Überschrift
    c.setFont('NotoSansCJK', 16)
    #c.setFont("STSong-Light", 16)
    c.drawString(100, 780, "Übungsblatt – Chinesische Schriftzeichen")

    y_position = 750
    box_width = 30
    box_height = 30
    box_spacing = 5
    page_margin_bottom = 30

    for _, row in df.iterrows():
        # Zeile mit Zeichen, Pinyin (mit Ton) und Bedeutung
        #c.setFont("STSong-Light", 14)
        c.setFont('NotoSansCJK', 12)
        line = f"{row['zeichen']}  [{row['aussprache']}]  –  {row['bedeutung']}"
        c.drawString(100, y_position, line)
        y_position -= 10#30

        # Wie viele Symbole (="Boxen")?
        zeichen_text = str(row['zeichen'])
        n_boxen = 12#len(zeichen_text)

        # Leere Kästchen nebeneinander
        for i in range(n_boxen):
            box_x = 100 + i * (box_width + box_spacing)
            c.rect(box_x, y_position - box_height, box_width, box_height, stroke=1, fill=0)
        y_position -= (box_height + 25)

        # Seitenumbruch falls nötig
        if y_position < page_margin_bottom + box_height:
            c.showPage()
            c.setFont('NotoSansCJK', 12)
            #c.setFont("STSong-Light", 14)
            y_position = 750

    c.save()
    buffer.seek(0)
    return buffer


st.title("📚 Chinesisch Übungsblätter Generator")

# File upload
csv_datei = st.file_uploader("📤 Lade deine CSV-Datei hoch", type=["csv"])
github_file_url = "https://raw.githubusercontent.com/angelos-th/mandarin_csv_pdf/refs/heads/main/Kap.1-12.csv"#"https://raw.githubusercontent.com/angelos-th/mandarin_csv_pdf/refs/heads/main/Kap.1-12.csv"

# Initialize df as None
df = None

# Button to load the file from GitHub
if st.button("Buch Wortschatz Kap. 1-12"):
    file_content = load_file_from_github(github_file_url)
    if file_content:
        st.write("File loaded successfully!")
        # Assuming the file from GitHub is a CSV
        #df = pd.read_csv(io.StringIO(file_content), encoding="utf-8")
        st.session_state.df = pd.read_csv(io.StringIO(file_content), encoding="utf-8")
        st.success("File loaded successfully from GitHub! ✅")
        st.dataframe(st.session_state.df)
        #st.dataframe(df)
    else:
        st.write("Failed to load the file.")



# Load and display the CSV file if uploaded
if csv_datei:
    #df = lade_woerter(csv_datei)
    #st.success("Datei erfolgreich geladen! ✅")
    st.session_state.df = lade_woerter(csv_datei)
    st.success("Datei erfolgreich geladen! ✅")
    st.dataframe(st.session_state.df)
    #st.dataframe(df)
df = st.session_state.df
# Proceed only if df is not None
if df is not None:
    # Filter options
    kapitel_liste = sorted(df["kapitel"].dropna().unique())
    
    kapitel = st.multiselect("📘 Kapitel auswählen", kapitel_liste)#st.multiselect("📘 Kapitel auswählen", sorted(df["kapitel"].unique()))
    aussprache = st.text_input("🔤 Filter: Aussprache ohne Ton (z. B. 'hao')")
    grammatik = st.multiselect("🧠 Grammatikalische Kategorie wählen", sorted(df["grammatik"].dropna().unique()))
    hsk = st.multiselect("📊 HSK-Niveau auswählen", sorted(df["HSK"].dropna().unique()))

    # --- Kategorien zusammenführen ---
    df["alle_tags"] = (
        df[["kategorie 1", "kategorie 2", "kategorie 3"]]
        .fillna("")
        .agg("|".join, axis=1)
        .str.split("|")
        .apply(lambda lst: [tag.strip() for tag in lst if tag.strip()])
    )
    alle_tags_einzigartig = sorted({tag for tags in df["alle_tags"] for tag in tags if tag})
    tags_filter = st.multiselect("🏷️ Tags auswählen (aus allen Kategorien)", alle_tags_einzigartig)

    # Filter data
    gefiltert = df.copy()
    if kapitel:
        gefiltert = gefiltert[gefiltert["kapitel"].isin(kapitel)]
    if aussprache:
        gefiltert = gefiltert[
        gefiltert["aussprache_ohne_ton"]
        .fillna("")  # fehlende Aussprache durch leeren String ersetzen
        .str.lower()
        .str.contains(aussprache.lower(), na=False)  # na=False = treat NaN as False
    ]
        #gefiltert = gefiltert[gefiltert["aussprache_ohne_ton"].str.lower() == aussprache.lower()]
    if grammatik:
        gefiltert = gefiltert[gefiltert["grammatik"].isin(grammatik)]
    if tags_filter:
        gefiltert = gefiltert[gefiltert["alle_tags"].apply(lambda tag_liste: any(tag in tag_liste for tag in tags_filter))]

   
    st.subheader("🔍 Gefilterte Daten")
    st.dataframe(gefiltert)

    st.write(f"Gefundene Wörter: {len(gefiltert)}")

    if not gefiltert.empty:
        if st.button("📄 PDF generieren"):
            pdf_bytes = generate_pdf(gefiltert)
            st.download_button(
                label="📥 PDF herunterladen",
                data=pdf_bytes,
                file_name="uebungsblatt.pdf",
                mime="application/pdf"
            )










