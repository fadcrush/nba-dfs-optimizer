pythonimport streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

st.set_page_config(
    page_title="NBA DFS Optimizer",
    page_icon="🏀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 10px 30px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏀 NBA DFS Lineup Optimizer")
st.markdown("### Build winning lineups with core stack strategy")

# Sidebar
st.sidebar.header("📊 Status")
if 'slate_loaded' not in st.session_state:
    st.session_state.slate_loaded = False
    st.session_state.player_pool = None
    st.session_state.cores = []
    st.session_state.lineups = []

st.sidebar.metric("Slate Loaded", "✅" if st.session_state.slate_loaded else "❌")
st.sidebar.metric("Player Pool", len(st.session_state.player_pool) if st.session_state.player_pool is not None else 0)
st.sidebar.metric("Core Stacks", len(st.session_state.cores))
st.sidebar.metric("Lineups", len(st.session_state.lineups))

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Upload Slate", 
    "🔍 Filter Pool", 
    "⭐ Core Stacks", 
    "⚡ Generate Lineups", 
    "👀 View Results"
])

# Tab 1: Upload Slate
with tab1:
    st.header("Upload Slate File")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv', 'xlsx'],
            help="Upload your DraftKings or FanDuel projection file"
        )
    
    with col2:
        platform = st.selectbox("Platform", ["FanDuel", "DraftKings"])
    
    if uploaded_file is not None:
        if st.button("Load Slate", type="primary"):
            # Load CSV
            df = pd.read_csv(uploaded_file)
            
            # Standardize columns (simplified)
            column_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'name' in col_lower:
                    column_map[col] = 'name'
                elif 'pos' in col_lower:
                    column_map[col] = 'position'
                elif 'sal' in col_lower:
                    column_map[col] = 'salary'
                elif 'proj' in col_lower or 'fppg' in col_lower:
                    column_map[col] = 'proj_pts'
                elif 'team' in col_lower:
                    column_map[col] = 'team'
            
            df = df.rename(columns=column_map)
            
            # Add calculated fields
            if 'proj_pts' in df.columns and 'salary' in df.columns:
                df['value'] = df['proj_pts'] / (df['salary'] / 1000)
            
            # Store in session
            st.session_state.slate_data = df
            st.session_state.slate_loaded = True
            
            st.success(f"✅ Loaded {len(df)} players from slate!")
            
            # Show preview
            st.subheader("Preview (Top 10 by Projection)")
            if 'proj_pts' in df.columns:
                preview = df.nlargest(10, 'proj_pts')[['name', 'position', 'team', 'salary', 'proj_pts', 'value']]
                st.dataframe(preview, use_container_width=True)

# Tab 2: Filter Pool
with tab2:
    st.header("Filter Player Pool")
    
    if not st.session_state.slate_loaded:
        st.warning("⚠️ Please upload a slate first")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_minutes = st.number_input("Minimum Minutes", value=22, min_value=0)
        
        with col2:
            min_value = st.number_input("Minimum Value", value=2.0, step=0.1)
        
        with col3:
            max_salary = st.number_input("Max Salary (0=none)", value=0, step=100)
        
        if st.button("Apply Filters", type="primary"):
            df = st.session_state.slate_data.copy()
            
            # Apply filters
            if 'value' in df.columns:
                filtered = df[df['value'] >= min_value]
            else:
                filtered = df
            
            if max_salary > 0:
                filtered = filtered[filtered['salary'] <= max_salary]
            
            # Sort by value
            filtered = filtered.sort_values('value', ascending=False)
            
            st.session_state.player_pool = filtered
            
            st.success(f"✅ Filtered to {len(filtered)} players")
            
            # Show top 20
            st.subheader("Top 20 Value Plays")
            top20 = filtered.head(20)[['name', 'position', 'team', 'salary', 'proj_pts', 'value']]
            st.dataframe(top20, use_container_width=True)

# Tab 3: Core Stacks
with tab3:
    st.header("Generate Core Stacks")
    
    if st.session_state.player_pool is None:
        st.warning("⚠️ Please filter player pool first")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            num_cores = st.number_input("Number of Core Stacks", value=4, min_value=1, max_value=10)
        
        with col2:
            players_per_core = st.number_input("Players Per Core", value=4, min_value=2, max_value=6)
        
        if st.button("Generate Core Stacks", type="primary"):
            df = st.session_state.player_pool
            cores = []
            used_players = set()
            
            # Simple core generation
            for i in range(num_cores):
                core = []
                available = df[~df['name'].isin(used_players)]
                
                for j in range(players_per_core):
                    if len(available) > 0:
                        player = available.iloc[j]
                        core.append(player.to_dict())
                        used_players.add(player['name'])
                
                if len(core) == players_per_core:
                    cores.append(core)
            
            st.session_state.cores = cores
            
            st.success(f"✅ Generated {len(cores)} core stacks")
            
            # Display cores
            for i, core in enumerate(cores, 1):
                with st.expander(f"Core Stack {i} (${sum(p['salary'] for p in core):,})"):
                    for player in core:
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        col1.write(f"**{player['name']}**")
                        col2.write(player['position'])
                        col3.write(f"${player['salary']:,}")
                        col4.write(f"{player['proj_pts']:.1f} pts")

# Tab 4: Generate Lineups
with tab4:
    st.header("Generate Lineups")
    
    if len(st.session_state.cores) == 0:
        st.warning("⚠️ Please generate core stacks first")
    else:
        lineups_per_core = st.number_input("Lineups Per Core", value=5, min_value=1, max_value=20)
        
        if st.button("Generate Lineups", type="primary"):
            lineups = []
            
            with st.spinner("Generating lineups..."):
                for core_idx, core in enumerate(st.session_state.cores):
                    for i in range(lineups_per_core):
                        # Simple lineup generation
                        lineup_players = core.copy()
                        
                        # Add 5 more players
                        remaining = st.session_state.player_pool[
                            ~st.session_state.player_pool['name'].isin([p['name'] for p in core])
                        ].head(5)
                        
                        for _, player in remaining.iterrows():
                            lineup_players.append(player.to_dict())
                        
                        lineup = {
                            'core_set': core_idx + 1,
                            'players': lineup_players,
                            'salary': sum(p['salary'] for p in lineup_players),
                            'projection': sum(p['proj_pts'] for p in lineup_players),
                            'num_players': len(lineup_players)
                        }
                        
                        lineups.append(lineup)
            
            st.session_state.lineups = lineups
            
            avg_proj = sum(l['projection'] for l in lineups) / len(lineups)
            avg_sal = sum(l['salary'] for l in lineups) / len(lineups)
            
            st.success(f"✅ Generated {len(lineups)} lineups")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Lineups", len(lineups))
            col2.metric("Avg Projection", f"{avg_proj:.1f} pts")
            col3.metric("Avg Salary", f"${avg_sal:,.0f}")

# Tab 5: View Results
with tab5:
    st.header("View Generated Lineups")
    
    if len(st.session_state.lineups) == 0:
        st.warning("⚠️ No lineups generated yet")
    else:
        # Summary table
        summary_data = []
        for i, lineup in enumerate(st.session_state.lineups, 1):
            summary_data.append({
                'Lineup #': i,
                'Core Set': lineup['core_set'],
                'Salary': f"${lineup['salary']:,}",
                'Projection': f"{lineup['projection']:.1f}",
                'Players': lineup['num_players']
            })
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        
        # Detailed view
        st.subheader("Detailed Lineup View")
        lineup_num = st.selectbox("Select Lineup", range(1, len(st.session_state.lineups) + 1))
        
        if lineup_num:
            lineup = st.session_state.lineups[lineup_num - 1]
            
            st.info(f"**Core Set {lineup['core_set']}** | Salary: ${lineup['salary']:,} | Projection: {lineup['projection']:.1f} pts")
            
            # Player table
            players_df = pd.DataFrame(lineup['players'])
            if 'name' in players_df.columns:
                st.dataframe(
                    players_df[['name', 'position', 'team', 'salary', 'proj_pts', 'value']],
                    use_container_width=True
                )
            
            # Export button
            if st.button("Download This Lineup (JSON)"):
                json_str = json.dumps(lineup, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"lineup_{lineup_num}.json",
                    mime="application/json"
                )

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | NBA DFS Lineup Optimizer")