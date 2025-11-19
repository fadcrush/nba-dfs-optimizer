import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="NBA DFS Optimizer", page_icon="🏀", layout="wide")

# Initialize session state
if 'slate_data' not in st.session_state:
    st.session_state['slate_data'] = None
if 'player_pool' not in st.session_state:
    st.session_state['player_pool'] = None
if 'core_stacks' not in st.session_state:
    st.session_state['core_stacks'] = []
if 'lineups' not in st.session_state:
    st.session_state['lineups'] = []

# Helper functions
def parse_csv(df):
    """Parse CSV and extract player data"""
    players = []
    
    for _, row in df.iterrows():
        player = {}
        
        # Flexible column mapping
        for col in df.columns:
            col_lower = col.lower()
            
            if 'name' in col_lower or col_lower == 'nickname':
                player['name'] = row[col]
            elif 'pos' in col_lower and 'opp' not in col_lower:
                player['position'] = row[col]
            elif 'sal' in col_lower or col_lower == 'salary':
                player['salary'] = float(str(row[col]).replace('$', '').replace(',', ''))
            elif 'proj' in col_lower or 'fppg' in col_lower:
                player['proj_pts'] = float(row[col])
            elif 'team' in col_lower and 'opp' not in col_lower:
                player['team'] = row[col]
            elif 'own' in col_lower:
                player['ownership'] = float(row[col])
        
        # Calculate value
        if 'name' in player and player.get('salary', 0) > 0 and player.get('proj_pts', 0) > 0:
            player['value'] = player['proj_pts'] / (player['salary'] / 1000)
            players.append(player)
    
    return pd.DataFrame(players)

def filter_players(df, min_projection=20.0, min_value=4.0, max_salary=12000):
    """Filter player pool"""
    filtered = df[
        (df['proj_pts'] >= min_projection) & 
        (df['value'] >= min_value) & 
        (df['salary'] <= max_salary)
    ].copy()
    
    return filtered.sort_values('value', ascending=False)

def generate_cores(df, num_cores=4, players_per_core=4):
    """Generate core stacks"""
    cores = []
    used_players = set()
    
    df_sorted = df.sort_values('value', ascending=False)
    
    for i in range(num_cores):
        core = []
        
        for _, player in df_sorted.iterrows():
            if player['name'] not in used_players and len(core) < players_per_core:
                core.append({
                    'name': player['name'],
                    'position': player['position'],
                    'salary': int(player['salary']),
                    'proj_pts': float(player['proj_pts']),
                    'value': float(player['value']),
                    'team': player.get('team', '')
                })
                used_players.add(player['name'])
        
        if len(core) == players_per_core:
            cores.append(core)
    
    return cores

def generate_lineups_from_cores(df, cores, lineups_per_core=5, salary_cap=60000):
    """Generate lineups from core stacks"""
    all_lineups = []
    
    for core_idx, core in enumerate(cores, 1):
        core_names = {p['name'] for p in core}
        core_salary = sum(p['salary'] for p in core)
        
        # Get available players (not in core)
        available = df[~df['name'].isin(core_names)].sort_values('value', ascending=False)
        
        for lineup_num in range(lineups_per_core):
            lineup = core.copy()
            current_salary = core_salary
            used_in_lineup = core_names.copy()
            
            # Add remaining players to fill 9-player lineup
            for _, player in available.iterrows():
                if len(lineup) >= 9:
                    break
                
                if player['name'] not in used_in_lineup:
                    if current_salary + player['salary'] <= salary_cap:
                        lineup.append({
                            'name': player['name'],
                            'position': player['position'],
                            'salary': int(player['salary']),
                            'proj_pts': float(player['proj_pts']),
                            'value': float(player['value']),
                            'team': player.get('team', '')
                        })
                        current_salary += player['salary']
                        used_in_lineup.add(player['name'])
            
            # Only add if we have a complete 9-player lineup
            if len(lineup) == 9:
                total_projection = sum(p['proj_pts'] for p in lineup)
                
                all_lineups.append({
                    'core_set': core_idx,
                    'lineup': lineup,
                    'total_salary': int(current_salary),
                    'remaining_salary': int(salary_cap - current_salary),
                    'projected_points': float(total_projection),
                    'num_players': len(lineup)
                })
    
    return all_lineups

# Title
st.title("🏀 NBA DFS Lineup Optimizer")
st.markdown("### Upload your slate and generate contrarian lineups")

# Sidebar
st.sidebar.header("📊 Settings")
num_cores = st.sidebar.number_input("Number of Core Stacks", min_value=1, max_value=10, value=4)
lineups_per_core = st.sidebar.number_input("Lineups Per Core", min_value=1, max_value=20, value=5)
salary_cap = st.sidebar.number_input("Salary Cap", min_value=40000, max_value=70000, value=60000, step=100)

st.sidebar.markdown("---")
st.sidebar.info("Upload a CSV file with player data to get started")

# Status indicators
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.session_state['slate_data'] is not None:
        st.success(f"✅ Slate: {len(st.session_state['slate_data'])} players")
    else:
        st.error("❌ No slate loaded")

with col2:
    if st.session_state['player_pool'] is not None:
        st.success(f"✅ Pool: {len(st.session_state['player_pool'])} players")
    else:
        st.error("❌ Not filtered")

with col3:
    if st.session_state['core_stacks']:
        st.success(f"✅ Cores: {len(st.session_state['core_stacks'])}")
    else:
        st.error("❌ No cores")

with col4:
    if st.session_state['lineups']:
        st.success(f"✅ Lineups: {len(st.session_state['lineups'])}")
    else:
        st.error("❌ No lineups")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Data", "🔍 Filter Players", "⭐ Core Stacks", "⚡ Lineups"])

with tab1:
    st.header("Upload Slate File")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            raw_df = pd.read_csv(uploaded_file)
            parsed_df = parse_csv(raw_df)
            
            st.session_state['slate_data'] = parsed_df
            
            st.success(f"✅ Successfully loaded {len(parsed_df)} players")
            
            # Show preview
            st.subheader("Data Preview (Top 15 by Value)")
            display_df = parsed_df.nlargest(15, 'value')[['name', 'position', 'team', 'salary', 'proj_pts', 'value']]
            st.dataframe(display_df, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
    else:
        st.info("👆 Upload a CSV file to begin")

with tab2:
    st.header("Filter Player Pool")
    
    if st.session_state['slate_data'] is None:
        st.warning("⚠️ Please upload a slate file first")
    else:
        df = st.session_state['slate_data']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_projection = st.number_input(
                "Minimum Projection", 
                min_value=0.0, 
                max_value=100.0, 
                value=20.0,
                step=1.0
            )
        
        with col2:
            min_value = st.number_input(
                "Minimum Value (pts/$1K)", 
                min_value=0.0, 
                max_value=20.0, 
                value=4.0,
                step=0.1
            )
        
        with col3:
            max_salary = st.number_input(
                "Maximum Salary", 
                min_value=3000, 
                max_value=15000, 
                value=12000,
                step=100
            )
        
        if st.button("Apply Filters", type="primary"):
            filtered = filter_players(df, min_projection, min_value, max_salary)
            st.session_state['player_pool'] = filtered
            
            st.success(f"✅ Filtered to {len(filtered)} players")
            
            # Show filtered results
            st.subheader("Filtered Players (Top 30)")
            display_df = filtered.head(30)[['name', 'position', 'team', 'salary', 'proj_pts', 'value']]
            st.dataframe(display_df, use_container_width=True)

with tab3:
    st.header("Generate Core Stacks")
    
    if st.session_state['player_pool'] is None:
        st.warning("⚠️ Please upload and filter players first")
    else:
        st.info(f"💡 Each core stack is 4 players that will play together in the same lineup")
        
        if st.button("Generate Core Stacks", type="primary"):
            cores = generate_cores(
                st.session_state['player_pool'], 
                num_cores=num_cores, 
                players_per_core=4
            )
            st.session_state['core_stacks'] = cores
            
            st.success(f"✅ Generated {len(cores)} core stacks!")
            
        # Display cores if they exist
        if st.session_state['core_stacks']:
            st.subheader("Core Stacks")
            
            for i, core in enumerate(st.session_state['core_stacks'], 1):
                total_sal = sum(p['salary'] for p in core)
                total_proj = sum(p['proj_pts'] for p in core)
                avg_value = sum(p['value'] for p in core) / len(core)
                
                with st.expander(f"Core Stack {i} - ${total_sal:,} | {total_proj:.1f} pts | Avg Value: {avg_value:.2f}", expanded=True):
                    for p in core:
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        with col1:
                            st.write(f"**{p['name']}** ({p['position']})")
                        with col2:
                            st.write(f"${p['salary']:,}")
                        with col3:
                            st.write(f"{p['proj_pts']:.1f} pts")
                        with col4:
                            st.write(f"Val: {p['value']:.2f}")

with tab4:
    st.header("Generate Lineups")
    
    if not st.session_state['core_stacks']:
        st.warning("⚠️ Please generate core stacks first")
    else:
        if st.button("Generate All Lineups", type="primary"):
            lineups = generate_lineups_from_cores(
                st.session_state['player_pool'],
                st.session_state['core_stacks'],
                lineups_per_core=lineups_per_core,
                salary_cap=salary_cap
            )
            st.session_state['lineups'] = lineups
            
            if lineups:
                avg_proj = sum(lu['projected_points'] for lu in lineups) / len(lineups)
                st.success(f"✅ Generated {len(lineups)} lineups!")
                st.info(f"Average Projection: {avg_proj:.1f} pts")
            else:
                st.error("❌ Could not generate any valid lineups. Try loosening filters or increasing salary cap.")
        
        # Display lineups if they exist
        if st.session_state['lineups']:
            st.subheader("Generated Lineups")
            
            for i, lineup in enumerate(st.session_state['lineups'], 1):
                under_cap = lineup['remaining_salary'] >= 0
                
                with st.expander(
                    f"Lineup {i} (Core {lineup['core_set']}) - "
                    f"${lineup['total_salary']:,} | {lineup['projected_points']:.1f} pts | "
                    f"{'✅' if under_cap else '❌'} ${lineup['remaining_salary']:,} remaining",
                    expanded=False
                ):
                    for idx, p in enumerate(lineup['lineup']):
                        is_core = idx < 4
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{p['name']}** ({p['position']}) {'🌟' if is_core else ''}")
                        with col2:
                            st.write(p.get('team', ''))
                        with col3:
                            st.write(f"${p['salary']:,}")
                        with col4:
                            st.write(f"{p['proj_pts']:.1f} pts")
                        with col5:
                            st.write(f"{p['value']:.2f}")
            
            # Export button
            st.markdown("---")
            if st.button("📥 Export Lineups to CSV"):
                # Create CSV
                rows = []
                for i, lineup in enumerate(st.session_state['lineups'], 1):
                    for p in lineup['lineup']:
                        rows.append({
                            'Lineup': i,
                            'Player': p['name'],
                            'Position': p['position'],
                            'Team': p.get('team', ''),
                            'Salary': p['salary'],
                            'Projection': p['proj_pts'],
                            'Value': p['value']
                        })
                
                export_df = pd.DataFrame(rows)
                csv = export_df.to_csv(index=False)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"nba_lineups_{timestamp}.csv"
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=filename,
                    mime='text/csv',
                )
                st.success("✅ Ready to download!")

# Footer
st.markdown("---")
st.markdown("**NBA DFS Lineup Optimizer** | Built with Streamlit")