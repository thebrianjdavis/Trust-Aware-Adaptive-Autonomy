import pandas as pd

df = pd.read_csv("data/raw/us_disaster_declarations.csv")

print("Total records:", len(df))

print("\nIncident Types:")
print(df["incident_type"].value_counts())

df["incident_begin_date"] = pd.to_datetime(df["incident_begin_date"], errors="coerce")
df["incident_end_date"] = pd.to_datetime(df["incident_end_date"], errors="coerce")

df["duration_days"] = (
    df["incident_end_date"] - df["incident_begin_date"]
).dt.days

valid_durations = df["duration_days"].dropna()
valid_durations = valid_durations[valid_durations >= 0]

print("\nDuration statistics (non-negative only):")
print(valid_durations.describe())

print("\nMedian duration by incident type:")
print(
    df.loc[df["duration_days"] >= 0]
    .groupby("incident_type")["duration_days"]
    .median()
    .sort_values(ascending=False)
)
