import pandas as pd
import plotly.graph_objects as go

def build_3d_wire(front_df, right_df):
    n = min(len(front_df), len(right_df))
    df = pd.DataFrame()
    df['X'] = front_df['x'].iloc[:n]
    df['Y'] = front_df['y'].iloc[:n]
    df['Z'] = right_df['y'].iloc[:n]
    df['wire'] = front_df['wire'].iloc[:n]
    return df


def plot_3d_wire_split(df):
    fig = go.Figure()
    for w in df['wire'].unique():
        sub = df[df['wire']==w]
        fig.add_trace(go.Scatter3d(x=sub['X'],y=sub['Y'],z=sub['Z'],mode='lines',name=f'Wire {w}'))
    return fig
