import pandas as pd

def clean_data(df):
    df.dropna(how='all', inplace=True)  # Remove empty rows
    df.fillna('', inplace=True)  # Replace missing values with empty strings
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

