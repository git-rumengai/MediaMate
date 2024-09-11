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
    '每日资讯': {
        'file': f'{advance_dir}/ex_mrzx.py',
        'description': '该示例需要需要能访问Google, 这是一个 每日资讯 的示例. ',
        'upload_path': f'{news_dir}/news_mrzx'
    },
    '平台精选': {
        'file': f'{advance_dir}/ex_ptjx.py',
        'description': '该示例需要需要能访问Google, 这是一个 平台精选 的示例. ',
        'upload_path': f'{news_dir}/news_ptjx'
    },
    '前沿资讯': {
        'file': f'{advance_dir}/ex_qyzx.py',
        'description': '该示例需要需要能访问Google, 这是一个 前沿资讯 的示例. ',
        'upload_path': f'{news_dir}/news_qyzx'
    },
    '热点新闻': {
        'file': f'{advance_dir}/ex_rdxw.py',
        'description': '该示例需要需要能访问Google, 这是一个 热点新闻 的示例. ',
        'upload_path': f'{news_dir}/news_rdxw'
    },
    '我的订阅': {
        'file': f'{advance_dir}/ex_wddy.py',
        'description': '该示例需要需要能访问Google, 这是一个 我的订阅 的示例. ',
        'upload_path': f'{news_dir}/news_wddy'
    },
    '最新资讯': {
        'file': f'{advance_dir}/ex_zxzx.py',
        'description': '该示例需要需要能访问Google, 这是一个 最新资讯 的示例. ',
        'upload_path': f'{news_dir}/news_zxzx'
    },
    '新闻资讯': {
        'file': f'{advance_dir}/ex_xwzx.py',
        'description': '该示例需要需要能访问Google, 这是一个 新闻资讯 的示例. ',
        'upload_path': f'{news_dir}/news_xwzx'
    }
}


# 创建一个下拉菜单，让用户选择要运行的示例
selected_script = st.selectbox("选择要运行的示例:", list(examples.keys()))
st.markdown("**示例说明:**")
st.write(examples[selected_script]["description"])

# 创建一个空字典用于存储用户输入的参数
if 'script_params' not in st.session_state:
    st.session_state.script_params = {}

st.markdown("**参数面板**")
if selected_script == '每日资讯':
    # 新闻标题配置
    title1 = st.text_input('主标题', value='AI小报亭')
    title2 = st.text_input('副标题1', value='AI·大模型')
    title3 = st.text_input('副标题2', value='每日资讯')
    title4 = st.text_input('英文标题1', value='BREAKING NEWS')
    title5 = st.text_input('英文标题2', value='AI·LLM')
    if 'theme_keywords' not in st.session_state:
        st.session_state.theme_keywords = []
    col1, col2, col3 = st.columns([3, 5, 1.5])
    with col1:
        new_theme = st.text_input('新闻主题(模块的标题)', key="new_theme")
    with col2:
        new_keywords_input = st.text_input("新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)", key="new_keywords")
        new_keywords_input = new_keywords_input.replace('，', ',')
    with col3:
        st.write("")
        st.write("")
        if st.button("添加", key="add_button"):
            if new_theme and new_keywords_input:
                new_keywords = [kw.strip() for kw in new_keywords_input.split(',') if kw.strip()]
                st.session_state.theme_keywords.append({'theme': new_theme, 'keywords': new_keywords})
    for idx, item in enumerate(st.session_state.theme_keywords):
        st.markdown(f"**主题{idx + 1}**: {item['theme']}, **关键词**: {', '.join(item['keywords'])}")
    sentence = st.number_input('每条新闻摘要最多保留n句话(-1则全部保留, 0则不要摘要)', min_value=-1, value=-1)
    data_imag = st.text_input('底部的图片URL(为空则不显示)', value='')
    news_keywords = {}
    for theme_keywords in st.session_state.theme_keywords:
        news_keywords[theme_keywords['theme']] = theme_keywords['keywords']

    # 汇总所有新闻参数
    st.session_state.script_params = {
        'title1': title1,
        'title2': title2,
        'title3': title3,
        'title4': title4,
        'title5': title5,
        'news_keywords': news_keywords,
        'sentence': sentence,
        'data_imag': data_imag,
    }
elif selected_script == '平台精选':
    title = st.text_input('主标题', value='AI小报亭')
    keywords = st.text_input('新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)', value='AI')
    keywords = keywords.replace('，', ',')
    if keywords.strip():
        keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords = []
    st.session_state.script_params = {
        'title': title,
        'keywords': keywords,
    }
elif selected_script == '前沿资讯':
    title = st.text_input('主标题', value='AI小报亭')
    username = st.text_input('作者', value='RuMengAI')
    topic = st.text_input('话题', value='AIGC')
    keywords = st.text_input('新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)', value='AI')
    keywords = keywords.replace('，', ',')
    if keywords.strip():
        keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords = []
    st.session_state.script_params = {
        'title': title,
        'username': username,
        'topic': topic,
        'keywords': keywords,
    }
elif selected_script == '热点新闻':
    title = st.text_input('主标题', value='AI小报亭')
    subtitle = st.text_input('副标题', value='AIGC')
    username = st.text_input('作者', value='RuMengAI')
    keywords = st.text_input('新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)', value='AI')
    keywords = keywords.replace('，', ',')
    if keywords.strip():
        keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords = []
    st.session_state.script_params = {
        'title': title,
        'username': username,
        'subtitle': subtitle,
        'keywords': keywords,
    }
elif selected_script == '我的订阅':
    title = st.text_input('主标题', value='AI小报亭')
    username = st.text_input('作者', value='RuMengAI')
    keywords = st.text_input('新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)', value='AI')
    keywords = keywords.replace('，', ',')
    if keywords.strip():
        keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords = []
    st.session_state.script_params = {
        'title': title,
        'username': username,
        'keywords': keywords,
    }
elif selected_script == '最新资讯':
    title = st.text_input('主标题', value='AI小报亭')
    username = st.text_input('作者', value='RuMengAI')
    topic = st.text_input('话题', value='AIGC')
    keywords = st.text_input('新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)', value='AI')
    keywords = keywords.replace('，', ',')
    if keywords.strip():
        keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords = []
    st.session_state.script_params = {
        'title': title,
        'username': username,
        'topic': topic,
        'keywords': keywords,
    }
elif selected_script == '新闻资讯':
    title = st.text_input('主标题', value='AI小报亭')
    subtitle = st.text_input('副标题', value='精彩时刻, 不容错过')
    username = st.text_input('作者', value='RuMengAI')
    keywords = st.text_input('新闻关键词(用于搜索, 多个关键词之间用英文逗号分隔)', value='AI')
    keywords = keywords.replace('，', ',')
    if keywords.strip():
        keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords = []
    st.session_state.script_params = {
        'title': title,
        'subtitle': subtitle,
        'username': username,
        'keywords': keywords,
    }

blacklist = st.text_input('新闻网站黑名单(过滤指定网站新闻, 多个网站用英文逗号分隔)', value='aibase')
blacklist = blacklist.replace('，', ',')
if blacklist.strip():
    blacklist = [kw.strip() for kw in blacklist.split(',') if kw.strip()]
else:
    blacklist = []
qr_code = st.text_input('二维码链接', value='')
limit = st.number_input('每个主题保留的新闻数量', min_value=1, max_value=100, value=6)
days = st.number_input('限制新闻时间, 最近n天', min_value=1, max_value=100, value=7)
st.session_state.script_params.update({
    'qr_code': qr_code,
    'blacklist': blacklist,
    'limit': limit,
    'days': days
})


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
