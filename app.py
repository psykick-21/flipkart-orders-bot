import os
from dotenv import load_dotenv
from src.modules.graph import build_flipkart_scraper_graph
from IPython import display
from playwright.async_api import async_playwright
from src.modules.helper import call_agent, read_file
import asyncio

load_dotenv()

os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_PROJECT'] = 'flipkart-scraping'

graph = build_flipkart_scraper_graph()

async def main():

    browser = await async_playwright().start()
    browser = await browser.chromium.launch(headless=False, args=None)
    page = await browser.new_page()
    _ = await page.goto("https://www.google.com")

    user_input = read_file("src/prompts/user_prompt.txt")

    await call_agent(user_input, page, graph, max_steps=100)

if __name__=="__main__":
    asyncio.run(main())