import os
import shutil
import random
import pandas as pd
import plotly.graph_objects as go

from mediamate.tools.chart_video.base import BaseChat
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__name__)


class LineTrend(BaseChat):
    def generate_frames(self):
        # 读取数据
        df_data = pd.read_csv(self.filename)
        df_data = df_data.fillna(0)
        df_data['date'] = pd.to_datetime(df_data['date'])
        df_data['date'] = df_data['date'].dt.strftime('%Y-%m-%d')
        dates = sorted(df_data['date'].unique())
        items = df_data.columns[1:].tolist()
        colors = {item: f'#{random.randint(0, 0xFFFFFF):06x}' for item in items}
        avatars = {}
        for item in items:
            avatar = self.generate_ui_avatar(item, size=64, background_color=colors[item][1:])
            if avatar:
                avatars[item] = self.pil_image_to_base64(avatar)

        frames = []
        max_y = df_data[items].max().max() * 1.1
        total = len(dates)
        for index, date in enumerate(dates):
            date_data = df_data[df_data['date'] <= date]
            # 创建折线数据
            lines = []
            images = []
            annotations = [
                go.layout.Annotation(
                    text=date,
                    xref='paper',
                    yref='paper',
                    x=0.02,
                    y=1.0,
                    showarrow=False,
                    font=dict(size=38)
                )
            ]
            for item in items:
                lines.append(go.Scatter(
                    x=date_data['date'],
                    y=date_data[item],
                    mode='lines+markers',
                    line=dict(color=colors.get(item, 'black')),
                    name=f'{item}: {date_data[item].iloc[-1]}',
                ))
                # 图片的每一步都走前面
                if index < total - 1:
                    x_value = index + 1
                    y_value = df_data[item].iloc[x_value]
                else:
                    x_value = index
                    y_value = df_data[item].iloc[x_value]
                images.append(
                    dict(
                        source=avatars[item],
                        x=x_value/total,
                        y=y_value / max_y,      # date_data.iloc[-1][item]
                        xref='paper',
                        yref='paper',
                        sizex=0.05,
                        sizey=0.05,
                        xanchor='left',
                        yanchor='bottom',
                    )
                )
            frame = go.Frame(
                data=lines,
                name=date,
                layout=go.Layout(
                    images=images,
                    annotations=annotations,
                )
            )
            frames.append(frame)
        # 创建初始图表
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
            legend=dict(
                x=0.02,
                y=0.9,
                xanchor='left',
                yanchor='top',
                font=dict(size=18)
            ),
            xaxis=dict(
                tickformat='%Y-%m-%d',
                showgrid=True,  # 显示 x 轴网格线
                gridcolor='rgba(0, 0, 0, 0.1)',  # 设置 x 轴网格线颜色为半透明黑色
                gridwidth=1,  # 设置 x 轴网格线宽度
                griddash='dot',  # 设置 x 轴网格线为虚线
                tickfont=dict(size=24),
                range=[min(dates), max(dates)],
            ),
            yaxis=dict(
                showline=True,  # 显示Y轴线
                showticklabels=True,  # 显示Y轴标签
                showgrid=True,  # 显示 y 轴网格线
                gridcolor='rgba(0, 0, 0, 0.1)',  # 设置 y 轴网格线颜色为半透明黑色
                gridwidth=1,  # 设置 y 轴网格线宽度
                griddash='dot',  # 设置 y 轴网格线为虚线
                tickfont=dict(size=24),
                range=[df_data[items].min().min(), df_data[items].max().max() * 1.1]
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


if __name__ == '__main__':
    data_path = r'/data/upload/xiaohongshu/RuMengAI/line_trend'
    cv = LineTrend(data_path).generate_frames()
