import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* Base Theme */
        :root {
            --primary-color: #FF4B4B;
            --background-color: #0E1117;
            --secondary-background-color: #262730;
            --text-color: #FAFAFA;
            --font: "Source Sans Pro", sans-serif;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #1E1E1E;
            border-right: 1px solid #333;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        
        h1 {
            background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Metrics / Cards */
        div[data-testid="metric-container"] {
            background-color: #262730;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid #333;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #1E1E1E;
            border-radius: 8px 8px 0 0;
            border: 1px solid #333;
            color: #ccc;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border-bottom: none;
        }
        
        /* Buttons */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3);
        }

        </style>
    """, unsafe_allow_html=True)

def header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")
