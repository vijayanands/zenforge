import streamlit as st


def set_page_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f0f2f6;
        }
        .content-container {
            background-color: #ffffff;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
        }
        .stTextInput>div>div>input {
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        .stSelectbox>div>div>div {
            border: 1px solid #ccc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_page_container_style(
    max_width: int = 1100,
    max_width_100_percent: bool = False,
    padding_top: int = 1,
    padding_right: int = 10,
    padding_left: int = 10,
    padding_bottom: int = 10,
    color: str = "black",
    background_color: str = "#f0f2f6",
):
    if max_width_100_percent:
        max_width_str = f"max-width: 100%;"
    else:
        max_width_str = f"max-width: {max_width}px;"
    st.markdown(
        f"""
            <style>
                .reportview-container .main .block-container{{
                    {max_width_str}
                    padding-top: {padding_top}rem;
                    padding-right: {padding_right}rem;
                    padding-left: {padding_left}rem;
                    padding-bottom: {padding_bottom}rem;
                }}
                .reportview-container .main {{
                    color: {color};
                    background-color: {background_color};
                }}
            </style>
            """,
        unsafe_allow_html=True,
    )
