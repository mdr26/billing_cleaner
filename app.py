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


def is_patient_row(row):
    return pd.notna(row.iloc[0]) and str(row.iloc[0]).isdigit()


def clean_file(file):

    df = pd.read_excel(file, header=None)
    df = df.dropna(how="all").reset_index(drop=True)

    cleaned_rows = []
    current_company = None
    current_category = None

    for idx, row in df.iterrows():

        row_text = " ".join(
            [str(x) for x in row if pd.notna(x)]
        ).lower()

        # Skip subtotal rows immediately
        if "sub-total" in row_text:
            continue

        # Detect financial category block
        if "financial category" in row_text or "finanial category" in row_text:

            # Find company safely above category
            for j in range(idx-1, max(idx-6, -1), -1):

                prev_row = df.iloc[j]
                prev_text = " ".join(
                    [str(x) for x in prev_row if pd.notna(x)]
                ).strip()

                lower_text = prev_text.lower()

                if (
                    prev_text
                    and "sub-total" not in lower_text
                    and not is_patient_row(prev_row)
                    and not any(x in lower_text for x in [
                        "medical no",
                        "act.no",
                        "patients name",
                        "admission date",
                        "case no"
                    ])
                ):
                    current_company = prev_text
                    break

            # Extract financial category code
            for cell in row:
                if pd.notna(cell):
                    text = str(cell).strip()
                    if (
                        "financial category" not in text.lower()
                        and len(text) <= 15
                    ):
                        current_category = text
                        break

            continue

        # Patient rows
        if is_patient_row(row):

            admission = pd.to_datetime(
                row.iloc[25], errors="coerce", dayfirst=True
            )

            discharge = pd.to_datetime(
                row.iloc[33], errors="coerce", dayfirst=True
            )

            los = None
            if pd.notna(admission) and pd.notna(discharge):
                los = (discharge - admission).days

            new_row = dict.fromkeys(FINAL_COLUMNS, None)

            new_row["Company"] = current_company
            new_row["Financial Category"] = current_category
            new_row["Medical No."] = row.iloc[0]
            new_row["Act No."] = row.iloc[5]
            new_row["Case No."] = row.iloc[10]
            new_row["Patients Name"] = row.iloc[14]
            new_row["Admission Date"] = admission
            new_row["Discharge Date"] = discharge
            new_row["Length of Stay"] = los
            new_row["Total Price"] = row.iloc[36]
            new_row["Total"] = row.iloc[37]
            new_row["Comp. Part"] = row.iloc[39]
            new_row["Patient"] = row.iloc[41]
            new_row["Type"] = row.iloc[42]

            cleaned_rows.append(new_row)

    clean_df = pd.DataFrame(cleaned_rows).drop_duplicates()

    return clean_df


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
