import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Load Base Data ---
@st.cache_data
def load_base_data():
    return pd.read_csv("base_file_new.csv")

base_df = load_base_data()

# --- Simulation Engine ---
# --- Simulation Engine ---
def simulate_population_fixed(
    base_df,
    migration_scenario="current",
    immigration_boost=0,
    boost_start_year=None,
    boost_end_year=None,
    boost_min_age=18,
    boost_max_age=29,
    bring_children=False
):
    projections = base_df.copy()
    years = list(range(2023, 2076))
    sex_ratio_at_birth = 0.512

    births_per_year = {}

    for year in years[:-1]:
        next_year = year + 1

        total_italiani = (projections[f"maschi_italiani_{year}"] + projections[f"femmine_italiani_{year}"]).sum()
        total_stranieri = (projections[f"maschi_stranieri_{year}"] + projections[f"femmine_stranieri_{year}"]).sum()

        projections["w_maschi_italiani"] = projections[f"maschi_italiani_{year}"] / total_italiani if total_italiani != 0 else 0
        projections["w_femmine_italiani"] = projections[f"femmine_italiani_{year}"] / total_italiani if total_italiani != 0 else 0
        projections["w_maschi_stranieri"] = projections[f"maschi_stranieri_{year}"] / total_stranieri if total_stranieri != 0 else 0
        projections["w_femmine_stranieri"] = projections[f"femmine_stranieri_{year}"] / total_stranieri if total_stranieri != 0 else 0

        if migration_scenario == "current":
            total_outmigration = projections[f"outmigration_{year}"].iloc[0]
            total_immigration = projections[f"immigration_{year}"].iloc[0]
        elif migration_scenario == "no_migration":
            total_outmigration = projections[f"outmigration_{year}"].iloc[0]
            total_immigration = 0
        elif migration_scenario == "boosted":
            total_outmigration = projections[f"outmigration_{year}"].iloc[0]
            total_immigration = projections[f"immigration_{year}"].iloc[0]

        projections[f"maschi_italiani_{year}"] -= total_outmigration * projections["w_maschi_italiani"]
        projections[f"femmine_italiani_{year}"] -= total_outmigration * projections["w_femmine_italiani"]
        projections[f"maschi_stranieri_{year}"] += total_immigration * projections["w_maschi_stranieri"]
        projections[f"femmine_stranieri_{year}"] += total_immigration * projections["w_femmine_stranieri"]
        
        if migration_scenario == "boosted" and immigration_boost > 0:
            if boost_start_year and boost_end_year:
                if boost_start_year <= year <= boost_end_year:
                    male_boost = immigration_boost * 0.5
                    female_boost = immigration_boost * 0.5
                    num_ages_adult = boost_max_age - boost_min_age + 1
                    male_boost_per_age = male_boost / num_ages_adult
                    female_boost_per_age = female_boost / num_ages_adult
                    for age in range(boost_min_age, boost_max_age + 1):
                        projections.loc[projections["età"] == age, f"maschi_stranieri_{year}"] += male_boost_per_age
                        projections.loc[projections["età"] == age, f"femmine_stranieri_{year}"] += female_boost_per_age

            if bring_children:
                total_children = immigration_boost / 2
                male_children = total_children * 0.5
                female_children = total_children * 0.5
                male_children_per_age = male_children / 18
                female_children_per_age = female_children / 18
                for age in range(0, 18):
                    projections.loc[projections["età"] == age, f"maschi_stranieri_{year}"] += male_children_per_age
                    projections.loc[projections["età"] == age, f"femmine_stranieri_{year}"] += female_children_per_age

        for group in ["maschi_italiani", "femmine_italiani", "maschi_stranieri", "femmine_stranieri"]:
            s_col = "survival_maschi" if "maschi" in group else "survival_femmine"
            projections[f"{group}_{year}"] *= projections[s_col]
        
        for group in ["maschi_italiani", "femmine_italiani", "maschi_stranieri", "femmine_stranieri"]:
            projections.loc[projections.index[1:], f"{group}_{next_year}"] = projections.loc[projections.index[:-1], f"{group}_{year}"].values

        if next_year == 2075:
            projections.loc[projections["età"] == 100, f"{group}_{next_year}"] = (
                projections.loc[projections["età"] == 99, f"{group}_{year}"].values[0] * projections[s_col].iloc[99] +
                projections.loc[projections["età"] == 100, f"{group}_{year}"].values[0] * projections[s_col].iloc[100] * projections[s_col].iloc[100]
            )
        else:
            projections.loc[projections["età"] == 100, f"{group}_{next_year}"] += projections.loc[projections["età"] == 100, f"{group}_{year}"].values

        births_italiani = (projections[f"femmine_italiani_{year}"] * (projections["fertility_italiani"] / 1000)).sum()
        births_stranieri = (projections[f"femmine_stranieri_{year}"] * (projections["fertility_stranieri"] / 1000)).sum()

        newborn_males_italiani = int(round(births_italiani * sex_ratio_at_birth))
        newborn_females_italiani = int(round(births_italiani * (1 - sex_ratio_at_birth)))
        newborn_males_stranieri = int(round(births_stranieri * sex_ratio_at_birth))
        newborn_females_stranieri = int(round(births_stranieri * (1 - sex_ratio_at_birth)))

        projections.loc[projections["età"] == 0, f"maschi_italiani_{next_year}"] = newborn_males_italiani
        projections.loc[projections["età"] == 0, f"femmine_italiani_{next_year}"] = newborn_females_italiani
        projections.loc[projections["età"] == 0, f"maschi_stranieri_{next_year}"] = newborn_males_stranieri
        projections.loc[projections["età"] == 0, f"femmine_stranieri_{next_year}"] = newborn_females_stranieri

        births_per_year[year] = births_italiani + births_stranieri
        
        for col in [f"maschi_italiani_{next_year}", f"femmine_italiani_{next_year}",
                    f"maschi_stranieri_{next_year}", f"femmine_stranieri_{next_year}"]:
            projections[col] = projections[col].round().astype(int)

    births_df = pd.DataFrame(list(births_per_year.items()), columns=["year", "total_births"])

    return projections, births_df

# --- Helper Functions ---
def total_population(projections):
    years = list(range(2023, 2076))
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

def old_age_dependency(projections):
    years = list(range(2023, 2076))
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

def population_pyramid(df, year):
    male = df[f"maschi_italiani_{year}"] + df[f"maschi_stranieri_{year}"]
    female = df[f"femmine_italiani_{year}"] + df[f"femmine_stranieri_{year}"]
    return male.values, female.values

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

pop_total_baseline = total_population(projections_baseline)
pop_total_boosted = total_population(projections_boosted)

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

# --- Plot 3: Population Pyramid in 2075 ---
st.subheader("Population Pyramid in 2075")
ages = projections_baseline["età"].values
males_baseline, females_baseline = population_pyramid(projections_baseline, 2075)
males_boosted, females_boosted = population_pyramid(projections_boosted, 2075)

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

# --- Plot 4: Old-Age Dependency Ratio (OADR) Over Time ---
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

# --- End of Streamlit App ---

# (Nothing else is needed — Streamlit automatically manages session state.)

