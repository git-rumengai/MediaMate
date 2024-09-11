import os
import shutil
import random
import pandas as pd
import plotly.graph_objects as go

from mediamate.tools.chart_video.base import BaseChat
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__name__)


class BarRace(BaseChat):
    def generate_frames(self):
        """  """
        df_data = pd.read_csv(self.filename)
        # 将日期列转换为 datetime 对象
        df_data['date'] = pd.to_datetime(df_data['date'])
        # 获取所有日期
        dates = sorted(df_data['date'].unique())
        items = df_data.columns[1:].tolist()
        colors = {item: f'#{random.randint(0, 0xFFFFFF):06x}' for item in items}
        avatars = {}
        for item in items:
            avatar = self.generate_ui_avatar(item, size=64, background_color=colors[item][1:])
            if avatar:
                avatars[item] = self.pil_image_to_base64(avatar)

        # 创建动画帧
        frames = []
        for date in dates:
            # 提取该日期的数据
            date_data = df_data[df_data['date'] == date].drop(columns=['date'])
            date_data_sum = date_data.sum().reset_index()
            date_data_sum.columns = ['Key', 'Value']
            # 按死亡人数降序排序
            date_data_sum = date_data_sum.sort_values(by='Value', ascending=True)
            x_pos = round(-0.06 + (len(items) * 0.004), 4)
            x_pos = min(x_pos, -0.02)
            y_size = round(0.6 - (len(items) * 0.005), 4)
            y_size = max(y_size, 0.2)
            images = [
                dict(
                    source=avatars[key],
                    x=x_pos,
                    y=key,
                    xref='paper',
                    yref='y',
                    sizex=1,
                    sizey=y_size,
                    xanchor="left",
                    yanchor="middle"
                )
                for key, value in zip(date_data_sum['Key'], date_data_sum['Value']) if key in avatars
            ]
            annotations = [
                go.layout.Annotation(
                    text=date.strftime('%Y-%m-%d'),
                    xref='paper',
                    yref='paper',
                    x=0.8,
                    y=0.2,
                    xanchor='right',
                    yanchor='bottom',
                    showarrow=False,
                    font=dict(size=38)
                )
            ]
            frame = go.Frame(
                data=[
                    go.Bar(
                        y=date_data_sum['Key'],
                        x=date_data_sum['Value'],
                        orientation='h',
                        marker=dict(
                            color=[colors[key] for key in date_data_sum['Key']],
                        ),
                        textposition='outside',
                        textfont=dict(color='black'),
                        texttemplate='<b>%{y}: %{x:,.0f}</b>',  # 使用 <b> 标签加粗文本
                        text=[f"{key} {value:,.0f}" for key, value in zip(date_data_sum['Key'], date_data_sum['Value'])],
                    )
                ],
                name=date.strftime('%Y-%m-%d'),  # 使用日期格式作为帧名称
                layout=go.Layout(
                    annotations=annotations,
                    images=images
                )
            )
            frames.append(frame)

        fig = go.Figure(frames[0].data)
        fig.update_layout(frames[0].layout)
        # 设置图表布局
        fig.update_layout(
            margin=dict(l=100, b=150),
            title={
                'text': self.chart_video_config.get('title'),  # 标题文本
                'y': 0.95,  # 标题的垂直位置（0 到 1 之间的值）
                'x': 0.5,  # 标题的水平位置（0 到 1 之间的值）
                'xanchor': 'center',  # 标题的水平对齐方式
                'yanchor': 'top'  # 标题的垂直对齐方式
            },
            xaxis=dict(
                showgrid=True,  # 显示 x 轴网格线
                gridcolor='rgba(0, 0, 0, 0.2)',  # 设置 x 轴网格线颜色为半透明黑色
                gridwidth=1,  # 设置 x 轴网格线宽度
                griddash='dot',  # 设置 x 轴网格线为虚线
                tickfont=dict(size=24),
                range=[df_data[items].min().min(), df_data[items].max().max() * 1.1],
            ),
            yaxis=dict(
                showline=True,  # 不显示Y轴线
                showticklabels=False,  # 不显示Y轴标签
                ticktext=[],  # 清除Y轴刻度文字
                showgrid=True,  # 显示 y 轴网格线
                gridcolor='rgba(0, 0, 0, 0.2)',  # 设置 y 轴网格线颜色为半透明黑色
                gridwidth=1,  # 设置 y 轴网格线宽度
                griddash='dot'  # 设置 y 轴网格线为虚线
            ),
            plot_bgcolor=self.chart_video_config.get('plot_bgcolor'),  # 设置图形区域的背景色
            paper_bgcolor=self.chart_video_config.get('paper_bgcolor'),  # # 设置整个图形的背景色
            font_color='black',
        )
        fig.frames = frames
        html_file = f"{self.filename.rsplit('.')[0]}.html"
        fig.write_html(html_file)
        frames_dir = os.path.join(self.data_path, 'frames')
        shutil.rmtree(frames_dir, ignore_errors=True)
        os.makedirs(frames_dir, exist_ok=True)
        logger.info(f'共有数据帧: {len(frames)} 帧')
        for i, frame in enumerate(frames):
            logger.info(i)
            fig.update(data=frame.data, layout=frame.layout)
            fig.write_image(f'{frames_dir}/frame_{i:04d}.png', width=self.width, height=self.height, scale=2)
