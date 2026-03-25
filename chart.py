import plotly.graph_objects as go

def build_chart(df, score):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Price"],
        name="WTI",
        line=dict(width=3)
    ))

    if score < 50:
        color = "rgba(255,0,0,0.2)"
    elif score <= 75:
        color = "rgba(255,255,0,0.2)"
    else:
        color = "rgba(0,255,0,0.2)"

    fig.add_vrect(
        x0=df["Date"].iloc[-30],
        x1=df["Date"].iloc[-1],
        fillcolor=color,
        opacity=0.3,
        line_width=0
    )

    fig.update_layout(template="plotly_dark", height=400)

    return fig
