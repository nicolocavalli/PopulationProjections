import streamlit as st
import pandas as pd
import numpy as np

def simulate_population_fixed(
    base_df,
    immigration_boost=0,
    boost_start_year=None,
    boost_end_year=None,
    boost_min_age=18,
    boost_max_age=29,
):
    projections_baseline = base_df.copy()
    projections_boosted = base_df.copy()

    start_year = 2023
    end_year = 2075
    years = list(range(start_year, end_year + 1))

    sex_ratio_at_birth = 0.512

    # Initialize storage
    for df in [projections_baseline, projections_boosted]:
        for year in years[1:]:
            for group in ["maschi_italiani", "femmine_italiani", "maschi_stranieri", "femmine_stranieri"]:
                df[f"{group}_{year}"] = 0

    # Simulate year by year
    for year in years[:-1]:
        next_year = year + 1

        for df, scenario in [(projections_baseline, "baseline"), (projections_boosted, "boosted")]:
            
            # 1. Outmigration (Italians only)
            total_outmigration = df[f"outmigration_{year}"].iloc[0]
            total_italiani = (df[f"maschi_italiani_{year}"] + df[f"femmine_italiani_{year}"]).sum()

            if total_italiani > 0:
                df["w_maschi_italiani"] = df[f"maschi_italiani_{year}"] / total_italiani
                df["w_femmine_italiani"] = df[f"femmine_italiani_{year}"] / total_italiani
            else:
                df["w_maschi_italiani"] = 0
                df["w_femmine_italiani"] = 0

            df[f"maschi_italiani_{year}"] -= total_outmigration * df["w_maschi_italiani"]
            df[f"femmine_italiani_{year}"] -= total_outmigration * df["w_femmine_italiani"]

            # 2. Regular Immigration (foreigners only)
            total_immigration = df[f"immigration_{year}"].iloc[0]
            total_stranieri = (df[f"maschi_stranieri_{year}"] + df[f"femmine_stranieri_{year}"]).sum()

            if total_stranieri > 0:
                df["w_maschi_stranieri"] = df[f"maschi_stranieri_{year}"] / total_stranieri
                df["w_femmine_stranieri"] = df[f"femmine_stranieri_{year}"] / total_stranieri
            else:
                df["w_maschi_stranieri"] = 0
                df["w_femmine_stranieri"] = 0

            df[f"maschi_stranieri_{year}"] += total_immigration * df["w_maschi_stranieri"]
            df[f"femmine_stranieri_{year}"] += total_immigration * df["w_femmine_stranieri"]

            # 3. Apply Survival (existing population)
            for group, survival in zip(["maschi_italiani", "femmine_italiani", "maschi_stranieri", "femmine_stranieri"],
                                       ["survival_maschi", "survival_femmine", "survival_maschi", "survival_femmine"]):
                df[f"{group}_{year}"] *= df[survival]

            # 4. Apply Boost (only after survival)
            if scenario == "boosted" and boost_start_year and boost_end_year:
                if boost_start_year <= year <= boost_end_year:
                    male_boost = immigration_boost * 0.5
                    female_boost = immigration_boost * 0.5
                    num_ages = boost_max_age - boost_min_age + 1
                    male_boost_per_age = male_boost / num_ages
                    female_boost_per_age = female_boost / num_ages

                    for age in range(boost_min_age, boost_max_age + 1):
                        df.loc[df["età"] == age, f"maschi_stranieri_{year}"] += male_boost_per_age
                        df.loc[df["età"] == age, f"femmine_stranieri_{year}"] += female_boost_per_age

            # 5. Aging: Shift everyone
            for group in ["maschi_italiani", "femmine_italiani", "maschi_stranieri", "femmine_stranieri"]:
                df.loc[df.index[1:], f"{group}_{next_year}"] = df.loc[df.index[:-1], f"{group}_{year}"].values
                df.loc[df["età"] == 100, f"{group}_{next_year}"] += df.loc[df["età"] == 100, f"{group}_{year}"].values

            # 6. Births
            births_italiani = (df[f"femmine_italiani_{year}"] * (df["fertility_italiani"] / 1000)).sum()
            births_stranieri = (df[f"femmine_stranieri_{year}"] * (df["fertility_stranieri"] / 1000)).sum()

            newborn_males_italiani = int(round(births_italiani * sex_ratio_at_birth))
            newborn_females_italiani = int(round(births_italiani * (1 - sex_ratio_at_birth)))
            newborn_males_stranieri = int(round(births_stranieri * sex_ratio_at_birth))
            newborn_females_stranieri = int(round(births_stranieri * (1 - sex_ratio_at_birth)))

            df.loc[df["età"] == 0, f"maschi_italiani_{next_year}"] = newborn_males_italiani
            df.loc[df["età"] == 0, f"femmine_italiani_{next_year}"] = newborn_females_italiani
            df.loc[df["età"] == 0, f"maschi_stranieri_{next_year}"] = newborn_males_stranieri
            df.loc[df["età"] == 0, f"femmine_stranieri_{next_year}"] = newborn_females_stranieri

    return projections_baseline, projections_boosted

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

