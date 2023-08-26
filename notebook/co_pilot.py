
import pandas as pd
# get the time series plot of the data

# read excel data into dataframe
df = pd.read_excel('oi_pivot_20apr.xlsx')

# unique of all columns in dataframe
def unique(df):
    for col in df.columns:
        print(col, df[col].unique())

unique(df)
