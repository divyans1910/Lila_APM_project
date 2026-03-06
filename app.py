import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
import glob
from datetime import datetime

# --- 1. OPERATIONAL CONFIGURATION ---
MAP_CONFIG = {
    'AmbroseValley': {'scale': 900, 'ox': -370, 'oz': -473, 'img': 'AmbroseValley_Minimap.png', 'color': '#00FF41'},
    'GrandRift': {'scale': 581, 'ox': -290, 'oz': -290, 'img': 'GrandRift_Minimap.png', 'color': '#FFD700'},
    'Lockdown': {'scale': 1000, 'ox': -500, 'oz': -500, 'img': 'Lockdown_Minimap.jpg', 'color': '#FF3131'}
}

EMOJI_KILL, EMOJI_DEATH, EMOJI_LOOT, EMOJI_STORM = "🎯", "💀", "📦", "⚡"

st.set_page_config(page_title="LILA BLACK", layout="wide", initial_sidebar_state="expanded")

# --- 2. TACTICAL UI STYLING ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        .stApp { background-color: #0B0E11; font-family: 'JetBrains Mono', monospace; }
        .block-container { padding-top: 5.5rem !important; }
        .metric-card {
            background: rgba(255, 255, 255, 0.1); 
            padding: 0 1.5rem; border-radius: 4px; border: 1px solid rgba(0, 255, 65, 0.5);
            text-align: left; width: 100%; height: 80px;      
            display: flex; flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: 10px;
        }
        .metric-label { color: #AAA; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; }
        .metric-value { color: #00FF41; font-size: 2.2rem; font-weight: 700; }
        .event-key-container {
            display: flex; gap: 20px; background: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 4px; border-left: 3px solid #00FF41; margin-bottom: 15px;
        }
        .key-item { font-size: 0.75rem; color: #EEE; display: flex; align-items: center; gap: 8px; }
        .key-icon { color: #00FF41; font-weight: bold; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        .map-loading-zone {
            height: 700px; display: flex; align-items: center; justify-content: center;
            background: rgba(0, 255, 65, 0.02); border: 2px dashed rgba(0, 255, 65, 0.2);
            color: #00FF41; font-weight: bold; animation: pulse 1.5s infinite; text-transform: uppercase; letter-spacing: 3px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data
def get_session_library():
    files = glob.glob(os.path.join("player_data", "**", "*.nakama-0"), recursive=True)
    library = []
    for f in files:
        if os.path.basename(f).startswith('.'): continue
        try:
            temp_df = pd.read_parquet(f, columns=['user_id', 'map_id'], engine='pyarrow')
            folder_name = os.path.basename(os.path.dirname(f))
            date_obj = datetime.strptime(f"{folder_name}_2026", "%B_%d_%Y").date()
            raw_id = str(temp_df['user_id'].iloc[0]).strip()
            library.append({"path": f, "name": os.path.basename(f), "type": "🤖 Bot" if raw_id.isdigit() else "👤 Human", "date": date_obj, "map": str(temp_df['map_id'].iloc[0])})
        except: continue
    return pd.DataFrame(library)

def load_combined_data(paths, target_map):
    frames = []
    for p in paths:
        df = pd.read_parquet(p, engine='pyarrow')
        df = df[df['map_id'] == target_map].copy()
        if df.empty: continue
        df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
        
        if pd.api.types.is_datetime64_any_dtype(df['ts']):
            df['dt'] = df['ts']
        else:
            ts_val = df['ts'].iloc[0]
            if isinstance(ts_val, (int, float)):
                unit = 's' if df['ts'].max() < 1e12 else 'ns'
                df['dt'] = pd.to_datetime(df['ts'], unit=unit)
            else:
                df['dt'] = pd.to_datetime(df['ts'])

        df['rel_sec'] = (df['dt'] - df['dt'].min()).dt.total_seconds()
        df['callsign'] = f"{str(df['user_id'].iloc[0]).strip()[:8]}"
        frames.append(df)
        
    if not frames: return pd.DataFrame(), target_map
    full_df = pd.concat(frames, ignore_index=True)
    conf = MAP_CONFIG.get(target_map, MAP_CONFIG['AmbroseValley'])
    full_df['px_x'] = ((full_df['x'] - conf['ox']) / conf['scale']) * 1024
    full_df['px_y'] = (1 - ((full_df['z'] - conf['oz']) / conf['scale'])) * 1024
    return full_df, target_map

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#00FF41; margin-bottom:0;'>LILA BLACK</h1>", unsafe_allow_html=True)
    lib_df = get_session_library()
    with st.expander("📂 SESSION SETUP", expanded=True):
        valid_dates = sorted(lib_df['date'].dropna().unique())
        sel_date = st.date_input("PLAYTEST DATE", value=max(valid_dates) if valid_dates else datetime.now().date())
        date_context = lib_df[lib_df['date'] == sel_date]
        if date_context.empty: st.stop()
        target_map = st.selectbox("OPERATIONAL AREA", sorted(date_context['map'].unique()))
    
    with st.expander("👥 ENTITY SELECTOR", expanded=True):
        map_context = date_context[date_context['map'] == target_map]
        search_query = st.text_input("🔍 SEARCH CALLSIGN", "").lower()
        h_avail = map_context[map_context['type']=="👤 Human"]
        b_avail = map_context[map_context['type']=="🤖 Bot"]
        if search_query:
            h_avail = h_avail[h_avail['name'].str.lower().str.contains(search_query)]
            b_avail = b_avail[b_avail['name'].str.lower().str.contains(search_query)]
        sel_h = st.multiselect("HUMANS", h_avail['path'], format_func=os.path.basename)
        sel_b = st.multiselect("BOTS", b_avail['path'], format_func=os.path.basename)
        all_selected = list(sel_h) + list(sel_b)

    with st.expander("🔥 TACTICAL OVERLAY", expanded=True):
        show_heatmap = st.checkbox("ENABLE HEATMAP", value=False)
        # Split options to distinguish between types
        heatmap_mode = st.radio("ANALYSIS TARGET", 
                                ["High-Traffic (Movement)", "Kill Zones (Attack)", "Death Zones (Fatalities)"]) if show_heatmap else None

# --- 5. MAIN INTERFACE ---
if not all_selected:
    st.markdown('<div class="map-loading-zone">AWAITING ENTITY AUTHORIZATION...</div>', unsafe_allow_html=True)
else:
    df, active_map = load_combined_data(all_selected, target_map)
    t_max = float(df['rel_sec'].max()) if not df.empty else 0.0

    if 'global_playhead' not in st.session_state:
        st.session_state.global_playhead = t_max

    with st.expander("📊 OPERATIONAL METRICS", expanded=True):
        m1, m2, m3, m4 = st.columns(4)
        metrics = [("Entities", len(df["callsign"].unique())), 
                   ("Kills", len(df[df["event"].str.contains("Kill", case=False)])),
                   ("Deaths", len(df[df["event"].str.contains("Death|Storm", case=False)])),
                   ("Loot", len(df[df["event"].str.contains("Loot", case=False)]))]
        for col, (l, v) in zip([m1, m2, m3, m4], metrics):
            col.markdown(f'<div class="metric-card"><div class="metric-label">{l}</div><div class="metric-value">{v}</div></div>', unsafe_allow_html=True)

    st.slider("🎞️ TIMELINE CONTROL", 0.0, t_max, key="global_playhead")
    v_df = df[df['rel_sec'] <= st.session_state.global_playhead].copy()

    st.markdown(f"""
        <div class="event-key-container">
            <div class="key-item"><span class="key-icon">{EMOJI_KILL}</span> KILL</div>
            <div class="key-item"><span class="key-icon">{EMOJI_DEATH}</span> DEATH</div>
            <div class="key-item"><span class="key-icon">{EMOJI_LOOT}</span> LOOT</div>
            <div class="key-item"><span class="key-icon">{EMOJI_STORM}</span> STORM</div>
        </div>
    """, unsafe_allow_html=True)

    col_map, col_log = st.columns([2.3, 1])
    
    with col_map:
        fig = go.Figure()
        img_p = os.path.join("player_data", "minimaps", MAP_CONFIG[active_map]['img'])
        if os.path.exists(img_p):
            fig.add_layout_image(dict(source=Image.open(img_p), xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))

        # --- ENHANCED INDEPENDENT HEATMAP LOGIC ---
        if show_heatmap and not v_df.empty:
            if "Kill Zones" in heatmap_mode:
                h_data = v_df[v_df['event'].str.contains('Kill', case=False, na=False)]
                colors = 'Reds'
            elif "Death Zones" in heatmap_mode:
                h_data = v_df[v_df['event'].str.contains('Death|Storm', case=False, na=False)]
                colors = 'Purples'
            else: # Movement
                h_data = v_df[v_df['event'].str.contains('Position', case=False, na=False)]
                colors = 'Greens'
            
            if not h_data.empty:
                fig.add_trace(go.Histogram2dContour(
                    x=h_data['px_x'], y=h_data['px_y'],
                    colorscale=colors, ncontours=40, line_width=0, 
                    opacity=0.6, showlegend=False, hoverinfo='skip'
                ))

        for cs in v_df['callsign'].unique():
            p_data = v_df[v_df['callsign'] == cs]
            pos = p_data[p_data['event'].str.contains('Position', case=False)]
            if not pos.empty:
                fig.add_trace(go.Scatter(x=pos['px_x'], y=pos['px_y'], mode='lines', line=dict(width=2), name=cs, hoverinfo='skip'))
            evs = p_data[~p_data['event'].str.contains('Position', case=False)]
            for _, row in evs.iterrows():
                e = str(row['event']).lower()
                mark = EMOJI_STORM if "storm" in e else EMOJI_KILL if "kill" in e else EMOJI_DEATH if "death" in e else EMOJI_LOOT if "loot" in e else None
                if mark:
                    fig.add_trace(go.Scatter(x=[row['px_x']], y=[row['px_y']], mode='text', text=[mark], textfont=dict(size=24), name=f"{cs}: {row['event']}", hoverinfo='name'))

        fig.update_layout(width=900, height=800, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        fig.update_xaxes(range=[0, 1024], visible=False); fig.update_yaxes(range=[1024, 0], visible=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_log:
        st.markdown("<p style='color:#00FF41; font-size:0.75rem; font-weight:bold;'>// JUMP TO CRITICAL EVENT</p>", unsafe_allow_html=True)
        jump_events = df[df['event'].str.contains('Kill|Death|Storm', case=False, na=False)].sort_values('rel_sec')
        if not jump_events.empty:
            jump_events['label'] = jump_events.apply(lambda r: f"{r['event']} - {r['callsign']} (@ {int(r['rel_sec'])}s)", axis=1)
            selected_label = st.selectbox("Select event", options=["--- Select Target ---"] + list(jump_events['label']), label_visibility="collapsed")
            if selected_label != "--- Select Target ---":
                new_ts = jump_events[jump_events['label'] == selected_label]['rel_sec'].iloc[0]
                st.session_state.global_playhead = float(new_ts)
                st.rerun()

        st.markdown("<br><p style='color:#666; font-size:0.7rem; letter-spacing:2px;'>// INTELLIGENCE FEED</p>", unsafe_allow_html=True)
        log_df = v_df[~v_df['event'].str.contains('Position', case=False)].sort_values('dt', ascending=False)
        st.dataframe(log_df[['dt', 'event', 'callsign']], hide_index=True, use_container_width=True, height=650)