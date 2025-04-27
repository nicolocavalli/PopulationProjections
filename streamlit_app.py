import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- UI Sidebar ---
st.sidebar.title("Immigration Boost Policy Settings")

boost_start = st.sidebar.number_input("Boost Start Year", min_value=2026, max_value=2070, value=2026, step=1)
boost_end = st.sidebar.number_input("Boost End Year", min_value=2026, max_value=2075, value=2035, step=1)
boost_amount = st.sidebar.number_input("Annual Immigration Boost", min_value=0, value=200000, step=10000)
boost_age_min = st.sidebar.number_input("Minimum Age of Boosted Immigrants", min_value=18, max_value=49, value=18, step=1)
boost_age_max = st.sidebar.number_input("Maximum Age of Boosted Immigrants", min_value=18, max_value=49, value=29, step=1)
bring_children = st.sidebar.checkbox("Immigrants Arrive with Children (50%)", value=False)

# --- Load Data ---
@st.cache_data
def load_data():
    boost_df = pd.read_csv("projections_baseline.csv") 
    no_imm_df = pd.read_csv("projections_no_immigration.csv") 
    return boost_df, no_imm_df

boost_df, no_immigration_df = load_data()

# --- Projection Engine ---
def simulate_boost_population(boost_start, boost_end, boost_amount, base_df):
    projections = base_df.copy()
    years = list(range(2025, 2076))
    sex_ratio_at_birth = 0.512

    # Initialize boost columns to 0
    for year in years:
        for group in ["maschi_stranieri", "femmine_stranieri"]:
            projections[f"{group}_boost_{year}"] = 0

    for year in years[:-1]:
        next_year = year + 1

        if boost_start <= year <= boost_end:
            eligible = projections[
                (projections["età"] >= boost_age_min) & 
                (projections["età"] <= boost_age_max)
            ]
            total_cells = len(eligible)

            if total_cells > 0:
                per_cell_boost = boost_amount / total_cells
                mask = (projections["età"] >= boost_age_min) & (projections["età"] <= boost_age_max)
                projections.loc[mask, f"maschi_stranieri_boost_{year}"] += per_cell_boost / 2
                projections.loc[mask, f"femmine_stranieri_boost_{year}"] += per_cell_boost / 2

            if bring_children:
                child_cells = projections[(projections["età"] >= 0) & (projections["età"] <= 17)]
                total_child_cells = len(child_cells)
                if total_child_cells > 0:
                    per_child_boost = (boost_amount / 2) / total_child_cells
                    mask_child = (projections["età"] >= 0) & (projections["età"] <= 17)
                    projections.loc[mask_child, f"maschi_stranieri_boost_{year}"] += per_child_boost / 2
                    projections.loc[mask_child, f"femmine_stranieri_boost_{year}"] += per_child_boost / 2

        # Survival
        for group in ["maschi_stranieri", "femmine_stranieri"]:
            s_col = "survival_maschi" if "maschi" in group else "survival_femmine"
            projections[f"{group}_boost_{next_year}"] = projections[f"{group}_boost_{year}"] * projections[s_col]

        # Aging
        for group in ["maschi_stranieri", "femmine_stranieri"]:
            s_col = "survival_maschi" if "maschi" in group else "survival_femmine"
            projections.loc[projections.index[1:], f"{group}_boost_{next_year}"] = (
                projections.loc[projections.index[:-1], f"{group}_boost_{next_year}"].values
            )
            projections.loc[projections["età"] == 100, f"{group}_boost_{next_year}"] = (
                projections.loc[projections["età"] == 99, f"{group}_boost_{year}"].values[0] * projections[s_col].iloc[99] +
                projections.loc[projections["età"] == 100, f"{group}_boost_{year}"].values[0] * projections[s_col].iloc[100]
            )

        # Fertility
        fert_col = "fertility_stranieri"
        births_boost = (projections[f"femmine_stranieri_boost_{year}"] * projections[fert_col]).sum() / 1000
        projections.loc[0, f"births_boost_{year}"] = births_boost
        projections.loc[projections["età"] == 0, f"maschi_stranieri_boost_{next_year}"] += births_boost * sex_ratio_at_birth
        projections.loc[projections["età"] == 0, f"femmine_stranieri_boost_{next_year}"] += births_boost * (1 - sex_ratio_at_birth)

    return projections

# --- Totals Calculation ---
def total_population(df):
    years = list(range(2025, 2076))
    return [
        (df[f"maschi_italiani_{y}"] + df[f"femmine_italiani_{y}"] +
         df[f"maschi_stranieri_{y}"] + df[f"femmine_stranieri_{y}"]).sum()
        for y in years
    ]

def total_foreign_population(df):
    years = list(range(2025, 2076))
    return [
        (df[f"maschi_stranieri_{y}"] + df[f"femmine_stranieri_{y}"]).sum()
        for y in years
    ]

# --- Run Projection ---
years = list(range(2025, 2076))
pop_baseline = total_population(boost_df)
pop_no_immigration = total_population(no_immigration_df)

boost_projection = simulate_boost_population(boost_start, boost_end, boost_amount, boost_df)
pop_boost = total_foreign_population(boost_projection)
pop_boosted = [b + p for b, p in zip(pop_baseline, pop_boost)]

# --- Plot: Total Births Over Time ---
#st.subheader("Total Births Per Year: Baseline vs Boosted Scenario")

#birth_years = list(range(2025, 2075))
#births_baseline = [
 #   boost_df[f"births_italiani_{y}"].sum() + boost_df[f"births_stranieri_{y}"].sum()
  #  for y in birth_years
#]
#births_boosted = [
#    boost_df[f"births_italiani_{y}"].sum() + 
 #   boost_df[f"births_stranieri_{y}"].sum() + 
  #  boost_projection.get(f"births_boost_{y}", pd.Series([0])).sum()
   # for y in birth_years
#]

#fig3, ax3 = plt.subplots(figsize=(10, 5))
#ax3.plot(birth_years, births_baseline, label="Baseline", linestyle="--", color="black")
#ax3.plot(birth_years, births_boosted, label="With Immigration Boost", color="blue", linewidth=2)
#ax3.axvspan(boost_start, boost_end, color="blue", alpha=0.1, label="Boost Period")
#ax3.set_xlabel("Year")
#ax3.set_ylabel("Total Births")
#ax3.set_title("Total Annual Births: Baseline vs Boosted Scenario")
#ax3.legend()
#ax3.grid(True)
#st.pyplot(fig3)

# --- Plot: Total Population Over Time ---
st.subheader("Total Population Over Time")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(years, pop_no_immigration, label="No Immigration", linestyle="--", color="gray")
ax.plot(years, pop_baseline, label="Baseline (Current Forecast)", linestyle="--", color="black")
ax.plot(years, pop_boosted, label="With Immigration Boost", color="blue", linewidth=2)
ax.axvspan(boost_start, boost_end, color="blue", alpha=0.1, label="Boost Period")
ax.set_xlabel("Year")
ax.set_ylabel("Total Population")
ax.set_title("Total Population: No Immigration vs Baseline vs Boost")
ax.legend()
ax.grid(True)
st.pyplot(fig)

