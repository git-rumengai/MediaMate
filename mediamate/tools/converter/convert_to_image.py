import io
import markdown2

from playwright.async_api import async_playwright
from PIL import Image

from mediamate.tools.converter.styles import STYLE1


class ConvertToImage:
    def __init__(self, style_css=None):
        self.style_css = style_css if style_css else STYLE1

    async def html_to_image(self, html_content, output_image_path):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)
            await page.wait_for_load_state('networkidle')
            image = await page.screenshot(full_page=True)
            await browser.close()

            with Image.open(io.BytesIO(image)) as img:
                img.save(output_image_path)

    async def text_to_image(self, text, output_image_path):
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
