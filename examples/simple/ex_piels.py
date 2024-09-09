from mediamate.tools.free_media.free_pexels import FreePexels


if __name__ == '__main__':
    fp = FreePexels()
    text = '小红书作为一个以分享生活方式和购物体验为核心的社交平台，吸引了大量年轻用户。而对于新入驻的小红书博主而言，快速增长粉丝是实现内容传播和品牌建设的重要基础。本文将整合多位专家的意见，提供一个全面的操作手册，以帮助新号博主有效提升关注度。'
    result = fp.get_photo(text, 3)
    print(result)

    result = fp.get_video(text, 3)
    print(result)
