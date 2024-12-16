import streamlit as st

from tools.utils import get_base64_of_bin_file


def set_title_bar():
    logo_path = "images/pathforge-logo-final.png"
    logo_base64 = get_base64_of_bin_file(logo_path)

    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');

            .title-bar {{
                display: flex;
                align-items: center;
                background: linear-gradient(135deg, #2c3e50, #4ca1af);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .title-bar img {{
                height: 50px;
                margin-right: 20px;
                filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.3));
            }}
            .title-bar h1 {{
                font-size: 24px;
                color: #ffffff;
                margin: 0;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            }}
            .empower-text {{
                font-family: 'Poppins', sans-serif;
                font-size: 32px;
                font-weight: 700;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                letter-spacing: 2px;
                margin-right: 20px;
            }}
            .highlight-blue {{
                color: #66ccff;
                font-weight: bold;
            }}
            .highlight-pink {{
                color: #ff99cc;
                font-weight: bold;
            }}
        </style>
        <div class="title-bar">
            <img src="data:image/png;base64,{logo_base64}" alt="PathForge Logo">
            <div class="empower-text">EMPOWER</div>
            <h1>
                Empowering Employee 
                <span class="highlight-pink">Productivity</span>, 
                <span class="highlight-blue">Performance</span>, 
                <span class="highlight-pink">Career</span>, 
                <span class="highlight-blue">Skills</span> and 
                <span class="highlight-pink">Learning</span>
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
