import re
import json
from typing import Optional, Tuple
from playwright.async_api import Page

from mediamate.utils.const import DEFAULT_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.platforms.base import BaseLocator


logger = log_manager.get_logger(__file__)


class DyDownloader(BaseLocator):
    """ 下载数据 """
    async def ensure_page(self, page: Page) -> Page:
        """ 页面重新加载, 所有步骤要重新执行 """
        home_loading = page.locator(self.parser.get_xpath('common home_loading'))
        if await home_loading.is_visible():
            logger.info('页面加载中...')
            await home_loading.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='hidden')
        page_loading = page.locator(self.parser.get_xpath('common page_loading'))
        if await page_loading.is_visible():
            logger.info('页面加载中...')
            await page_loading.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='hidden')
        page_wrong = page.locator(self.parser.get_xpath('common page_wrong'))
        if await page_wrong.is_visible():
            logger.info('页面出错, 重新加载...')
            await page.reload(timeout=DEFAULT_URL_TIMEOUT)
        tips_warning = page.locator(self.parser.get_xpath('common tips_warning'))
        if await page_wrong.is_visible():
            logger.info('页面警告提示...')
            await tips_warning.click()
            await tips_warning.wait_for(state='hidden')
        return page

    async def click_manage(self, page: Page, num: int = 10) -> Optional[Page]:
        """ 作品管理 """
        logger.info('即将进入: 作品管理')
        steps = ('home', 'home text_datacenter', 'manage', 'manage work', 'manage all_work')
        await self.ensure_step_page(page, steps)

        video_list = await self.get_visible_locators(page, 'manage video_list')
        text_video = await self.get_visible_locator(page, 'manage text_video')
        text_video_text = await text_video.inner_text()
        match = re.search(r'共\s*([0-9]+)\s*个作品', text_video_text)
        if match:
            total = match.group(1)
            num = min(num, int(total))
            logger.info(f'共有 {total} 个作品, 下载 {num} 个作品')
        else:
            num = -1
            logger.info(f'未匹配到作品数量, 下载全部作品')
        loading_end = page.locator(self.parser.get_xpath('manage loading_end'))
        if num == -1:
            count = 0
            while True:
                count += 1
                # 滚动页面，确保新内容可以加载
                await self.scroll(page)
                await self.wait_medium(page)  # 适当的延迟，让页面加载更多内容
                if await loading_end.is_visible():
                    logger.info("找到了 '没有更多作品' 的提示")
                    break
                else:
                    logger.info(f'滑动页面第 {count} 次, 直至获取全部数据')
        else:
            count = 0
            while True:
                count += 1
                video_cards = await video_list.all()
                if len(video_cards) < num:
                    # 滚动页面，确保新内容可以加载
                    await self.scroll(page)
                    await self.wait_medium(page)  # 适当的延迟，让页面加载更多内容
                else:
                    logger.info(f'滑动页面第 {count} 次, 直至获取{num}条数据')
                    break

            video_cards = await video_list.all()
            result = []
            for video in video_cards:
                cover = await self.get_child_visible_locator(video, 'manage video_list _cover')
                title = await self.get_child_visible_locator(video, 'manage video_list _title')
                dt = await self.get_child_visible_locator(video, 'manage video_list _datetime')
                view = await self.get_child_visible_locator(video, 'manage video_list _view')
                comment = await self.get_child_visible_locator(video, 'manage video_list _comment')
                like = await self.get_child_visible_locator(video, 'manage video_list _like')

                cover_style = await cover.get_attribute('style')
                cover_url = cover_style.split('url("')[1].split('")')[0] if cover_style else ''
                title_text = await title.inner_text()
                title_text = title_text.strip() if title_text else ''
                dt_text = await dt.inner_text()
                dt_text = dt_text.strip() if dt_text else ''
                view_text = await view.inner_text()
                view_text = view_text.strip() if view_text else ''
                comment_text = await comment.inner_text()
                comment_text = comment_text.strip() if comment_text else ''
                like_text = await like.inner_text()
                like_text = like_text.strip() if like_text else ''
                item = {
                        '封面': cover_url,
                        '标题': title_text,
                        '日期': dt_text,
                        '浏览数': view_text,
                        '评论数': comment_text,
                        '点赞数': like_text
                }
                logger.info(f'时间: {dt_text}, 观看数: {view_text}, 评论数: {comment_text}, 点赞数: {like_text}, 标题: {title_text}')
                result.append(item)
            with open(f'{self.data_path.download_personal}/作品管理.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            # 保存数据
            return page

    async def click_datacenter(self, page: Page) -> Optional[Page]:
        """ 数据中心, 账户不一定有 """
        logger.info('即将进入: 数据中心')
        steps = ('home', )
        await self.ensure_step_page(page, steps)
        datacenter = await self.get_locator(page, 'home text_datacenter')
        if not await datacenter.is_visible():
            logger.info('没有找到数据中心菜单, 可能需要手动开通')
            return page

        steps = ('home text_datacenter', 'datacenter', 'datacenter analysis')
        await self.ensure_step_page(page, steps)

        # 获取数据表现
        summary_list = await self.get_visible_locators(page, 'home summary_list')
        summary_list_all = await summary_list.all()
        summary = []
        for i in summary_list_all:
            key = await self.get_child_visible_locator(i, 'home summary_list _key')
            value = await self.get_child_visible_locator(i, 'home summary_list _value')
            summary.append({key: value})
        with open(f'{self.data_path.download_personal}/数据表现.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        # 相关热门数据
        result = {}
        for type_list in ['topic_list', 'video_list']:
            all_data = await self.get_visible_locators(page, f'datacenter {type_list}')
            all_data = await all_data.all()
            result[type_list] = []
            for data in all_data:
                cover = await self.get_child_visible_locator(data, f'datacenter {type_list} _cover')
                title = await self.get_child_visible_locator(data, f'datacenter {type_list} _title')
                view = await self.get_child_visible_locator(data, f'datacenter {type_list} _view')
                play = await self.get_child_visible_locator(data, f'datacenter {type_list} _play')
                comment = await self.get_child_visible_locator(data, f'datacenter {type_list} _comment')
                like = await self.get_child_visible_locator(data, f'datacenter {type_list} _like')

                cover_url = await cover.get_attribute('src')
                title_text = await title.inner_text()
                title_text = title_text.strip() if title_text else ''
                view_text = await view.inner_text()
                view_text = view_text.strip() if view_text else ''
                play_text = await play.inner_text()
                play_text = play_text.strip() if play_text else ''
                comment_text = await comment.inner_text()
                comment_text = comment_text.strip() if comment_text else ''
                like_text = await like.inner_text()
                like_text = like_text.strip() if like_text else ''
                logger.info(f'热度: {view_text}, 播放数: {play_text}, 评论数: {comment_text}, 点赞数: {like_text}')
                result[type_list].append({
                    '封面': cover_url,
                    '标题': title_text,
                    '热度': view_text,
                    '播放数': play_text,
                    '评论数': comment_text,
                    '点赞数': like_text
                    })
        with open(f'{self.data_path.download_personal}/热门数据.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        return page

    async def click_creative_guidance(self, page: Page, words: Tuple[str, ...] = ()) -> Optional[Page]:
        """ 创作灵感数据 """
        logger.info('即将进入: 创作灵感')
        steps = ('home', 'home text_datacenter', 'creative', 'creative guidance', 'creative guidance insight')
        await self.ensure_step_page(page, steps)

        if not words:
            logger.info(f'无下载标签, 默认下载: 财经')
            return page

        showmore = await self.get_visible_locator(page, 'creative guidance showmore')
        await showmore.click()

        title_list = await self.get_visible_locators(page, 'creative guidance title_list')
        all_nodes = await title_list.all()
        all_child_nodes = {}
        for node in all_nodes:
            inner_nodes = await self.get_child_visible_locators(node, 'creative guidance title_list inner_title_list')
            inner_nodes = await inner_nodes.all()
            for inner_node in inner_nodes:
                name = await inner_node.inner_text()
                all_child_nodes[name.strip()] = inner_node

        result = {}
        for word in words:
            if word not in all_child_nodes.keys():
                logger.info(f'词条不存在: {word}')
                continue
            await all_child_nodes[word].click()
            data_list = await self.get_visible_locators(page, 'creative guidance data_list')
            data_list = await data_list.all()
            result[word] = []
            for data in data_list:
                cover = await self.get_child_visible_locator(data, f'creative guidance data_list _cover')
                title = await self.get_child_visible_locator(data, f'creative guidance data_list _title')
                view = await self.get_child_visible_locator(data, f'creative guidance data_list _view')
                play = await self.get_child_visible_locator(data, f'creative guidance data_list _play')
                comment = await self.get_child_visible_locator(data, f'creative guidance data_list _comment')
                like = await self.get_child_visible_locator(data, f'creative guidance data_list _like')

                cover_url = await cover.get_attribute('src')
                title_text = await title.inner_text()
                title_text = title_text.strip() if title_text else ''
                view_text = await view.inner_text()
                view_text = view_text.strip() if view_text else ''
                play_text = await play.inner_text()
                play_text = play_text.strip() if play_text else ''
                comment_text = await comment.inner_text()
                comment_text = comment_text.strip() if comment_text else ''
                like_text = await like.inner_text()
                like_text = like_text.strip() if like_text else ''
                logger.info(f'热度: {view_text}, 播放数: {play_text}, 评论数: {comment_text}, 点赞数: {like_text}')
                result[word].append({
                    '封面': f'https:{cover_url}',
                    '标题': title_text,
                    '热度': view_text,
                    '播放数': play_text,
                    '评论数': comment_text,
                    '点赞数': like_text
                    })

        with open(f'{self.data_path.download_personal}/创作灵感.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        return page

    async def click_billboard(self, page: Page, words: Tuple[str, ...] = ()) -> Optional[Page]:
        """ 抖音排行榜 """
        logger.info('即将进入: 抖音排行榜')
        steps = ('home', 'home text_datacenter', 'creative', 'creative billboard')
        await self.ensure_step_page(page, steps)

        if not words:
            logger.info(f'无下载标签')
            return page

        title_list = await self.get_visible_locators(page, 'creative billboard title_list')
        all_child_nodes = {}
        all_nodes = await title_list.all()
        for node in all_nodes:
            name = await node.inner_text()
            all_child_nodes[name.strip()] = node

        result = {}
        for word in words:
            if word not in all_child_nodes.keys():
                logger.info(f'词条不存在: {word}')
                continue
            logger.info(f'下载类别: {word}')
            await all_child_nodes[word].click()
            thead_list = await self.get_visible_locators(page, 'creative billboard thead_list')
            tbody_list = await self.get_visible_locators(page, 'creative billboard tbody_list')

            thead = await thead_list.all()
            titles = []
            for th in thead:
                title = await th.inner_text()
                titles.append(title.strip())
            tbody = await tbody_list.all()
            result[word] = []
            for tr in tbody:
                tds = await tr.locator('td').all()
                if len(tds) != len(titles):
                    continue
                item = {}
                for index, td in enumerate(tds):
                    if titles[index] == '封面':
                        content = await td.locator('img').get_attribute('src')
                    else:
                        content = await td.inner_text()
                    item[titles[index]] = content
                result[word].append(item)
        with open(f'{self.data_path.download_personal}/抖音排行榜.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        logger.info('回到首页')
        back_home = await self.get_visible_locator(page, 'creative billboard back_home')
        await back_home.click()
        return page


__all__ = ['DyDownloader']
