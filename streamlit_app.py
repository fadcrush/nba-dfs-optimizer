import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="NBA DFS Optimizer", page_icon="🏀", layout="wide")

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

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Data", "🔍 Filter Players", "⭐ Core Stacks", "⚡ Lineups"])

with tab1:
    st.header("Upload Slate File")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state['slate_data'] = df
            
            st.success(f"✅ Successfully loaded {len(df)} players")
            
            # Show preview
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Show column info
            st.subheader("Available Columns")
            cols = st.columns(4)
            for idx, col in enumerate(df.columns):
                with cols[idx % 4]:
                    st.text(col)
                    
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
    else:
        st.info("👆 Upload a CSV file to begin")

with tab2:
    st.header("Filter Player Pool")
    
    if 'slate_data' not in st.session_state:
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
            # This is a placeholder - you'll add actual filtering logic
            st.success(f"✅ Filters applied!")
            
            # Show sample filtered results
            st.subheader("Filtered Players")
            st.dataframe(df.head(20), use_container_width=True)

with tab3:
    st.header("Generate Core Stacks")
    
    if 'slate_data' not in st.session_state:
        st.warning("⚠️ Please upload and filter players first")
    else:
        st.info(f"💡 Each core stack is 4 players that will play together in the same lineup")
        
        strategy = st.selectbox(
            "Core Generation Strategy",
            ["Top Value Players", "Balanced (Value + Projection)", "Diverse Positions"]
        )
        
        if st.button("Generate Core Stacks", type="primary"):
            st.success(f"✅ Generated {num_cores} core stacks!")
            
            # Placeholder for core display
            for i in range(num_cores):
                with st.expander(f"Core Stack {i+1}", expanded=True):
                    st.write("Core players will appear here...")

with tab4:
    st.header("Generate Lineups")
    
    if 'slate_data' not in st.session_state:
        st.warning("⚠️ Please complete previous steps first")
    else:
        if st.button("Generate All Lineups", type="primary"):
            st.success(f"✅ Generated {num_cores * lineups_per_core} lineups!")
            
            # Placeholder for lineup display
            st.subheader("Generated Lineups")
            st.info("Lineups will appear here...")
            
        st.markdown("---")
        if st.button("📥 Export to CSV"):
            st.info("Export functionality coming soon...")

# Footer
st.markdown("---")
st.markdown("**NBA DFS Lineup Optimizer** | Built with Streamlit")