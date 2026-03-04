import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter


# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="Product Cleaner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Product Data Cleaning Dashboard")
st.markdown("---")

st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV File",
    type=["csv"]
)


# -------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------

def calculate_basic_stats(df):
    return (
        len(df),
        len(df.columns),
        df.isna().sum().sum(),
        df.duplicated().sum()
    )


def clean_product_name(series):
    return series.fillna("Unknown").astype(str).str.strip().str.title()


def clean_price_column(series):
    return (
        pd.to_numeric(
            series.astype(str).str.replace(r"[$€£,]", "", regex=True),
            errors="coerce"
        ).fillna(0)
    )


def clean_category_column(series):
    return series.fillna("Uncategorized").astype(str).str.strip().str.title()


def clean_dataframe(df):
    cleaned = df.copy()

    for col in cleaned.columns:
        if "name" in col.lower():
            cleaned[col] = clean_product_name(cleaned[col])

        elif "price" in col.lower():
            cleaned[col] = clean_price_column(cleaned[col])

        elif "category" in col.lower():
            cleaned[col] = clean_category_column(cleaned[col])

    cleaned = cleaned.drop_duplicates()
    cleaned = cleaned.fillna(method="ffill")

    return cleaned


def predict_missing_prices(df):
    predicted_df = df.copy()

    price_col = None
    for col in predicted_df.columns:
        if "price" in col.lower():
            price_col = col
            break

    if price_col:
        avg_price = predicted_df[predicted_df[price_col] > 0][price_col].mean()

        predicted_df["Predicted_Price"] = predicted_df[price_col]

        predicted_df.loc[
            predicted_df[price_col] == 0,
            "Predicted_Price"
        ] = round(avg_price, 2)

    return predicted_df


def build_pdf_report(clean_df, predicted_df, before_stats, after_stats):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Product Data Cleaning Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    summary_data = [
        ["Metric", "Before Cleaning", "After Cleaning"],
        ["Total Records", before_stats[0], after_stats[0]],
        ["Missing Values", before_stats[2], after_stats[2]],
        ["Duplicate Records", before_stats[3], after_stats[3]]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(summary_table)
    elements.append(PageBreak())

    elements.append(Paragraph("Cleaned Dataset", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    clean_table = [clean_df.columns.tolist()] + clean_df.astype(str).values.tolist()
    elements.append(Table(clean_table, repeatRows=1))
    elements.append(PageBreak())

    elements.append(Paragraph("Predicted Dataset", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    pred_table = [predicted_df.columns.tolist()] + predicted_df.astype(str).values.tolist()
    elements.append(Table(pred_table, repeatRows=1))

    doc.build(elements)
    buffer.seek(0)

    return buffer


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if uploaded_file:

    df = pd.read_csv(uploaded_file)
    before_stats = calculate_basic_stats(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", before_stats[0])
    col2.metric("Total Columns", before_stats[1])
    col3.metric("Missing Values", before_stats[2])
    col4.metric("Duplicate Records", before_stats[3])

    st.markdown("---")

    # ✅ CLICK TO VIEW RAW DATA
    with st.expander("🔍 Click to View Raw Data"):
        st.dataframe(df, use_container_width=True)

    # ✅ CLICK TO VIEW MISSING ROWS
    with st.expander("⚠ Click to View Rows with Missing Values"):
        missing_rows = df[df.isna().any(axis=1)]
        st.dataframe(missing_rows, use_container_width=True)

    # ✅ CLICK TO VIEW DUPLICATES
    with st.expander("🔁 Click to View Duplicate Rows"):
        duplicate_rows = df[df.duplicated(keep=False)]
        st.dataframe(duplicate_rows, use_container_width=True)

    st.markdown("---")

    if st.button("🚀 Run Data Cleaning"):

        cleaned_df = clean_dataframe(df)
        predicted_df = predict_missing_prices(cleaned_df)
        after_stats = calculate_basic_stats(cleaned_df)

        tab1, tab2, tab3 = st.tabs(
            ["Raw Data", "Cleaned Data", "Predicted Prices"]
        )

        with tab1:
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.dataframe(cleaned_df, use_container_width=True)

        with tab3:
            st.dataframe(predicted_df, use_container_width=True)

            st.subheader("Rows Where Original Price Was Zero")

            price_column = None
            for col in predicted_df.columns:
                if "price" in col.lower() and col != "Predicted_Price":
                    price_column = col
                    break

            if price_column:
                zero_rows = predicted_df[predicted_df[price_column] == 0]
                st.dataframe(zero_rows, use_container_width=True)

        pdf_buffer = build_pdf_report(
            cleaned_df,
            predicted_df,
            before_stats,
            after_stats
        )

        st.download_button(
            "📄 Download Full PDF Report",
            pdf_buffer,
            "clean_report.pdf",
            "application/pdf"
        )

else:
    st.info("Upload a CSV file from the sidebar to begin.")
