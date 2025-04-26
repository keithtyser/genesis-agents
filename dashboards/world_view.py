import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st, networkx as nx
from dashboards.utils import load_world, tail_logs
from dashboards.graph_builder import build_graph
from networkx.readwrite import json_graph
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import plotly.express as px

REFRESH_EVERY = int(os.getenv("DASH_REFRESH", "5"))  # seconds

st.set_page_config(page_title="Sandbox World-View", layout="wide")
st.title("🌍  Empty-Earth Sandbox — Live view")

# auto-refresh every REFRESH_EVERY seconds without full page flicker
st_autorefresh(interval=REFRESH_EVERY * 1000, key="worldview_autorefresh")

world = load_world()
g = build_graph(world)

# Sidebar metrics
with st.sidebar:
    st.markdown("### Stats")
    st.write(f"Current tick: **{world['tick']}**")
    st.write(f"Agents: **{len(world['agents'])}**")
    st.write(f"Objects: **{len(world['objects'])}**")

    def gini(values):
        if not values:
            return 0.0
        values = sorted(values)
        n = len(values)
        cumulative = 0
        for i, x in enumerate(values, 1):
            cumulative += (2 * i - n - 1) * x
        return cumulative / (n * sum(values)) if sum(values) else 0.0

    ownership_counts = {}
    for obj in world["objects"].values():
        creator = obj.get("creator")
        if creator:
            ownership_counts[creator] = ownership_counts.get(creator, 0) + 1
    ownership_gini = gini(list(ownership_counts.values()))

    st.write(f"Ownership Gini: **{ownership_gini:.2f}**")

    st.markdown("### Custom Verbs")
    for v, t in world.get("verbs", {}).items():
        st.write(f"{v} → {t}")

# Plotly force-directed
data = json_graph.node_link_data(g)

# colour palette mapping for kinds
kind_set = {node.get("kind", "object") for node in data["nodes"] if node.get("kind", "object") != "agent"}
palette_seq = px.colors.qualitative.Set2
palette = {"agent": "royalblue"}
for idx, kind in enumerate(sorted(kind_set)):
    palette[kind] = palette_seq[idx % len(palette_seq)]

# Compute spring layout once per refresh
pos = nx.spring_layout(g, seed=42, k=0.8)

# Performance guardrail: hide text labels if too many nodes
show_labels = len(data["nodes"]) <= 150

x, y, text, hover, marker_color, marker_size = [], [], [], [], [], []
for node_dict in data["nodes"]:
    node_id = node_dict["id"]
    node_kind = node_dict.get("kind", "object")
    pos_x, pos_y = pos[node_id]
    x.append(pos_x)
    y.append(pos_y)
    if show_labels:
        text.append(node_id)
    else:
        text.append("")

    marker_color.append(palette.get(node_kind, "lightgray"))
    marker_size.append(10 + 2 * g.degree(node_id))

    # Build hover info
    if node_kind == "agent":
        owned = ownership_counts.get(node_id, 0)
        agent_rec = world["agents"].get(node_id, {})
        parents = agent_rec.get("parents", [])
        hover.append(f"Agent: {node_id}<br>Owned objects: {owned}<br>Parents: {', '.join(parents) if parents else '—'}")
    else:
        obj_rec = world["objects"].get(node_id, {})
        creator = obj_rec.get("creator", "?")
        hover.append(f"Object: {node_id}<br>Kind: {node_kind}<br>Creator: {creator}")

# Build edges with styling
owns_x, owns_y, parent_x, parent_y = [], [], [], []
for src, dst, attrs in g.edges(data=True):
    x0, y0 = pos[src]
    x1, y1 = pos[dst]
    if attrs.get("rel") == "parent":
        parent_x += [x0, x1, None]
        parent_y += [y0, y1, None]
    else:
        owns_x += [x0, x1, None]
        owns_y += [y0, y1, None]

fig = go.Figure(
    data=[
        go.Scatter(x=owns_x, y=owns_y, mode="lines", line=dict(width=1, color="#4a86e8"), hoverinfo="none"),
        go.Scatter(x=parent_x, y=parent_y, mode="lines", line=dict(width=1, dash="dot", color="gray"), hoverinfo="none"),
        go.Scatter(
            x=x, y=y, mode="markers+text" if show_labels else "markers", text=text,
            textposition="bottom center", hoverinfo="text", textfont=dict(color="white"),
            hovertext=hover,
            marker=dict(size=marker_size, color=marker_color, line_width=2)
        )
    ],
    layout=go.Layout(
        showlegend=False, margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        dragmode="pan", hovermode="closest",
    )
)
fig.update_layout(autosize=True)
st.plotly_chart(fig, use_container_width=True)

logs = tail_logs(300)

with st.expander("📜 Recent chat & events", expanded=False):
    keyword = st.text_input("Filter", "", placeholder="Type to filter messages or events")
    def match(rec):
        if not keyword:
            return True
        kw = keyword.lower()
        if kw in rec.get("content", "").lower():
            return True
        for ev in rec.get("events", []):
            if kw in ev.lower():
                return True
        return False

    filtered = [r for r in logs if match(r)]

    html_lines = []
    for rec in filtered:
        turn = rec.get("tick", "?")
        speaker = rec.get("speaker", "?")
        ts = rec.get("time", "")
        ts_str = ts[11:19] if len(ts) >= 19 else ""
        color = palette.get("agent", "royalblue") if speaker in world["agents"] else "#6fcf70"
        html_lines.append(
            f"<div><span style='color:{color}; font-weight:bold'>T{turn} {speaker}</span> "
            f"<span style='color:gray;font-size:0.85em;'>[{ts_str}]</span>: {rec.get('content','')}</div>"
        )
        for ev in rec.get("events", []):
            html_lines.append(f"<div style='margin-left:24px;color:orange;'>• {ev}</div>")
    log_html = "\n".join(html_lines) or "<em>No log entries.</em>"
    st.markdown(
        f"<div id='logbox' style='height:300px; overflow-y:auto; border:1px solid #444; padding:8px;'>{log_html}</div>",
        unsafe_allow_html=True,
    )
    # auto-scroll to bottom
    st.markdown(
        "<script>var logbox=document.getElementById('logbox'); if(logbox){logbox.scrollTop=logbox.scrollHeight;}</script>",
        unsafe_allow_html=True,
    ) 