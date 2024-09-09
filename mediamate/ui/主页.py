import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import streamlit as st
from mediamate.config import config

readme_file = f'{os.path.dirname(config.PROJECT_DIR)}/README.md'

with open(readme_file, 'r', encoding='utf-8') as f:
    readme = f.read()

st.set_page_config(
    page_title='你好',
    page_icon='👋',
)

st.write("# 欢迎使用 RuMengAI MediaMate 项目! 👋")
st.markdown(readme.split('项目缺陷')[0])

docs_dir = f'{os.path.dirname(config.PROJECT_DIR)}/docs'
# 创建三列
col1, col2 = st.columns([1, 1])

# 在第一列中添加第一张图片
with col1:
    st.image(f'{docs_dir}/imgs/微信好友.jpg', caption="微信好友")

# 在第二列中添加第二张图片
with col2:
    st.image(f'{docs_dir}/imgs/二维码收款.jpg', caption="二维码收款")
