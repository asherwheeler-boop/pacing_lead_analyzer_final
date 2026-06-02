import numpy as np
import plotly.graph_objects as go

def build_animation_frames(df_in, df_ex, steps=25):
    frames = []
    for t in np.linspace(0,1,steps):
        X = (1-t)*df_in['X'] + t*df_ex['X']
        Y = (1-t)*df_in['Y'] + t*df_ex['Y']
        Z = (1-t)*df_in['Z'] + t*df_ex['Z']
        frames.append((X,Y,Z))
    return frames


def plot_animation_multi(df_in, df_ex):
    wires = df_in['wire'].unique()
    frames = []
    interp = build_animation_frames(df_in, df_ex)

    for i,(X,Y,Z) in enumerate(interp):
        traces = []
        for w in wires:
            mask = df_in['wire']==w
            traces.append(go.Scatter3d(x=X[mask],y=Y[mask],z=Z[mask],mode='lines'))
        frames.append(go.Frame(data=traces,name=str(i)))

    fig = go.Figure(data=frames[0].data,frames=frames)
    return fig
