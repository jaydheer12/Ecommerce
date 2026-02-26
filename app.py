import streamlit as st
import pandas as pd
import io
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

st.set_page_config(page_title="Product Cleaner", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main {background-color:#f4f6f9;}
h1 {color:#1f2937;}
.stButton>button {background:#1f2937;color:white;border-radius:6px;}
.stDownloadButton>button {background:#2563eb;color:white;border-radius:6px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Product Data Cleaning Dashboard")
st.write("Professional E-commerce Data Processing System")

st.sidebar.header("Upload Data")
file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

if file:
    df = pd.read_csv(file)

    missing_before = df.isna().sum().sum()
    duplicates_before = df.duplicated().sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric("Missing Values", missing_before)
    col3.metric("Duplicate Records", duplicates_before)

    with st.expander("View Raw Data"):
        st.dataframe(df, use_container_width=True)

    with st.expander("Rows with Missing Values"):
        st.dataframe(df[df.isna().any(axis=1)], use_container_width=True)

    with st.expander("Duplicate Rows"):
        st.dataframe(df[df.duplicated(keep=False)], use_container_width=True)

    if st.button("Run Data Cleaning"):
        clean = df.copy()

        for col in clean.columns:
            if "name" in col.lower() or "product" in col.lower():
                clean[col] = clean[col].fillna("Unknown").str.strip().str.title()
            elif "price" in col.lower():
                clean[col] = pd.to_numeric(
                    clean[col].astype(str).str.replace(r"[$€£,]", "", regex=True),
                    errors="coerce"
                ).fillna(0)
            elif "category" in col.lower():
                clean[col] = clean[col].fillna("Uncategorized").str.strip().str.title()

        clean = clean.drop_duplicates().fillna(method="ffill")

        missing_after = clean.isna().sum().sum()
        duplicates_after = clean.duplicated().sum()

        st.subheader("📊 Raw vs Cleaned Comparison")
        tab1, tab2 = st.tabs(["Raw Data", "Cleaned Data"])
        with tab1: st.dataframe(df, use_container_width=True)
        with tab2: st.dataframe(clean, use_container_width=True)

        # ---- PDF REPORT ----
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Product Data Cleaning Report", styles["Title"]))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Generated: {datetime.now()}", styles["Normal"]))
        elements.append(Spacer(1, 15))

        stats = [
            ["Metric", "Before", "After"],
            ["Total Records", str(len(df)), str(len(clean))],
            ["Missing Values", str(missing_before), str(missing_after)],
            ["Duplicate Records", str(duplicates_before), str(duplicates_after)]
        ]

        stat_table = Table(stats)
        stat_table.setStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("GRID", (0,0), (-1,-1), 1, colors.black)
        ])
        elements.append(stat_table)
        elements.append(Spacer(1, 20))

        # Full Cleaned Data Table
        data = [clean.columns.tolist()] + clean.astype(str).values.tolist()
        data_table = Table(data, repeatRows=1)
        data_table.setStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTSIZE", (0,0), (-1,-1), 7)
        ])

        elements.append(Paragraph("Cleaned Dataset:", styles["Heading2"]))
        elements.append(Spacer(1, 10))
        elements.append(data_table)

        doc.build(elements)
        buffer.seek(0)

        st.download_button(
            "Download Full PDF Report",
            buffer,
            f"clean_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "application/pdf"
        )

else:
    st.info("Upload a CSV file from the sidebar to begin.")