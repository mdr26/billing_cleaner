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
    "Category Description",
    "Medical No.",
    "Act No.",
    "Case No.",
    "Patients Name",
    "Admission Date",
    "Discharge Date",
    "Total Price",
    "Total",
    "Comp. Part",
    "Patient",
    "Type"
]


def clean_file(file):

    df = pd.read_excel(file, header=None)
    df = df.dropna(how="all").reset_index(drop=True)

    cleaned_rows = []
    current_company = None
    current_category = None
    current_category_desc = None

    for idx, row in df.iterrows():

        row_text = " ".join(
            [str(x) for x in row if pd.notna(x)]
        ).lower()

        # Detect company / insurance
        if "insurance" in row_text or "hospital" in row_text:
            current_company = " ".join(
                [str(x) for x in row if pd.notna(x)]
            )
            continue

        # Detect financial category block
        if "financial category" in row_text or "finanial category" in row_text:

            category_code = None
            category_desc = None

            # Extract category code from same row
            for cell in row:
                if pd.notna(cell):
                    text = str(cell).strip()
                    if (
                        "financial category" not in text.lower()
                        and len(text) <= 15
                    ):
                        category_code = text
                        break

            # Extract description safely (skip header rows)
            for i in range(idx+1, min(idx+4, len(df))):
                next_row = df.iloc[i]

                next_text = " ".join(
                    [str(x) for x in next_row if pd.notna(x)]
                ).lower()

                # Skip table headers
                if any(x in next_text for x in [
                    "medical no",
                    "patients name",
                    "admission date",
                    "act.no",
                    "case no"
                ]):
                    continue

                desc_cells = [
                    str(x).strip()
                    for x in next_row
                    if pd.notna(x)
                ]

                if desc_cells:
                    category_desc = " ".join(desc_cells)
                    break

            current_category = category_code
            current_category_desc = category_desc

            continue

        # Skip subtotal rows
        if "sub-total" in row_text:
            continue

        # Detect patient data rows
        medical_no = row.iloc[0]

        if pd.notna(medical_no) and str(medical_no).isdigit():

            new_row = dict.fromkeys(FINAL_COLUMNS, None)

            new_row["Company"] = current_company
            new_row["Financial Category"] = current_category
            new_row["Category Description"] = current_category_desc

            new_row["Medical No."] = row.iloc[0]
            new_row["Act No."] = row.iloc[5]
            new_row["Case No."] = row.iloc[10]
            new_row["Patients Name"] = row.iloc[14]

            new_row["Admission Date"] = pd.to_datetime(
                row.iloc[25], errors="coerce", dayfirst=True
            )

            new_row["Discharge Date"] = pd.to_datetime(
                row.iloc[33], errors="coerce", dayfirst=True
            )

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

    # Proper Excel download
    buffer = io.BytesIO()
    cleaned_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        "📥 Download Cleaned Excel",
        buffer,
        "Cleaned_Billing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
