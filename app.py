import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf2 import FPDF

# Folder to store readings and summaries
DATA_DIR = "readings"
os.makedirs(DATA_DIR, exist_ok=True)

# Get current month key like "2025-06"
def get_current_month_key():
    return datetime.today().strftime("%Y-%m")

# File paths
def get_month_file(month_key):
    return os.path.join(DATA_DIR, f"{month_key}.csv")

def get_pdf_file(month_key):
    return os.path.join(DATA_DIR, f"{month_key}-summary.pdf")

# Load data
def load_data(month_key):
    file_path = get_month_file(month_key)
    if os.path.exists(file_path):
        return pd.read_csv(file_path, parse_dates=["date"])
    else:
        return pd.DataFrame(columns=["date", "time", "meter_reading", "difference", "razi", "zaki"])

# Save data
def save_data(df, month_key):
    df.to_csv(get_month_file(month_key), index=False)

# Generate PDF summary
def generate_pdf(df, month_key):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"Electricity Usage Report - {month_key}", ln=True, align="C")

    # Table headers
    pdf.set_font("Arial", "B", 10)
    col_widths = [30, 25, 30, 25, 25, 25]
    headers = ["Date", "Time", "Meter Reading", "Difference", "Razi", "Zaki"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1)
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        values = [
            row["date"],
            row["time"],
            str(row["meter_reading"]),
            str(row["difference"]),
            str(row["razi"]),
            str(row["zaki"]),
        ]
        for i, val in enumerate(values):
            pdf.cell(col_widths[i], 8, str(val), border=1)
        pdf.ln()

    # Summary section
    total_units = df["difference"].sum()
    total_razi = df["razi"].sum()
    total_zaki = df["zaki"].sum()

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Monthly Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(200, 8, f"Total Units Used (Difference): {total_units:.2f}", ln=True)
    pdf.cell(200, 8, f"Total Razi Units: {total_razi:.2f}", ln=True)
    pdf.cell(200, 8, f"Total Zaki Units: {total_zaki:.2f}", ln=True)

    pdf.output(get_pdf_file(month_key))

# Streamlit App
st.title("⚡ Monthly Electricity Unit Tracker")

# Get current month
month_key = get_current_month_key()
st.subheader(f"📅 Current Month: {month_key}")

# Load existing data
df = load_data(month_key)

# === INPUT FORM ===
with st.form("reading_form"):
    date = st.date_input("Date", datetime.today())
    time = st.time_input("Time", datetime.now().time())
    meter_reading = st.number_input("Meter Reading", min_value=0.0, step=0.1)

    # Calculate difference
    previous_reading = df["meter_reading"].iloc[-1] if not df.empty else None
    difference = meter_reading - previous_reading if previous_reading is not None else 0.0

    if previous_reading is not None:
        st.info(f"📉 Previous Reading: {previous_reading}")
        st.success(f"⚙️ Calculated Difference: {difference:.2f}")
    else:
        st.warning("No previous reading found. This will be treated as the starting point.")

    razi = st.number_input("Razi's Usage", min_value=0.0, step=0.1)
    zaki = st.number_input("Zaki's Usage", min_value=0.0, step=0.1)

    submitted = st.form_submit_button("Submit Reading")
    if submitted:
        new_entry = {
            "date": date.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "meter_reading": meter_reading,
            "difference": difference,
            "razi": razi,
            "zaki": zaki
        }
        df = df._append(new_entry, ignore_index=True)
        save_data(df, month_key)
        st.success("Reading saved successfully!")

# === DISPLAY CURRENT DATA ===
if not df.empty:
    st.subheader("📊 This Month's Readings")
    st.dataframe(df)

    st.metric("Total Units Used", f"{df['difference'].sum():.2f} kWh")
    st.bar_chart(df[["razi", "zaki"]])

# === CLOSE MONTH ===
st.markdown("---")
st.subheader("🔐 Close This Month")
if st.button("Close Month"):
    if not df.empty:
        save_data(df, month_key)
        generate_pdf(df, month_key)
        st.success(f"✅ {month_key} closed. PDF report saved.")
        st.info(f"📄 Saved to: `{get_pdf_file(month_key)}`")
    else:
        st.warning("⚠️ No data to close for this month.")
