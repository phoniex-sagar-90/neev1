import streamlit as st
import pandas as pd

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Metabolic Risk Analyzer",
    page_icon="🩺",
    layout="wide"
)

# =========================================================
# DATA PATH
# =========================================================

DATA_PATH = "data/diabetes_risk_prediction_dataset-selected-columns.csv"


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)

    # Convert required numeric columns
    numeric_columns = [
        "Age",
        "Height_cm",
        "Weight_kg",
        "BMI",
        "Waist_Circumference_cm",
        "Blood_Glucose",
        "HbA1c"
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    # Height and weight are required to calculate
    # BMI for population analysis.
    data = data.dropna(
        subset=["Height_cm", "Weight_kg"]
    ).copy()

    # Calculate BMI from height and weight.
    height_m = data["Height_cm"] / 100

    data["BMI_Calculated"] = (
        data["Weight_kg"] / (height_m ** 2)
    )

    return data


# =========================================================
# LOAD DATA SAFELY
# =========================================================

try:
    df = load_data()

except FileNotFoundError:
    st.error(
        "Dataset file was not found. Make sure the CSV is inside "
        "the 'data' folder."
    )
    st.stop()

except Exception as error:
    st.error(
        f"An error occurred while loading the dataset: {error}"
    )
    st.stop()


# =========================================================
# BMI CATEGORY
# =========================================================

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obesity"


# =========================================================
# RISK CALCULATION
# =========================================================

def calculate_risk(bmi, glucose=None, hba1c=None):

    # High Risk:
    # HbA1c >= 6.5
    # OR Blood Glucose >= 140
    # OR BMI >= 30

    if (
        bmi >= 30
        or (
            glucose is not None
            and glucose >= 140
        )
        or (
            hba1c is not None
            and hba1c >= 6.5
        )
    ):
        return "High Risk"

    # Moderate Risk:
    # HbA1c >= 5.7
    # OR Blood Glucose >= 100
    # OR BMI >= 25

    elif (
        bmi >= 25
        or (
            glucose is not None
            and glucose >= 100
        )
        or (
            hba1c is not None
            and hba1c >= 5.7
        )
    ):
        return "Moderate Risk"

    # Otherwise Low Risk
    else:
        return "Low Risk"


# =========================================================
# CALCULATE RISK FOR EVERY DATASET RECORD
# =========================================================

df["Risk_Tier"] = df.apply(
    lambda row: calculate_risk(
        bmi=row["BMI_Calculated"],
        glucose=(
            row["Blood_Glucose"]
            if pd.notna(row["Blood_Glucose"])
            else None
        ),
        hba1c=(
            row["HbA1c"]
            if pd.notna(row["HbA1c"])
            else None
        )
    ),
    axis=1
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🩺 Metabolic Risk Analyzer")

page = st.sidebar.radio(
    "Select Section",
    [
        "🏠 Population Dashboard",
        "🧮 Personal Assessment"
    ]
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Hackathon Project - Problem Statement 3"
)


# =========================================================
# POPULATION DASHBOARD
# =========================================================

if page == "🏠 Population Dashboard":

    st.title("🩺 Metabolic Risk Analyzer")

    st.write(
        "Interactive analysis of metabolic risk across "
        "the population dataset."
    )

    # -----------------------------------------------------
    # KPI CALCULATIONS
    # -----------------------------------------------------

    total_records = len(df)

    high_risk_count = (
        df["Risk_Tier"] == "High Risk"
    ).sum()

    moderate_risk_count = (
        df["Risk_Tier"] == "Moderate Risk"
    ).sum()

    low_risk_count = (
        df["Risk_Tier"] == "Low Risk"
    ).sum()

    # -----------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Records",
            f"{total_records:,}"
        )

    with col2:
        st.metric(
            "🔴 High Risk",
            f"{high_risk_count:,}"
        )

    with col3:
        st.metric(
            "🟡 Moderate Risk",
            f"{moderate_risk_count:,}"
        )

    with col4:
        st.metric(
            "🟢 Low Risk",
            f"{low_risk_count:,}"
        )

    st.markdown("---")

    # -----------------------------------------------------
    # RISK DISTRIBUTION
    # -----------------------------------------------------

    st.subheader("📊 Risk Tier Distribution")

    risk_distribution = (
        df["Risk_Tier"]
        .value_counts()
        .reindex(
            [
                "Low Risk",
                "Moderate Risk",
                "High Risk"
            ],
            fill_value=0
        )
    )

    st.bar_chart(
        risk_distribution
    )

    # -----------------------------------------------------
    # RISK PERCENTAGE
    # -----------------------------------------------------

    st.subheader("Risk Tier Percentage")

    risk_percentage = (
        risk_distribution / total_records * 100
    ).round(2)

    st.dataframe(
        risk_percentage.rename("Percentage (%)"),
        use_container_width=True
    )

    # -----------------------------------------------------
    # AVERAGE AGE BY RISK
    # -----------------------------------------------------

    st.subheader("👥 Average Age by Risk Tier")

    average_age = (
        df.groupby("Risk_Tier")["Age"]
        .mean()
        .reindex(
            [
                "Low Risk",
                "Moderate Risk",
                "High Risk"
            ]
        )
    )

    st.bar_chart(
        average_age
    )

    # -----------------------------------------------------
    # BMI AND GLUCOSE
    # -----------------------------------------------------

    left_chart, right_chart = st.columns(2)

    with left_chart:

        st.subheader("⚖️ BMI Distribution")

        bmi_distribution = (
            df["BMI_Calculated"]
            .dropna()
            .round(1)
            .value_counts()
            .sort_index()
        )

        st.line_chart(
            bmi_distribution
        )

    with right_chart:

        st.subheader("🩸 Blood Glucose Distribution")

        glucose_distribution = (
            df["Blood_Glucose"]
            .dropna()
            .round(0)
            .value_counts()
            .sort_index()
        )

        st.line_chart(
            glucose_distribution
        )

    # -----------------------------------------------------
    # DATASET PREVIEW
    # -----------------------------------------------------

    st.subheader("📋 Processed Dataset Preview")

    display_columns = [
        "Patient_ID",
        "Age",
        "Gender",
        "Country",
        "Height_cm",
        "Weight_kg",
        "BMI_Calculated",
        "Waist_Circumference_cm",
        "Blood_Glucose",
        "HbA1c",
        "Risk_Tier"
    ]

    st.dataframe(
        df[display_columns].head(20),
        use_container_width=True
    )


# =========================================================
# PERSONAL ASSESSMENT
# =========================================================

else:

    st.title("🧮 Personal Risk Assessment")

    st.write(
        "Enter your personal information. The application "
        "will calculate your BMI automatically from height "
        "and weight."
    )

    # -----------------------------------------------------
    # USER INPUTS
    # -----------------------------------------------------

    left, right = st.columns(2)

    with left:

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=25,
            step=1
        )

        gender = st.selectbox(
            "Gender",
            [
                "Male",
                "Female",
                "Other"
            ]
        )

        height = st.number_input(
            "Height (cm)",
            min_value=50.0,
            max_value=250.0,
            value=170.0,
            step=0.1
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=10.0,
            max_value=300.0,
            value=65.0,
            step=0.1
        )

    with right:

        waist = st.number_input(
            "Waist Circumference (cm)",
            min_value=30.0,
            max_value=200.0,
            value=80.0,
            step=0.1
        )

        glucose_input = st.number_input(
            "Blood Glucose (optional)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=0.1,
            help="Enter 0 if the value is not available."
        )

        hba1c_input = st.number_input(
            "HbA1c (optional)",
            min_value=0.0,
            max_value=20.0,
            value=0.0,
            step=0.1,
            help="Enter 0 if the value is not available."
        )

    st.markdown("---")

    # -----------------------------------------------------
    # CALCULATE INDIVIDUAL BMI
    # -----------------------------------------------------

    height_m = height / 100

    bmi = weight / (height_m ** 2)

    # -----------------------------------------------------
    # BMI CATEGORY
    # -----------------------------------------------------

    bmi_category = get_bmi_category(bmi)

    # -----------------------------------------------------
    # OPTIONAL VALUES
    # -----------------------------------------------------

    glucose = (
        None
        if glucose_input == 0
        else glucose_input
    )

    hba1c = (
        None
        if hba1c_input == 0
        else hba1c_input
    )

    # -----------------------------------------------------
    # CALCULATE PERSONAL RISK
    # -----------------------------------------------------

    individual_risk = calculate_risk(
        bmi=bmi,
        glucose=glucose,
        hba1c=hba1c
    )

    # -----------------------------------------------------
    # BMI PERCENTILE
    # -----------------------------------------------------

    bmi_percentile = (
        df["BMI_Calculated"] < bmi
    ).mean() * 100

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------

    st.subheader("📋 Your Results")

    result1, result2, result3 = st.columns(3)

    with result1:

        st.metric(
            "BMI Index",
            f"{bmi:.1f}"
        )

    with result2:

        st.metric(
            "BMI Category",
            bmi_category
        )

    with result3:

        st.metric(
            "Risk Tier",
            individual_risk
        )

    st.markdown("---")

    # -----------------------------------------------------
    # BMI ANALYSIS
    # -----------------------------------------------------

    st.subheader("⚖️ Individual BMI Analysis")

    st.write(
        f"**Height:** {height:.1f} cm"
    )

    st.write(
        f"**Weight:** {weight:.1f} kg"
    )

    st.write(
        f"**Calculated BMI:** {bmi:.1f}"
    )

    st.write(
        f"**BMI Category:** {bmi_category}"
    )

    # -----------------------------------------------------
    # PERCENTILE
    # -----------------------------------------------------

    st.info(
        f"Your BMI is higher than approximately "
        f"**{bmi_percentile:.1f}%** of the population "
        f"in this dataset."
    )

    # -----------------------------------------------------
    # RISK EXPLANATION
    # -----------------------------------------------------

    st.subheader("🔎 Risk Assessment")

    if individual_risk == "High Risk":

        st.error(
            "Your calculated risk tier is **High Risk** "
            "according to the hackathon's specified rules."
        )

    elif individual_risk == "Moderate Risk":

        st.warning(
            "Your calculated risk tier is **Moderate Risk** "
            "according to the hackathon's specified rules."
        )

    else:

        st.success(
            "Your calculated risk tier is **Low Risk** "
            "according to the hackathon's specified rules."
        )

    # -----------------------------------------------------
    # ENTERED INFORMATION
    # -----------------------------------------------------

    with st.expander("View Entered Information"):

        st.write(
            f"**Age:** {age}"
        )

        st.write(
            f"**Gender:** {gender}"
        )

        st.write(
            f"**Height:** {height:.1f} cm"
        )

        st.write(
            f"**Weight:** {weight:.1f} kg"
        )

        st.write(
            f"**BMI:** {bmi:.1f}"
        )

        st.write(
            f"**Waist Circumference:** "
            f"{waist:.1f} cm"
        )

        if glucose is None:

            st.write(
                "**Blood Glucose:** Not provided"
            )

        else:

            st.write(
                f"**Blood Glucose:** {glucose:.1f}"
            )

        if hba1c is None:

            st.write(
                "**HbA1c:** Not provided"
            )

        else:

            st.write(
                f"**HbA1c:** {hba1c:.1f}"
            )

    # -----------------------------------------------------
    # LIFESTYLE SUGGESTIONS
    # -----------------------------------------------------

    st.subheader("💡 General Lifestyle Suggestions")

    if individual_risk == "High Risk":

        st.write(
            "• Consider discussing these results with "
            "a qualified healthcare professional."
        )

        st.write(
            "• Maintain regular physical activity and "
            "balanced eating habits."
        )

        st.write(
            "• Consider monitoring your health measurements "
            "over time."
        )

    elif individual_risk == "Moderate Risk":

        st.write(
            "• Aim for consistent physical activity "
            "throughout the week."
        )

        st.write(
            "• Choose balanced meals containing vegetables, "
            "whole grains, and protein."
        )

        st.write(
            "• Keep track of relevant health measurements "
            "over time."
        )

    else:

        st.write(
            "• Continue regular physical activity."
        )

        st.write(
            "• Maintain balanced eating habits."
        )

        st.write(
            "• Continue monitoring your general health."
        )

    # -----------------------------------------------------
    # DISCLAIMER
    # -----------------------------------------------------

    st.markdown("---")

    st.caption(
        "Educational hackathon tool only. "
        "This application provides a dataset-based estimate "
        "and is not a medical diagnosis."
    )
    