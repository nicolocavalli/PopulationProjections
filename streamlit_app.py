# --- Streamlit App for Population Projections ---

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Import or define your functions
# Assume simulate_population_fixed and helper functions are imported correctly

# --- Load Base Data ---
@st.cache_data
def load_base_data():
    return pd.read_csv("base_file_new.csv")

base_df = load_base_data()

# --- Sidebar Inputs ---
st.sidebar.header("Immigration Policy Settings")

immigration_boost = st.sidebar.number_input("Additional Immigrants per Year", value=200000, step=50000)
boost_start_year = st.sidebar.number_input("Policy Start Year", value=2026, min_value=2023, max_value=2075)
boost_end_year = st.sidebar.number_input("Policy End Year", value=2035, min_value=2023, max_value=2075)
boost_min_age = st.sidebar.number_input("Minimum Age of Immigrants", value=18, min_value=0, max_value=100)
boost_max_age = st.sidebar.number_input("Maximum Age of Immigrants", value=29, min_value=0, max_value=100)
bring_children = st.sidebar.checkbox("Immigrants Bring Children", value=False)

st.title("Population Projection Simulator")

# --- Run Simulations ---

# Baseline (current migration)
projections_baseline, births_baseline = simulate_population_fixed(base_df, migration_scenario="current")

# Boosted Scenario
projections_boosted, births_boosted = simulate_population_fixed(
    base_df,
    migration_scenario="boosted",
    immigration_boost=immigration_boost,
    boost_start_year=boost_start_year,
    boost_end_year=boost_end_year,
    boost_min_age=boost_min_age,
    boost_max_age=boost_max_age,
    bring_children=bring_children
)

# --- Helper Calculations ---
years = list(range(2023, 2076))

def total_population(projections):
    totals = []
    for year in years:
        total = (
            projections[f"maschi_italiani_{year}"].sum() +
            projections[f"femmine_italiani_{year}"].sum() +
            projections[f"maschi_stranieri_{year}"].sum() +
            projections[f"femmine_stranieri_{year}"].sum()
        )
        totals.append(total)
    return totals

pop_total_baseline = total_population(projections_baseline)
pop_total_boosted = total_population(projections_boosted)

def old_age_dependency(projections):
    oadr = []
    for year in years:
        pop_65plus = projections[(projections["età"] >= 65)][f"maschi_italiani_{year}"].sum() + \
                     projections[(projections["età"] >= 65)][f"femmine_italiani_{year}"].sum() + \
                     projections[(projections["età"] >= 65)][f"maschi_stranieri_{year}"].sum() + \
                     projections[(projections["età"] >= 65)][f"femmine_stranieri_{year}"].sum()
        pop_working = projections[(projections["età"] >= 15) & (projections["età"] <= 64)][f"maschi_italiani_{year}"].sum() + \
                      projections[(projections["età"] >= 15) & (projections["età"] <= 64)][f"femmine_italiani_{year}"].sum() + \
                      projections[(projections["età"] >= 15) & (projections["età"] <= 64)][f"maschi_stranieri_{year}"].sum() + \
                      projections[(projections["età"] >= 15) & (projections["età"] <= 64)][f"femmine_stranieri_{year}"].sum()
        ratio = (pop_65plus / pop_working) * 100 if pop_working > 0 else 0
        oadr.append(ratio)
    return oadr

oadr_baseline = old_age_dependency(projections_baseline)
oadr_boosted = old_age_dependency(projections_boosted)

# --- Plot 1: Total Population ---
st.subheader("Total Population Over Time")
fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(years, pop_total_baseline, label="Baseline", linestyle="--", color="black")
ax1.plot(years, pop_total_boosted, label="Boosted", color="blue", linewidth=2)
ax1.axvspan(boost_start_year, boost_end_year, color="blue", alpha=0.1, label="Boost Period")
ax1.set_xlabel("Year")
ax1.set_ylabel("Total Population")
ax1.legend()
ax1.grid(True)
plt.tight_layout()
st.pyplot(fig1)

# --- Plot 2: Total Births ---
st.subheader("Total Births Over Time")
fig2, ax2 = plt.subplots(figsize=(10, 6))
ax2.plot(births_baseline['year'], births_baseline['total_births'], label="Baseline", linestyle="--", color="black")
ax2.plot(births_boosted['year'], births_boosted['total_births'], label="Boosted", color="blue", linewidth=2)
ax2.axvspan(boost_start_year, boost_end_year, color="blue", alpha=0.1, label="Boost Period")
ax2.set_xlabel("Year")
ax2.set_ylabel("Total Births")
ax2.legend()
ax2.grid(True)
plt.tight_layout()
st.pyplot(fig2)

# --- Plot 3: Population Pyramid (2075) ---
def population_pyramid(df, year):
    male = df[f"maschi_italiani_{year}"] + df[f"maschi_stranieri_{year}"]
    female = df[f"femmine_italiani_{year}"] + df[f"femmine_stranieri_{year}"]
    return male.values, female.values

ages = projections_baseline["età"].values
males_baseline, females_baseline = population_pyramid(projections_baseline, 2075)
males_boosted, females_boosted = population_pyramid(projections_boosted, 2075)

st.subheader("Population Pyramid in 2075")
fig3, ax3 = plt.subplots(figsize=(8, 6))
ax3.barh(ages, -males_baseline, color="lightgray", label="Baseline Males")
ax3.barh(ages, females_baseline, color="gray", label="Baseline Females")
ax3.barh(ages, -males_boosted, color="blue", alpha=0.4, label="Boosted Males")
ax3.barh(ages, females_boosted, color="red", alpha=0.4, label="Boosted Females")
ax3.set_xlabel("Population")
ax3.set_ylabel("Age")
ax3.legend(loc="lower right")
ax3.grid(True)
plt.tight_layout()
st.pyplot(fig3)

# --- Plot 4: Old-Age Dependency Ratio ---
st.subheader("Old-Age Dependency Ratio (OADR) Over Time")
fig4, ax4 = plt.subplots(figsize=(10, 6))
ax4.plot(years, oadr_baseline, label="Baseline", linestyle="--", color="black")
ax4.plot(years, oadr_boosted, label="Boosted", color="blue", linewidth=2)
ax4.set_xlabel("Year")
ax4.set_ylabel("OADR (%)")
ax4.legend()
ax4.grid(True)
plt.tight_layout()
st.pyplot(fig4)

# --- End of App ---


