
import pandas as pd

# Example helper for future extension

def summarize_database(df):
    return df.groupby(['Patient', 'Wire']).size().reset_index(name='Segment Count')
