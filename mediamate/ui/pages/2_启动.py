import os
import streamlit as st
import subprocess
import datetime
import json
import yaml
from mediamate.config import config
from mediamate.utils.common import extract_json
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


def run_script(placeholder, script_name, button_label):
    """运行指定的脚本并返回结果"""
    with placeholder:
        script_to_run = os.path.join(examples_dir, script_name)
        result = subprocess.run(["python", script_to_run], capture_output=True, text=True, encoding='utf-8')
        log_entry = f"返回码: {result.returncode}\n"
        log_entry += f"标准输出:\n{result.stdout}\n"
        log_entry += f"标准错误:\n{result.stderr}\n"

        # 保存日志到 session_state
        if 'log_entries' not in st.session_state:
            st.session_state.log_entries = {}
        st.session_state.log_entries[button_label] = log_entry
    return result


script_mapping = {
    '小红书创作者中心': 'ex_xhs_creator.py',
    '小红书主页': 'ex_xhs_home.py',
    '抖音创作者中心': 'ex_dy_creator.py',
    '抖音主页': 'ex_dy_home.py'
}
if 'button_state' not in st.session_state:
    st.session_state.button_state = {key: False for key in script_mapping.keys()}


def forbid_button(button_label):
    st.session_state.button_state[button_label] = True


st.markdown("""
### 运行主程序
1. 首次启动需要打开页面并登录
2. 执行内容由配置项决定
3. 配置中"无头模式"设置为True则不会显示界面
4. 配置中"自动上传"设置为True, 运行"创作者中心"会自动上传内容
> 注意: 自动上传会将upload目录下所有生成的内容逐个上传
""")
for button_label, script_name in script_mapping.items():
    placeholder_script = st.empty()
    if st.button(button_label, key=button_label, on_click=forbid_button, args=(button_label, ), disabled=st.session_state.button_state[button_label]):
        with st.spinner(f"正在运行 {button_label}..."):
            result = run_script(placeholder_script, script_name, button_label)
        st.session_state.button_state[button_label] = False
        st.rerun()
# 显示日志内容
if 'log_entries' in st.session_state:
    for button_label, log_entry in st.session_state.log_entries.items():
        with st.expander(f"{button_label} 的运行日志", expanded=False):
            st.code(log_entry)


st.markdown('\n\n\n---\n\n\n')

st.markdown('### 运行模板示例, 所有的示例结果可以直接上传到平台')
simple_dir = f'{os.path.dirname(config.PROJECT_DIR)}/examples/simple'
advance_dir = f'{os.path.dirname(config.PROJECT_DIR)}/examples/advance'
# 定义要运行的示例列表及其说明
examples = {
    '简单示例': {
        'file': f'{simple_dir}/ex_demo.py',
        'description': '这是一个简单的示例, 会自动下载一张图片, 运行成功后可以在 data/upload 文件夹下查看.',
        'upload_path': f'{news_dir}/demo'
    },
    '生成LOGO': {
        'file': f'{simple_dir}/ex_logo.py',
        'description': '该示例需要配置302AI, 利用大模型生成LOGO图片, 运行成功后可以在 data/upload 文件夹下查看.',
        'upload_path': f'{news_dir}/logo_gpt'
    },
    '宠物图片': {
        'file': f'{simple_dir}/ex_photo.py',
        'description': '该示例需要配置302AI, 利用大模型生成小猫的图片, 运行成功后可以在 data/upload 文件夹下查看.',
        'upload_path': f'{news_dir}/photo_gpt'
    },
    '简单新闻': {
        'file': f'{simple_dir}/ex_news.py',
        'description': '该示例需要需要能访问Google, 根据输入的关键词自动获取相关新闻并转为图片. ',
        'upload_path': f'{news_dir}/image_news'
    },
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
    },
    '多媒体识别': {
        'file': f'{simple_dir}/ex_media.py',
        'description': '该示例需要配置302AI, 1. 利用大模型识别一组图片并生成发表的图文描述. 2. 利用大模型识别视频文本并生成发表的图文描述. 运行成功后可以在 data/upload 文件夹下查看. ',
    },
    'GDP排行变动榜': {
        'file': f'{advance_dir}/ex_chart/ex_bar_race.py',
        'description': '该示例需要需要能访问Google, 自动生成GDP排行变动榜视频. ',
    },
    'GDP走势': {
        'file': f'{advance_dir}/ex_chart/ex_line_trend.py',
        'description': '该示例需要需要能访问Google, 自动生成历史GDP走势变动视频. ',
    },
}


selected_script = st.selectbox("选择要运行的示例:", list(examples.keys()))
st.markdown("**示例说明:**")
st.write(examples[selected_script]["description"])
if 'script_params' not in st.session_state:
    st.session_state.script_params = {}

st.markdown("**参数输入(仅支持新闻模板)**")
with st.form(key="parameter_form"):
    param = st.text_area("请输入参数 (JSON 格式)", value="{}", height=100)
    submit_button = st.form_submit_button(label="提交参数")
if submit_button:
    try:
        json_params = json.loads(extract_json(param))
        st.write('这是提交参数: ')
        st.json(json_params)
        st.session_state.script_params.update(json_params)
    except json.JSONDecodeError:
        st.error("JSON 输入格式有问题，请检查后重试。")


if st.button('运行示例', key='run_example'):
    placeholder = st.empty()
    script_to_run = examples[selected_script]["file"]
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
