import os
import streamlit as st
import yaml
import copy
from datetime import datetime
from typing import List, Optional
from mediamate.config import config
from dotenv import dotenv_values
from mediamate.utils.log_manager import log_manager

"""
点赞, 评论, 收藏

"""

logger = log_manager.get_logger(__file__)


def env_file_handler(file_name: str, data: Optional[dict] = None) -> dict:
    """  """
    result = {}
    if data:
        result = data
        with open(file_name, 'w', encoding='utf-8') as env_file:
            for key, value in data.items():
                env_file.write(f"{key}={value}\n")
        logger.info(f'数据已成功保存: {file_name}')
    else:
        if os.path.exists(file_name):
            result = dotenv_values(file_name, encoding='utf-8')
            if not result:
                result = {}
                logger.warning(f'文件为空: {file_name}')
        else:
            logger.error(f'文件不存在: {file_name}')
    return result


def yaml_file_handler(file_name, data: Optional[dict] = None) -> dict:
    """  """
    result = {}
    if data:
        result = data
        with open(file_name, 'w', encoding='utf-8') as yaml_file:
            yaml.dump(data, yaml_file, indent=4, allow_unicode=True)
        logger.info(f'数据已成功保存: {file_name}')
    else:
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as yaml_file:
                result = yaml.safe_load(yaml_file)
                if not result:
                    logger.warning(f'文件为空: {file_name}')
                    result = {}
        else:
            logger.error(f'文件不存在: {file_name}')
    return result


def config_file_handler(file_name, data: Optional[dict] = None) -> dict:
    if file_name.endswith('.env'):
        return env_file_handler(file_name, data)
    elif file_name.endswith('.yaml'):
        return yaml_file_handler(file_name, data)
    raise ValueError(f'不支持的文件类型: {file_name}')


env_template = f'{config.PROJECT_DIR}/static/config/.template.env'
project_env_config = f'{os.path.dirname(config.PROJECT_DIR)}/.env'
media_template = f'{config.PROJECT_DIR}/static/config/.template.media.yaml'
project_media_config = f'{os.path.dirname(config.PROJECT_DIR)}/.media.yaml'


# 定义一个全局字典来存储状态
if 'env_config' not in st.session_state:
    st.session_state.env_config = {}
    if os.path.exists(project_env_config):
        st.session_state.env_config = env_file_handler(project_env_config)
    if not st.session_state.env_config:
        st.session_state.env_config = env_file_handler(env_template)

if 'media_config' not in st.session_state:
    st.session_state.media_config = {}
    if os.path.exists(project_media_config):
        st.session_state.media_config = yaml_file_handler(project_media_config)
    if not st.session_state.media_config:
        st.session_state.media_config = yaml_file_handler(media_template)


def create_buttons(button_content: List[str]):
    """ 根据输出列表创建 button """
    buttons = []
    container = st.container()
    with container:
        st.markdown(
            """
            <style>
            .stButton button {
                margin: auto;
                display: block;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        cols = st.columns([1] * len(button_content))
        for col, content in zip(cols, button_content):
            with col:
                button = st.button(content, key=content)
            buttons.append(button)
    return buttons


def display_media(media_name: str):
    """  """
    media_configs = st.session_state.media_config['media'][media_name]
    new_media_configs = []
    st.markdown(f'**共有 {len(media_configs)} 个 {media_name} 账户配置**')
    multi_actions = ['点赞', '收藏', '评论']
    for index, media_config in enumerate(media_configs):
        st.markdown(f'### 第 {index + 1} 个 {media_name} 账户配置')
        unique_key = 'account'
        media_config[unique_key] = st.text_input('账户数据保存名称, 多个账户名称不能重复', value=media_config.get(unique_key, ''), key=f'{media_name}_{unique_key}_{index}')
        unique_key = 'headless'
        media_config[unique_key] = st.radio('无头模式启动浏览器, False会打开浏览器界面', [False, True], index=media_config.get(unique_key, False), key=f'{media_name}_{unique_key}_{index}')
        unique_key = 'proxy'
        media_config[unique_key] = st.text_input('账户的代理地址, 输入 close 强制关闭代理', value=media_config.get(unique_key, ''), key=f'{media_name}_{unique_key}_{index}')

        st.markdown(f'**{media_name} 的创作者中心配置**')
        if media_name == 'xhs':
            st.markdown(f'**{media_name} 的创作者中心**')
            unique_key = 'upload'
            upload = media_config['creator'].get(unique_key, False)
            media_config['creator'][unique_key] = st.radio(f'是否自动上传 {media_name} 视频/图文', [False, True], index=upload, key=f'{media_name}_creator_{unique_key}_{index}')
            unique_key = 'download'
            download = media_config['creator'].get(unique_key, [])
            if download:
                download_text = ', '.join(download)
                input_download = st.text_input('下载灵感笔记数据, 多个主题用逗号分割', value=download_text, key=f'{media_name}_explore_{unique_key}_{index}')
                input_download = input_download.replace('，', ',')
                media_config['creator'][unique_key] = [i.strip() for i in input_download.split(',')]
            st.markdown(f'**{media_name} 的主页操作配置**')
            unique_key = 'comment'
            comment = media_config['home']['operate'].get(unique_key, False)
            media_config['home']['operate'][unique_key] = st.radio('自动回复评论, 回复内容由"default_comment_reply_message"或"ai_prompt_content_comment_reply"决定', [False, True], index=comment, key=f'{media_name}_operate_{unique_key}_{index}')
            unique_key = 'ids'
            ids = media_config['home']['download'].get(unique_key, [])
            if ids:
                ids_text = ', '.join(ids)
                input_ids = st.text_input('下载某人小红书账号, 输入小红书号, 多个账号用逗号分割', value=ids_text, key=f'{media_name}_download_{unique_key}_{index}')
                input_ids = input_ids.replace('，', ',')
                media_config['home']['download'][unique_key] = [i.strip() for i in input_ids.split(',')]
            st.markdown(f'**{media_name} 的浏览配置**')
            unique_key = 'topics'
            topics = media_config['home']['explore'].get(unique_key)
            if topics:
                topics_text = ', '.join(topics)
                input_topics = st.text_input('浏览的主题, 小红书主页主题, 多个主题用逗号分割', value=topics_text, key=f'{media_name}_explore_{unique_key}_{index}')
                input_topics = input_topics.replace('，', ',')
                media_config['home']['explore'][unique_key] = [i.strip() for i in input_topics.split(',')]
            unique_key = 'actions'
            actions = media_config['home']['explore'].get(unique_key, [])
            if actions:
                media_config['home']['explore'][unique_key] = st.multiselect('浏览内容执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定', options=multi_actions, default=actions[:1], key=f'{media_name}_explore_{unique_key}_{index}')
            unique_key = 'mention'
            mention = media_config['home']['explore'].get(unique_key)
            if mention:
                mention_text = ', '.join(mention)
                input_mention = st.text_input('评论时@某人, 小红书用户名, 多个用户名用逗号分割', value=mention_text, key=f'{media_name}_explore_{unique_key}_{index}')
                input_mention = input_mention.replace('，', ',')
                media_config['home']['explore'][unique_key] = [i.strip() for i in input_mention.split(',')]
            unique_key = 'times'
            times = int(media_config['home']['explore'].get(unique_key, 0))
            if times:
                media_config['home']['explore'][unique_key] = st.number_input('每个主题浏览 n 篇内容', value=times, min_value=0, max_value=20, step=1, key=f'{media_name}_explore_{unique_key}_{index}')

            st.markdown(f'**{media_name} 的评论配置**')
            unique_key = 'ids'
            ids = media_config['home']['comment'].get(unique_key)
            if ids:
                ids_text = ', '.join(ids)
                input_ids = st.text_input('指定要浏览的用户小红书号', value=ids_text, key=f'{media_name}_comment_{unique_key}_{index}')
                input_ids = input_ids.replace('，', ',')
                media_config['home']['comment'][unique_key] = [i.strip() for i in input_ids.split(',')]
            unique_key = 'times'
            times = int(media_config['home']['comment'].get(unique_key, 0))
            if times:
                media_config['home']['comment'][unique_key] = st.number_input('查看每个用户的 n 条内容', value=times, min_value=0, max_value=20, step=1, key=f'{media_name}_comment_{unique_key}_{index}')
            unique_key = 'actions'
            actions = media_config['home']['comment'].get(unique_key, [])
            if actions:
                media_config['home']['comment'][unique_key] = st.multiselect('浏览内容执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定', options=multi_actions, default=actions[:1], key=f'{media_name}_comment_{unique_key}_{index}')
            unique_key = 'mention'
            mention = media_config['home']['comment'].get(unique_key)
            if mention:
                mention_text = ', '.join(mention)
                input_mention = st.text_input('评论时@某人, 小红书用户名, 多个用户名用逗号分割', value=mention_text, key=f'{media_name}_comment_{unique_key}_{index}'); input_mention = input_mention.replace('，', ',')
                media_config['home']['comment'][unique_key] = [i.strip() for i in input_mention.split(',')]
        elif media_name == 'dy':
            st.markdown(f'**{media_name} 的创作者中心**')
            unique_key = 'upload'
            upload = media_config['creator'].get(unique_key, False)
            media_config['creator'][unique_key] = st.radio(f'是否自动上传 {media_name} 视频/图文', [False, True], index=upload, key=f'{media_name}_creator_{unique_key}_{index}')

            st.markdown(f'**{media_name} 的创作者中心, 下载数据**')
            unique_key = 'manage'
            manage = media_config['creator']['download'].get(unique_key, False)
            media_config['creator']['download'][unique_key] = st.radio('下载作品管理页数据', [False, True], index=manage, key=f'{media_name}_creator_{unique_key}_{index}')
            unique_key = 'datacenter'
            datacenter = media_config['creator']['download'].get(unique_key, False)
            media_config['creator']['download'][unique_key] = st.radio('下载数据中心页数据, 有的账户没有, 需自行开通', [False, True], index=datacenter, key=f'{media_name}_creator_{unique_key}_{index}')
            unique_key = 'creative_guidance'
            creative_guidance = media_config['creator']['download'].get(unique_key, [])
            if creative_guidance:
                creative_guidance_text = ', '.join(creative_guidance)
                input_creative_guidance = st.text_input('下载创作灵感页数据, 多个主题用逗号分割', value=creative_guidance_text, key=f'{media_name}_explore_{unique_key}_{index}')
                input_creative_guidance = input_creative_guidance.replace('，', ',')
                media_config['creator']['download'][unique_key] = [i.strip() for i in input_creative_guidance.split(',')]
            unique_key = 'billboard'
            billboard = media_config['creator']['download'].get(unique_key, [])
            if billboard:
                billboard_text = ', '.join(billboard)
                input_billboard = st.text_input('下载创作灵感页数据, 多个主题用逗号分割', value=billboard_text, key=f'{media_name}_explore_{unique_key}_{index}')
                input_billboard = input_billboard.replace('，', ',')
                media_config['creator']['download'][unique_key] = [i.strip() for i in input_billboard.split(',')]

            st.markdown(f'**{media_name} 的主页操作配置**')
            unique_key = 'comment'
            comment = media_config['home']['operate'].get(unique_key, False)
            media_config['home']['operate'][unique_key] = st.radio('自动回复评论, 回复内容由"default_comment_reply_message"或"ai_prompt_content_comment_reply"决定', [False, True], index=comment, key=f'{media_name}_operate_{unique_key}_{index}')
            unique_key = 'chat'
            chat = media_config['home']['operate'].get(unique_key, False)
            media_config['home']['operate'][unique_key] = st.radio('自动处理私聊, 评论内容由"default_chat_reply_message"或"ai_prompt_content_chat_reply"决定', [False, True], index=chat, key=f'{media_name}_operate_{unique_key}_{index}')

            unique_key = 'ids'
            ids = media_config['home']['download'].get(unique_key, [])
            if ids:
                ids_text = ', '.join(ids)
                input_ids = st.text_input('下载某人抖音账号数据, 输入抖音号, 多个账号用逗号分割', value=ids_text, key=f'{media_name}_download_{unique_key}_{index}')
                input_ids = input_ids.replace('，', ',')
                media_config['home']['download'][unique_key] = [i.strip() for i in input_ids.split(',')]

            st.markdown(f'**{media_name} 的浏览配置**')
            unique_key = 'topics'
            topics = media_config['home']['discover'].get(unique_key)
            if topics:
                topics_text = ', '.join(topics)
                input_topics = st.text_input('浏览的榜单, 抖音首页榜单有的账户可能没有, 输入"首页"则首页随机刷, 多个榜单用逗号分割', value=topics_text, key=f'{media_name}_discover_{unique_key}_{index}')
                input_topics = input_topics.replace('，', ',')
                media_config['home']['discover'][unique_key] = [i.strip() for i in input_topics.split(',')]
            unique_key = 'actions'
            actions = media_config['home']['discover'].get(unique_key, [])
            if actions:
                media_config['home']['discover'][unique_key] = st.multiselect('浏览时执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定', options=multi_actions, default=actions[:1], key=f'{media_name}_discover_{unique_key}_{index}')
            unique_key = 'mention'
            mention = media_config['home']['discover'].get(unique_key)
            if mention:
                mention_text = ', '.join(mention)
                input_mention = st.text_input('如果需要评论, 评论时提及某人, 抖音号, 多个抖音号用逗号分割', value=mention_text, key=f'{media_name}_discover_{unique_key}_{index}')
                input_mention = input_mention.replace('，', ',')
                media_config['home']['discover'][unique_key] = [i.strip() for i in input_mention.split(',')]
            unique_key = 'times'
            times = int(media_config['home']['discover'].get(unique_key, 0))
            if times:
                media_config['home']['discover'][unique_key] = st.number_input('每个榜单点击 n 个视频', value=times, min_value=0, max_value=20, step=1, key=f'{media_name}_discover_{unique_key}_{index}')
            st.markdown(f'**{media_name} 的评论配置**')
            unique_key = 'ids'
            ids = media_config['home']['comment'].get(unique_key)
            if ids:
                ids_text = ', '.join(ids)
                input_ids = st.text_input('浏览指定用户视频, 抖音号, 多个账号用逗号分割', value=ids_text, key=f'{media_name}_comment_{unique_key}_{index}')
                input_ids = input_ids.replace('，', ',')
                media_config['home']['comment'][unique_key] = [i.strip() for i in input_ids.split(',')]
            unique_key = 'times'
            times = int(media_config['home']['comment'].get(unique_key, 0))
            if times:
                media_config['home']['comment'][unique_key] = st.number_input('每个用户浏览 n 个视频', value=times, min_value=0, max_value=20, step=1, key=f'{media_name}_comment_{unique_key}_{index}')
            unique_key = 'actions'
            actions = media_config['home']['comment'].get(unique_key, [])
            if actions:
                media_config['home']['comment'][unique_key] = st.multiselect('浏览时执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定', options=multi_actions, default=actions[:1], key=f'{media_name}_comment_{unique_key}_{index}')
            unique_key = 'mention'
            mention = media_config['home']['comment'].get(unique_key)
            if mention:
                mention_text = ', '.join(mention)
                input_mention = st.text_input('评论时@某人, 抖音号, 多个抖音号用逗号分割', value=mention_text, key=f'{media_name}_comment_{unique_key}_{index}'); input_mention = input_mention.replace('，', ',')
                media_config['home']['comment'][unique_key] = [i.strip() for i in input_mention.split(',')]
            unique_key = 'shuffle'
            shuffle = media_config['home']['comment'].get(unique_key, False)
            media_config['home']['comment'][unique_key] = st.radio(f'随机选择浏览用户的视频, False则顺序浏览', [False, True], index=upload, key=f'{media_name}_comment_{unique_key}_{index}')
            st.markdown(f'**{media_name} 的私聊配置**')
            unique_key = 'ids'
            ids = media_config['home']['follow'].get(unique_key)
            if ids:
                ids_text = ', '.join(ids)
                input_ids = st.text_input('浏览指定用户视频, 抖音号, 多个账号用逗号分割', value=ids_text, key=f'{media_name}_follow_{unique_key}_{index}')
                input_ids = input_ids.replace('，', ',')
                media_config['home']['follow'][unique_key] = [i.strip() for i in input_ids.split(',')]
            unique_key = 'times'
            times = int(media_config['home']['follow'].get(unique_key, 0))
            if times:
                media_config['home']['follow'][unique_key] = st.number_input('每个用户浏览 n 个视频', value=times, min_value=0, max_value=20, step=1, key=f'{media_name}_follow_{unique_key}_{index}')
            unique_key = 'batch'
            batch = int(media_config['home']['follow'].get(unique_key, 0))
            if batch:
                media_config['home']['follow'][unique_key] = st.number_input('每个视频评论区选择 n 个好友', value=batch, min_value=0, max_value=20, step=1, key=f'{media_name}_follow_{unique_key}_{index}')
            unique_key = 'shuffle'
            shuffle = media_config['home']['follow'].get(unique_key, False)
            media_config['home']['follow'][unique_key] = st.radio(f'随机选择浏览用户的视频, False则顺序浏览', [False, True], index=upload, key=f'{media_name}_follow_{unique_key}_{index}')

        st.markdown('**通用配置**')
        unique_key = 'default_comment_message'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('评论别人作品默认消息', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_comment_reply_message'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('回复别人对自己的作品评论的默认消息', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_chat_message'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('主动私聊别人默认消息', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_chat_reply_message'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('回复别人私聊默认消息', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_data_length'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认获取数据长度', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_reply_chat_length'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认回复私聊数量', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_reply_comment_length'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认回复评论数量', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_reply_comment_days'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认回复最近 n 天的图文', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_reply_comment_times'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认回复最近 n 篇图文', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_video_wait'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认上传视频最长等待时间min', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'default_image_wait'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_input('默认上传图片最长等待时间min', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')

        st.markdown('**只有配置了302AI的APIKEY才会启用AI功能**')
        unique_key = 'ai_prompt_content_filter'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_area('浏览内容时判断是否过滤, 通过提示词让AI回复True保留, False过滤', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'ai_prompt_user_filter'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_area('通过评论判断是否为目标用户, 通过提示词让AI回复True保留, False过滤. True则主动发送私聊消息 default_chat_message', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'ai_prompt_content_comment'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_area('根据作品标题,内容+前5条有效评论作为参考. 发表评论', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'ai_prompt_content_comment_reply'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_area('根据作品标题,内容+用户评论作为参考. 回复对方', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')
        unique_key = 'ai_prompt_content_chat_reply'
        if media_config['common'].get(unique_key):
            media_config['common'][unique_key] = st.text_area('如果有人发消息, 根据最后5条对话内容作为参考, 回复对方', value=media_config['common'].get(unique_key, ''), key=f'{media_name}_common_{unique_key}_{index}')


        new_media_configs.append(media_config)
    st.session_state.media_config['media'][media_name] = new_media_configs


def media_button_handler(media_name: str):
    """  """
    with st.expander(f'点击展开/折叠 {media_name} 配置'):
        media_save_button, media_add_button, media_default_button = create_buttons([f'保存 {media_name} 配置', f'新增 {media_name} 账户', f'恢复默认 {media_name} 配置'])
        if media_save_button:
            if os.path.exists(project_media_config):
                temp_media_config = yaml_file_handler(project_media_config)
            else:
                temp_media_config = yaml_file_handler(media_template)
            temp_media_config['media'][media_name] = copy.deepcopy(st.session_state.media_config['media'][media_name])
            yaml_file_handler(project_media_config, temp_media_config)
            st.sidebar.write(f'保存配置: {media_name}')
            st.sidebar.write(st.session_state.media_config)
        if media_add_button:
            temp_media_config = yaml_file_handler(media_template)
            temp_config = copy.deepcopy(temp_media_config['media'][media_name][0])
            # 确保新增用户名不重复
            accounts = [i['account'] for i in st.session_state.media_config['media'][media_name]]
            if temp_config['account'] in accounts:
                temp_config['account'] += f'_{int(datetime.now().timestamp())}'
            st.session_state.media_config['media'][media_name].append(temp_config)

            st.sidebar.write(f'新增配置: {media_name}')
            st.sidebar.write(st.session_state.media_config)
        if media_default_button:
            temp_media_config = yaml_file_handler(media_template)
            st.session_state.media_config['media'][media_name] = copy.deepcopy(temp_media_config['media'][media_name])
            st.sidebar.write(f'恢复默认配置: {media_name}')
            st.sidebar.write(st.session_state.media_config)
        display_media(media_name)


media_button_handler('xhs')
media_button_handler('dy')


def display_env():
    """  """
    env_config = st.session_state.env_config
    unique_key = 'MM__DATA'
    env_config[unique_key] = st.text_input('项目数据保存名称, 项目同级目录下', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__FIXED_PROXY'
    env_config[unique_key] = st.text_input('固定代理 https://...', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__PROXY_NAME'
    env_config[unique_key] = st.text_input('代理池名称, 只支持快代理(KDL)', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__PROXY_BACKUP'
    env_config[unique_key] = st.text_input('代理池中代理的数量', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__KDL_USERNAME'
    env_config[unique_key] = st.text_input('KDL USERNAME', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__KDL_PASSWORD'
    env_config[unique_key] = st.text_input('KDL PASSWORD', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__KDL_SECRETKEY'
    env_config[unique_key] = st.text_input('KDL SECRETKEY', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__302__APIKEY'
    env_config[unique_key] = st.text_input('302AI SECRETKEY', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__302__LLM'
    env_config[unique_key] = st.text_input('默认使用的302AI模型', value=env_config.get(unique_key, ''), key=unique_key)
    unique_key = 'MM__PEXELS'
    env_config[unique_key] = st.text_input('PEXELS SECRETKEY', value=env_config.get(unique_key, ''), key=unique_key)
    st.session_state.env_config = env_config


with st.expander("点击展开/折叠 env 配置"):
    env_save_button, env_default_button = create_buttons(['保存 env 配置', '恢复默认 env 配置'])
    if env_save_button:
        env_file_handler(project_env_config, st.session_state.env_config)
        st.sidebar.write(f'保存配置: env')
        st.sidebar.write(st.session_state.env_config)
    if env_default_button:
        st.session_state.env_config = env_file_handler(env_template)
        st.sidebar.write(f'加载默认配置: env')
        st.sidebar.write(st.session_state.env_config)
    display_env()
