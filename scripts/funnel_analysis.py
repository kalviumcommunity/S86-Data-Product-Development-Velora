import os
import pandas as pd
import matplotlib.pyplot as plt

# Create output folder
os.makedirs("output", exist_ok=True)

# ----------------------------
# Funnel Stages
# ----------------------------

stages = {
    "Sign Up": 10000,
    "Email Entered": 8000,
    "Password Created": 6000,
    "Email Verified": 5000,
    "Payment Added": 4000,
    "First Purchase": 2000
}

print("FUNNEL STAGES")
print(stages)

# ----------------------------
# Task 2
# Drop-off Calculation
# ----------------------------

stage_list = list(stages.values())
stage_names = list(stages.keys())

drop_off = []

for i in range(len(stage_list)-1):

    users_before = stage_list[i]
    users_after = stage_list[i+1]

    users_lost = users_before - users_after

    completion_rate = (users_after/users_before)*100

    drop_rate = (users_lost/users_before)*100

    drop_off.append({
        "from_stage": stage_names[i],
        "to_stage": stage_names[i+1],
        "users_lost": users_lost,
        "completion_rate": f"{completion_rate:.1f}%",
        "drop_rate": f"{drop_rate:.1f}%"
    })

funnel_df = pd.DataFrame(drop_off)

print("\nDROP OFF ANALYSIS")
print(funnel_df)

# Biggest drop
biggest_drop = funnel_df.loc[
    funnel_df["users_lost"].idxmax()
]

print("\nBIGGEST DROP")
print(biggest_drop)

# ----------------------------
# Task 3
# Visualization
# ----------------------------

colors = [
    "steelblue",
    "green",
    "orange",
    "purple",
    "red",
    "brown"
]

plt.figure(figsize=(10,6))

bars = plt.bar(
    stages.keys(),
    stages.values(),
    color=colors
)

plt.title("Signup Funnel")

plt.xlabel("Stage")

plt.ylabel("Users")

for bar in bars:

    y = bar.get_height()

    plt.text(
        bar.get_x()+bar.get_width()/2,
        y+100,
        int(y),
        ha="center"
    )

plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    "output/funnel_chart.png"
)

plt.show()

# ----------------------------
# Task 4
# Business Impact
# ----------------------------

revenue_per_customer = 100

impact=[]

for _, row in funnel_df.iterrows():

    revenue_lost = (
        row["users_lost"] *
        revenue_per_customer
    )

    impact.append({

        "drop_point":
        row["from_stage"]+" -> "+row["to_stage"],

        "users_lost":
        row["users_lost"],

        "revenue_impact":
        revenue_lost,

        "priority":
        "HIGH"
        if revenue_lost>100000
        else "MEDIUM"
    })

impact_df = pd.DataFrame(impact)

print("\nBUSINESS IMPACT")

print(
    impact_df.sort_values(
        "users_lost",
        ascending=False
    )
)

# ----------------------------
# Task 5
# Recommendation
# ----------------------------

recommendation=f"""
FUNNEL OPTIMIZATION

Highest Bottleneck

{biggest_drop['from_stage']}
↓

{biggest_drop['to_stage']}

Users Lost : {biggest_drop['users_lost']}

Drop Rate : {biggest_drop['drop_rate']}

Estimated Revenue Lost :
${biggest_drop['users_lost']*100}

Recommended Action

1 Improve this step first

2 Simplify user experience

3 Perform A/B testing

4 Measure conversion improvement
"""

print(recommendation)

with open(
    "output/funnel_analysis.txt",
    "w"
) as file:

    file.write(recommendation)

print("\nFiles Saved")
print("output/funnel_chart.png")
print("output/funnel_analysis.txt")