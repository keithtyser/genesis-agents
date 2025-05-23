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
import pandas as pd

REFRESH_EVERY = int(os.getenv("DASH_REFRESH", "5"))  # seconds

st.set_page_config(page_title="Genesis Agents - Live Dashboard", layout="wide")
st.title("🌍 Genesis Agents — Multi-Generational Civilization Tracker")

# auto-refresh every REFRESH_EVERY seconds without full page flicker
st_autorefresh(interval=REFRESH_EVERY * 1000, key="worldview_autorefresh")

world = load_world()
g = build_graph(world)

# Helper function to extract family relationships
def build_family_tree():
    """Build family tree data structure from agents."""
    family_data = []
    for agent_name, agent_data in world.get('agents', {}).items():
        parents = agent_data.get('parents', [])
        born_tick = agent_data.get('born', 0)
        skills = len(agent_data.get('skills', []))
        location = agent_data.get('location', 'unknown')
        
        family_data.append({
            'agent': agent_name,
            'parents': ', '.join(parents) if parents else 'Original',
            'born_tick': born_tick,
            'generation': 1 if not parents else 2,  # Simplified generation tracking
            'skills_count': skills,
            'location': location
        })
    return pd.DataFrame(family_data)

# Helper function to get innovation metrics
def get_innovation_metrics():
    """Extract innovation reward data."""
    innovation_rewards = world.get('environment', {}).get('innovation_rewards', [])
    if not innovation_rewards:
        return pd.DataFrame()
    
    innovation_df = pd.DataFrame(innovation_rewards)
    return innovation_df

# Helper function to get discovery materials
def get_discovery_data():
    """Get enhanced objects and discovery materials."""
    enhanced_objects = []
    discovery_materials = []
    
    for obj_id, obj_data in world.get('objects', {}).items():
        # Check for enhanced objects
        if obj_data.get('enhanced', False):
            enhanced_objects.append({
                'object_id': obj_id,
                'kind': obj_data.get('kind', 'unknown'),
                'creator': obj_data.get('creator', 'unknown'),
                'discovery_level': obj_data.get('discovery_level', 0),
                'rarity': obj_data.get('rarity', 'common')
            })
        
        # Check for discovery materials
        if obj_data.get('creator') in ['cosmic', 'ancient'] or obj_data.get('rarity') in ['rare', 'legendary']:
            discovery_materials.append({
                'object_id': obj_id,
                'kind': obj_data.get('kind', 'unknown'),
                'creator': obj_data.get('creator', 'unknown'),
                'energy_level': obj_data.get('energy_level', 'unknown'),
                'rarity': obj_data.get('rarity', 'unknown')
            })
    
    return pd.DataFrame(enhanced_objects), pd.DataFrame(discovery_materials)

# Main dashboard layout with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Overview", "👨‍👩‍👧‍👦 Family Trees", "🏆 Innovation", "🔮 Discovery", "🌍 Environment"])

with tab1:
    # Overview metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Tick", world.get('tick', 0))
        st.metric("Total Agents", len(world.get('agents', {})))
    
    with col2:
        total_objects = len(world.get('objects', {}))
        created_objects = len([obj for obj in world.get('objects', {}).values() 
                             if obj.get('creator') not in ['nature', None, 'cosmic', 'ancient']])
        st.metric("Total Objects", total_objects)
        st.metric("Agent-Created", created_objects)
    
    with col3:
        env_events = len(world.get('environment', {}).get('event_history', []))
        active_events = len(world.get('environment', {}).get('active_events', []))
        st.metric("Environmental Events", env_events)
        st.metric("Active Events", active_events)
    
    with col4:
        innovation_rewards = len(world.get('environment', {}).get('innovation_rewards', []))
        discovery_materials = len(world.get('environment', {}).get('discovery_materials', []))
        st.metric("Innovation Rewards", innovation_rewards)
        st.metric("Discovery Materials", discovery_materials)

    # Population Growth Chart
    family_df = build_family_tree()
    if not family_df.empty:
        st.subheader("📈 Population Growth Timeline")
        
        # Create population growth over time
        birth_data = family_df.groupby('born_tick').size().cumsum().reset_index()
        birth_data.columns = ['Tick', 'Population']
        
        fig_pop = px.line(birth_data, x='Tick', y='Population', 
                         title='Civilization Population Growth',
                         markers=True)
        fig_pop.update_layout(height=300)
        st.plotly_chart(fig_pop, use_container_width=True)

    # Network Visualization
    st.subheader("🔗 Civilization Network")

# colour palette mapping for kinds
    kind_set = {node.get("kind", "object") for node in json_graph.node_link_data(g)["nodes"] if node.get("kind", "object") != "agent"}
palette_seq = px.colors.qualitative.Set2
palette = {"agent": "royalblue"}
for idx, kind in enumerate(sorted(kind_set)):
    palette[kind] = palette_seq[idx % len(palette_seq)]

# Compute spring layout once per refresh
pos = nx.spring_layout(g, seed=42, k=0.8)

# Performance guardrail: hide text labels if too many nodes
    show_labels = len(json_graph.node_link_data(g)["nodes"]) <= 150

    data = json_graph.node_link_data(g)
x, y, text, hover, marker_color, marker_size = [], [], [], [], [], []
    
    ownership_counts = {}
    for obj in world["objects"].values():
        creator = obj.get("creator")
        if creator:
            ownership_counts[creator] = ownership_counts.get(creator, 0) + 1

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
            go.Scatter(x=parent_x, y=parent_y, mode="lines", line=dict(width=3, dash="dot", color="red"), hoverinfo="none", name="Family"),
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
    fig.update_layout(autosize=True, height=400)
st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("👨‍👩‍👧‍👦 Multi-Generational Family Trees")
    
    family_df = build_family_tree()
    if not family_df.empty:
        # Family statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            original_agents = family_df[family_df['parents'] == 'Original'].shape[0]
            st.metric("Original Agents", original_agents)
        
        with col2:
            children = family_df[family_df['parents'] != 'Original'].shape[0]
            st.metric("Children Born", children)
        
        with col3:
            avg_skills = family_df['skills_count'].mean()
            st.metric("Avg Skills per Agent", f"{avg_skills:.1f}")
        
        # Family tree table
        st.subheader("Family Tree Details")
        st.dataframe(family_df, use_container_width=True)
        
        # Skills distribution
        if family_df['skills_count'].sum() > 0:
            st.subheader("📚 Skill Distribution Across Generations")
            fig_skills = px.bar(family_df, x='agent', y='skills_count', 
                              color='generation', 
                              title='Skills per Family Member')
            st.plotly_chart(fig_skills, use_container_width=True)
    else:
        st.info("No family data available yet. Families will appear when breeding occurs.")

with tab3:
    st.header("🏆 Innovation Metrics & Rewards")
    
    innovation_df = get_innovation_metrics()
    if not innovation_df.empty:
        # Innovation summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rewards = innovation_df['reward_value'].sum()
            st.metric("Total Innovation Points", total_rewards)
        
        with col2:
            top_innovator = innovation_df.groupby('agent')['reward_value'].sum().idxmax()
            st.metric("Top Innovator", top_innovator)
        
        with col3:
            most_common_type = innovation_df['type'].mode().iloc[0] if not innovation_df.empty else "None"
            st.metric("Most Common Type", most_common_type)
        
        with col4:
            recent_innovations = innovation_df[innovation_df['tick'] >= world.get('tick', 0) - 10].shape[0]
            st.metric("Recent Innovations", recent_innovations)
        
        # Innovation timeline
        st.subheader("📈 Innovation Timeline")
        fig_innovation = px.scatter(innovation_df, x='tick', y='reward_value', 
                                   color='agent', symbol='type',
                                   title='Innovation Rewards Over Time',
                                   hover_data=['details'])
        st.plotly_chart(fig_innovation, use_container_width=True)
        
        # Innovation details table
        st.subheader("Innovation Details")
        st.dataframe(innovation_df, use_container_width=True)
        
        # Innovation by type
        if len(innovation_df) > 0:
            st.subheader("🎯 Innovation Types Summary")
            type_summary = innovation_df.groupby('type').agg({
                'reward_value': ['count', 'sum', 'mean']
            }).round(2)
            st.dataframe(type_summary, use_container_width=True)
    else:
        st.info("No innovation rewards yet. Innovations will appear when agents combine, experiment, or trade.")

with tab4:
    st.header("🔮 Discovery Materials & Enhanced Objects")
    
    enhanced_df, discovery_df = get_discovery_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✨ Enhanced Objects")
        if not enhanced_df.empty:
            st.metric("Enhanced Objects Created", len(enhanced_df))
            
            # Enhanced objects by creator
            creator_counts = enhanced_df['creator'].value_counts()
            fig_enhanced = px.pie(values=creator_counts.values, names=creator_counts.index,
                                title="Enhanced Objects by Creator")
            st.plotly_chart(fig_enhanced, use_container_width=True)
            
            st.dataframe(enhanced_df, use_container_width=True)
        else:
            st.info("No enhanced objects yet. Use discovery materials with EXPERIMENT commands.")
    
    with col2:
        st.subheader("🌟 Discovery Materials")
        if not discovery_df.empty:
            st.metric("Discovery Materials Available", len(discovery_df))
            
            # Discovery materials by type
            rarity_counts = discovery_df['rarity'].value_counts()
            fig_discovery = px.bar(x=rarity_counts.index, y=rarity_counts.values,
                                 title="Discovery Materials by Rarity")
            st.plotly_chart(fig_discovery, use_container_width=True)
            
            st.dataframe(discovery_df, use_container_width=True)
        else:
            st.info("No discovery materials yet. Environmental events will spawn them.")

with tab5:
    st.header("🌍 Environmental State & Events")
    
    env_data = world.get('environment', {})
    
    # Current environmental state
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🌤️ Current Conditions")
        st.metric("Weather", env_data.get('weather', 'unknown').title())
        st.metric("Season", env_data.get('season', 'unknown').title())
        st.metric("World Focus", world.get('current_focus', 'unknown').title())
    
    with col2:
        st.subheader("📊 Resources")
        resources = env_data.get('resources', {})
        for resource, amount in resources.items():
            color = "normal"
            if amount < 30:
                color = "inverse"
            elif amount > 80:
                color = "off"
            st.metric(resource.title(), amount, delta_color=color)
    
    with col3:
        st.subheader("⚠️ Pressure Indicators")
        scarcity = env_data.get('scarcity_pressure', 0)
        st.metric("Scarcity Pressure", scarcity)
        
        active_events = env_data.get('active_events', [])
        st.metric("Active Events", len(active_events))
    
    # Active events
    if active_events:
        st.subheader("🌟 Active Environmental Events")
        for event in active_events:
            with st.expander(f"{event.get('type', 'Unknown').title()} Event"):
                st.write(f"**Description:** {event.get('description', 'No description')}")
                st.write(f"**Duration:** {event.get('duration', 0)} ticks")
                st.write(f"**Started:** Tick {event.get('start_tick', 0)}")
                st.write(f"**Ends:** Tick {event.get('end_tick', 0)}")
    
    # Event history
    event_history = env_data.get('event_history', [])
    if event_history:
        st.subheader("📜 Environmental Event History")
        
        # Event frequency chart
        event_df = pd.DataFrame(event_history)
        if not event_df.empty:
            event_counts = event_df['type'].value_counts()
            fig_events = px.bar(x=event_counts.index, y=event_counts.values,
                              title="Environmental Event Frequency")
            st.plotly_chart(fig_events, use_container_width=True)
            
            # Recent events
            st.subheader("Recent Events")
            recent_events = event_df.tail(10) if len(event_df) > 10 else event_df
            st.dataframe(recent_events, use_container_width=True)

# Recent activity log at bottom
st.header("📜 Recent Activity Log")
logs = tail_logs(50)

keyword = st.text_input("Filter activity", "", placeholder="Type to filter messages or events")

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
    color = "royalblue" if speaker in world.get("agents", {}) else "#6fcf70"
        html_lines.append(
            f"<div><span style='color:{color}; font-weight:bold'>T{turn} {speaker}</span> "
            f"<span style='color:gray;font-size:0.85em;'>[{ts_str}]</span>: {rec.get('content','')}</div>"
        )
        for ev in rec.get("events", []):
            html_lines.append(f"<div style='margin-left:24px;color:orange;'>• {ev}</div>")

    log_html = "\n".join(html_lines) or "<em>No log entries.</em>"
    st.markdown(
    f"<div style='height:300px; overflow-y:auto; border:1px solid #444; padding:8px; background-color:#1e1e1e;'>{log_html}</div>",
        unsafe_allow_html=True,
    ) 