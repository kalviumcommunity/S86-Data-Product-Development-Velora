import pandas as pd

def load_data():
    df = pd.read_csv("data/master_dataset.csv")

    df["created_date"] = pd.to_datetime(df["created_date"])
    df["resolved_date"] = pd.to_datetime(df["resolved_date"])

    return df