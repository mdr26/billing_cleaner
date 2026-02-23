import streamlit as st
import pandas as pd
import io

st.title("🏥 Hospital Billing Cleaner Tool")

uploaded_file = st.file_uploader(
    "Upload messy hospital billing Excel file",
    type=["xls", "xlsx"]
)

FINAL_COLUMNS = [
    "Company",
    "Financial Category",
    "Medical No.",
    "Act No.",
    "Case No.",
    "Patients Name",
    "Admission Date",
    "Discharge Date",
    "Length of Stay",
    "Total Price",
    "Total",
    "Comp. Part",
    "Patient",
    "Type"
]

def safe_get(row, index):
    return row.iloc[index] if len(row) > index else None

def is_patient_row(row):
    val = safe_get(row, 0)
    return pd.notna(val) and str(val).isdigit()

def clean_file(file):

    df = pd.read_excel(file, header=None)
    df = df.dropna(how="all").reset_index(drop=True)

    cleaned_rows = []
    current_company = None
    current_category = None

    for idx, row in df.iterrows():

        row_text = " ".join(
            [str(x) for x in row if pd.notna(x)]
        ).strip()

        lower_text = row_text.lower()

        # Skip subtotal rows
        if "sub-total" in lower_text:
            continue

        # Financial Category Block
        if "financial category" in lower_text or "finanial category" in lower_text:

            # Extract category code
            for cell in row:
                if pd.notna(cell):
                    text = str(cell).strip()
                    if (
                        "financial category" not in text.lower()
                        and len(text) <= 15
                    ):
                        current_category = text
                        break

            # Extract company from same row
            # Company text usually appears before "Financial Category"
            split_text = row_text.split("Financial Category")[0].strip()
            if split_text:
                current_company = split_text

            continue

        # Patient rows
        if is_patient_row(row):

            admission = pd.to_datetime(
                safe_get(row, 25), errors="coerce", dayfirst=True
            )

            discharge = pd.to_datetime(
                safe_get(row, 33), errors="coerce", dayfirst=True
            )

            los = None
            if pd.notna(admission) and pd.notna(discharge):
                los = (discharge - admission).days

            new_row = dict.fromkeys(FINAL_COLUMNS, None)

            new_row["Company"] = current_company
            new_row["Financial Category"] = current_category
            new_row["Medical No."] = safe_get(row, 0)
            new_row["Act No."] = safe_get(row, 5)
            new_row["Case No."] = safe_get(row, 10)
            new_row["Patients Name"] = safe_get(row, 14)
            new_row["Admission Date"] = admission
            new_row["Discharge Date"] = discharge
            new_row["Length of Stay"] = los
            new_row["Total Price"] = safe_get(row, 36)
            new_row["Total"] = safe_get(row, 37)
            new_row["Comp. Part"] = safe_get(row, 39)
            new_row["Patient"] = safe_get(row, 41)
            new_row["Type"] = safe_get(row, 42)

            cleaned_rows.append(new_row)

    return pd.DataFrame(cleaned_rows).drop_duplicates()

if uploaded_file:

    cleaned_df = clean_file(uploaded_file)

    st.success("✅ File cleaned successfully!")

    st.dataframe(cleaned_df)

    buffer = io.BytesIO()
    cleaned_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        "📥 Download Cleaned Excel",
        buffer,
        "Cleaned_Billing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
