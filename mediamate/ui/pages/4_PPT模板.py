import os
import yaml
import streamlit as st
import subprocess
import datetime
import json
from mediamate.config import config
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


def yaml_file_handler(file_name: str) -> dict:
    """  """
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as yaml_file:
            result = yaml.safe_load(yaml_file)
            if not result:
                logger.warning(f'文件为空: {file_name}')
                result = {}
    else:
        logger.error(f'文件不存在: {file_name}')
        st.stop()
    return result
project_media_config = f'{os.path.dirname(config.PROJECT_DIR)}/.media.yaml'
media_config = yaml_file_handler(project_media_config)
media_configs = media_config['media'].get('xhs')
if not media_configs:
    media_configs = media_config['media'].get('dy')
if not media_configs:
    logger.error(f'缺少配置文件')
    st.stop()
news_dir = f"{config.DATA_DIR}/upload/{media_configs[0]['platform']}/{media_configs[0]['account']}"
media_types = {
    '.png': st.image,
    '.jpg': st.image,
    '.jpeg': st.image,
    '.mp4': st.video,
    '.wav': st.audio,
    '.mp3': st.audio
}


# 获取示例目录
examples_dir = os.path.join(os.path.dirname(config.PROJECT_DIR), 'examples')

st.markdown('### 新闻模板')
advance_dir = f'{os.path.dirname(config.PROJECT_DIR)}/examples/advance'


# 定义要运行的示例列表及其说明
examples = {
    'KIMI_PPT': {
        'file': f'{advance_dir}/ex_kimi_ppt.py',
        'description': '1. 该示例会打开 [kimi 网站](https://kimi.moonshot.cn/), 首次需要登录.\n2. 将PPT转为图片时要求电脑安装PowerPoint. ',
        'upload_path': f'{news_dir}/kimi_ppt'
    }
}


# 创建一个下拉菜单，让用户选择要运行的示例
selected_script = st.selectbox("选择要运行的示例:", list(examples.keys()))
st.markdown("**示例说明:**")
st.markdown(examples[selected_script]["description"])

# 创建一个空字典用于存储用户输入的参数
if 'script_params' not in st.session_state:
    st.session_state.script_params = {}

st.markdown("**参数面板**")
if selected_script == 'KIMI_PPT':
    headless = st.radio('无头模式启动浏览器, False会打开浏览器界面', [False, True], index=0, key='headless')
    topic = st.text_input('PPT主题(也可以是本地文本文档)', value='小红书涨粉操作手册')
    logo_path = st.text_input('logo的绝对路径, 不填则不替换logo', value=f'{os.path.dirname(config.PROJECT_DIR)}/docs/imgs/logo-透明底.png'.replace('\\', '/'))
    username = st.text_input('作者, 不填则不替换PPT中的作者', value='RuMengAI')
    scene = st.text_input('PPT模板场景(参考kimi生成PPT的页面)', value='商业计划')
    style = st.text_input('PPT设计风格(参考kimi生成PPT的页面)', value='简约')
    color_index = st.number_input('PPT主题颜色索引', value=-4)
    card_index = st.number_input('PPT模板卡片索引', value=0)
    st.session_state.script_params = {
        'headless': headless,
        'topic': topic,
        'logo_path': logo_path,
        'username': username,
        'scene': scene,
        'style': style,
        'color_index': color_index,
        'card_index': card_index
    }

# 发布图文时的元数据配置
st.markdown("### 发布图文时的元数据配置")
title = st.text_input('标题', value='科技新闻')
description = st.text_area('描述', value='通过AI自动生成新闻并上传')
tags = st.text_input('标签(多个标签用英文逗号分隔)', value='RuMengAI, 新闻, 科技')
tags = tags.replace('，', ',')
location = st.text_input('地点', value='上海')
music = st.text_input('音乐', value='热歌榜')
sticker = st.text_input('贴纸', value='科技')
allow_save = st.selectbox('允许保存', ['是', '否'], index=1)

# 将标签转换为元组
if tags.strip():
    tags = [kw.strip() for kw in tags.split(',') if kw.strip()]
else:
    tags = []

# 汇总元数据
metadata = {
    '标题': title,
    '描述': description,
    '标签': tags,
    '地点': location,
    '音乐': music,
    '贴纸': sticker,
    '允许保存': allow_save,
}
st.session_state.script_params['metadata'] = metadata
st.json(st.session_state.script_params)


if st.button('运行示例', key='run_example'):
    placeholder = st.empty()
    script_to_run = examples[selected_script]['file']
    with st.spinner(f"正在运行 {script_to_run} ..."):
        with placeholder:
            result = subprocess.run(["python", script_to_run, json.dumps(st.session_state.script_params)], capture_output=True, text=True, encoding='utf-8')
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{current_time}] 运行示例: {script_to_run}\n"
            log_entry += f"返回码: {result.returncode}\n"
            log_entry += f"标准输出:\n{result.stdout}\n"
            log_entry += f"标准错误:\n{result.stderr}\n"
            st.write("运行日志:")
            st.code(log_entry)
            st.write("示例输出:")
            if result.returncode == 0:
                st.success("示例运行成功")
                st.code(result.stdout)
                media_dir = examples[selected_script].get('upload_path')
                if os.path.exists(media_dir):
                    with st.expander(f'点击展开/折叠结果'):
                        for media_file in os.listdir(media_dir):
                            file_ext = os.path.splitext(media_file)[1].lower()
                            if file_ext in media_types:
                                media_path = os.path.join(media_dir, media_file)
                                media_types[file_ext](media_path, caption=media_file)
            else:
                st.error("示例运行失败")
                st.code(result.stderr)
