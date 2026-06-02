import numpy as np
import plotly.graph_objects as go

def build_frames(df_in, df_ex, steps=30):

    frames = []

    for t in np.linspace(0, 1, steps):

        X = (1 - t) * df_in["X"] + t * df_ex["X"]
        Y = (1 - t) * df_in["Y"] + t * df_ex["Y"]
        Z = (1 - t) * df_in["Z"] + t * df_ex["Z"]

        frames.append((X, Y, Z))

    return frames


def plot_animation_multi(df_in, df_ex):

    wires = df_in["wire"].unique()
    frames_data = []

    frames = build_frames(df_in, df_ex)

    for i, (X, Y, Z) in enumerate(frames):

        traces = []

        for w in wires:
            mask = df_in["wire"] == w

            traces.append(go.Scatter3d(
                x=X[mask],
                y=Y[mask],
                z=Z[mask],
                mode='lines',
                name=f"Wire {w}"
            ))

        frames_data.append(go.Frame(data=traces, name=str(i)))

    fig = go.Figure(
        data=frames_data[0].data,
        frames=frames_data
    )

    fig.update_layout(
        height=800,
        updatemenus=[{
            "type": "buttons",
            "buttons": [
                {"label": "Play", "method": "animate", "args": [None]},
                {"label": "Pause", "method": "animate", "args": [[None]]}
            ]
        }]
    )

    return fig
