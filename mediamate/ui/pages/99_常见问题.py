import os
import streamlit as st
from mediamate.config import config


faq_file = f'{os.path.dirname(config.PROJECT_DIR)}/docs/FAQ.md'


with open(faq_file, 'r', encoding='utf-8') as file:
    markdown_content = file.read()

st.markdown(markdown_content)
