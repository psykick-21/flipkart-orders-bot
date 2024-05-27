from langchain_core.runnables import chain
import base64
import asyncio
from playwright.async_api import Page
from langgraph.graph.state import CompiledStateGraph


def read_file(filepath:str)->str:
    """Reads the file and returns the content.

    Args:
        filepath (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(filepath) as f:
        return f.read()


mark_page_script = read_file("src/scripts/mark_page.js")


@chain
async def mark_page(page: Page)->dict:
    """Annotates the elements on the page and returns the screenshot with the bounding boxes.

    Args:
        page (Page): The page to mark.

    Returns:
        dict: The screenshot of the page with the bounding boxes.
    """
    await page.evaluate(mark_page_script)
    for _ in range(10):
        try:
            bboxes = await page.evaluate("markPage()")
            break
        except:
            asyncio.sleep(3)
    screenshot = await page.screenshot()
    await page.evaluate("unmarkPage()")
    return {
        "img": base64.b64encode(screenshot).decode(),
        "bboxes": bboxes,
    }


async def call_agent(question: str, page: Page, graph: CompiledStateGraph, max_steps:int=10):
    """Calls the agent with the given question, page and graph.

    Args:
        question (str): The question to ask.
        page (Page): The page to interact with.
        graph (CompiledStateGraph): The compiled state graph.
        max_steps (int, optional): The maximum number of steps to run the agent. Defaults to 10.
    """

    event_stream = graph.astream(
        input = {
            'page':page,
            'input':question,
            'scratchpad':[],
        },
        config={
            'recursion_limit':max_steps
        }
    )

    async for event in event_stream:
        
        if "agent" in event:
            message = event['agent']['scratchpad'][-1]
            print("<","-"*10,"AI MESSAGE","-"*10,">\n")
            print(message.content)
            if message.additional_kwargs:
                function_call = message.additional_kwargs['function_call']
                function_name = function_call['name']
                arguments = function_call['arguments']
                print(f"Function call:\nName = {function_name}\nArguments = {arguments}\n\n")
        
        elif "update_scratchpad" in event:
            message = event['update_scratchpad']['scratchpad'][-1]
            print("<","-"*10,"SCRATCHPAD UPDATE","-"*10,">\n")
            print(message.content,'\n')
        
        else:
            pass