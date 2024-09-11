import io
import os
import markdown2

from PIL import Image
from pdf2image import convert_from_path
from typing import Optional
from playwright.async_api import async_playwright


STYLE1 = """
    <style>
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 18px;
            line-height: 1.6;
            padding: 40px;
            background-color: #ffffff;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3, h4, h5, h6 {
            color: #1a237e; /* 更醒目的标题颜色 */
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 {
            font-size: 2.5em;
            border-bottom: 2px solid #1a237e;
            padding-bottom: 0.2em;
            background-color: #e8eaf6; /* 标题背景色 */
            padding: 10px;
            border-radius: 5px;
        }
        h2 {
            font-size: 2em;
            background-color: #e8eaf6; /* 标题背景色 */
            padding: 10px;
            border-radius: 5px;
        }
        h3 {
            font-size: 1.5em;
            background-color: #e8eaf6; /* 标题背景色 */
            padding: 10px;
            border-radius: 5px;
        }
        p {
            margin-bottom: 1.5em;
        }
        pre {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            overflow: auto;
            font-size: 0.9em;
        }
        code {
            background-color: #e9ecef;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        blockquote {
            border-left: 4px solid #1a237e;
            padding-left: 15px;
            margin-left: 0;
            color: #555;
            font-style: italic;
        }
        a {
            color: #3f51b5;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        ul, ol {
            margin-bottom: 1.5em;
        }
        li {
            margin-bottom: 0.5em;
        }
    </style>
"""


class ConvertToImage:
    def __init__(self, style_css=None):
        self.style_css = style_css if style_css else STYLE1

    async def html_to_image(self, html_content, output_image_path, use_phone: bool = False):
        """  """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            if use_phone:
                iphone_12 = p.devices['iPhone 12']
                context = await browser.new_context(**iphone_12)
            else:
                context = await browser.new_context()
            page = await context.new_page()
            await page.set_content(html_content)
            await page.wait_for_load_state('networkidle')
            image = await page.screenshot(full_page=True)
            await browser.close()

            with Image.open(io.BytesIO(image)) as img:
                img.save(output_image_path)

    async def text_to_image(self, text, output_image_path):
        """  """
        html_content = f"""
            <html>
                <head>
                    {self.style_css}
                </head>
                <body>
                    {text}
                </body>
            </html>
        """
        await self.html_to_image(html_content, output_image_path)

    async def markdown_to_image(self, markdown_text, output_image_path):
        """  """
        if not markdown_text:
            return
        html_content = markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "code-friendly"])
        full_html_content = f"""
            <html>
                <head>
                    {self.style_css}
                </head>
                <body>
                    {html_content}
                </body>
            </html>
        """
        await self.html_to_image(full_html_content, output_image_path)

    async def pdf_to_images(self, pdf_path, output_folder: Optional[str] = None):
        """  """
        output_folder = os.path.dirname(pdf_path) if not output_folder else output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f'page_{str(i+1).zfill(2)}.png')
            image.save(image_path, 'PNG')

    async def ppt_to_images(self, ppt_path, output_folder: Optional[str] = None):
        """  """
        import logging
        logging.getLogger("comtypes.client._code_cache").setLevel(logging.WARNING)
        from comtypes.client import CreateObject

        output_folder = os.path.dirname(ppt_path) if not output_folder else output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        ppt = CreateObject("PowerPoint.Application")
        ppt.Visible = 1
        presentation = ppt.Presentations.Open(ppt_path)
        ppt.WindowState = 2
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        for i, slide in enumerate(presentation.Slides):
            image_path = os.path.join(output_folder, f"slide_{str(i+1).zfill(2)}.png")
            slide.Export(image_path, "PNG")
        presentation.Close()
        ppt.Quit()
