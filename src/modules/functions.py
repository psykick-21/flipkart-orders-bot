from typing import Sequence, Literal
from playwright.async_api import Page
import asyncio
import platform
from src.modules.struct import BBox, AgentState, CompleteTask, OutputOrders


async def click(bbox_id:int, bboxes:Sequence[BBox], page: Page)->dict:
    """Used to click on a bounding box on a web page.

    Args:
        page (Page): The page to click on.
        bbox_id (int): The ID of the bounding box to click on.
        bboxes (Sequence[BBox]): The list of bounding boxes on the page.

    Returns:
        dict: The value as str with the message that the click was successful, with key 'tool_output'.
    """
    try:
        bbox = bboxes[bbox_id]
    except Exception as e:
        return f"Error occured. {e}"
    x, y = bbox["x"], bbox["y"]
    _ = await page.mouse.click(x, y)
    return {"tool_output": f"Clicked {bbox_id}"}


async def type_text(page: Page, bbox_id:int, type_content:str, bboxes:Sequence[BBox])->dict:
    """Used to type text in a web page.

    Args:
        page (Page): The page to type on.
        bbox_id (int): The ID of the bounding box to type on.
        type_content (str): The content to type.
        bboxes (Sequence[BBox]): The list of bounding boxes on the page.

    Returns:
        dict: The value as str with the message that the text was typed successfully, with key 'tool_output'.
    """
    bbox = bboxes[bbox_id]
    x, y = bbox["x"], bbox["y"]
    await page.mouse.click(x, y)
    select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
    await page.keyboard.press(select_all)
    await page.keyboard.press("Backspace")
    await page.keyboard.type(type_content)
    await page.keyboard.press("Enter")
    return {"tool_output": f"Typed {type_content} and submitted"}

# Union[Literal['WINDOW'],int]
async def scroll(page: Page, target: str, direction:Literal['up','down'], bboxes: Sequence[BBox])->dict:
    """Used to scroll up or down in a web page.
    If the complete window needs to be scrolled, then the target is 'WINDOW'. Else the target is the ID of the bounding box to scroll in.

    Args:
        page (Page): The page to scroll in.
        target str: The target to scroll in. 'WINDOW' if the complete window needs to be scrolled, else the ID of the bounding box to scroll in.
        direction (Literal['up','down']): The direction to scroll in.
        bboxes (Sequence[BBox]): The list of bounding boxes on the page.

    Returns:
        dict: The value as str with the message that the scroll was successful, with key 'tool_output'.
    """
    if target == "WINDOW":
        scroll_amount = 600
        scroll_direction = (
            -scroll_amount if direction == "up" else scroll_amount
        )
        await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
    else:
        scroll_amount = 200
        target_id = int(target)
        bbox = bboxes[target_id]
        x, y = bbox["x"], bbox["y"]
        scroll_direction = (
            -scroll_amount if direction == "up" else scroll_amount
        )
        await page.mouse.move(x, y)
        await page.mouse.wheel(0, scroll_direction)

    return {"tool_output": f"Scrolled {direction} in {'WINDOW' if target == 'WINDOW' else 'element'} with ID {target}."}


async def wait()->dict:
    """Used to wait for 5 seconds. This is generally used to wait for the page to load.

    Returns:
        dict: The value as str with the message that the wait is complete, with key 'tool_output'.
    """
    sleep_time = 5
    await asyncio.sleep(sleep_time)
    return {"tool_output": f"Waited for {sleep_time}s."}


async def go_back(page: Page)->dict:
    """Used to navigate back a page.

    Args:
        page (Page): The page to navigate back in.

    Returns:
        dict: The value as str with the message that the navigation is complete, with key 'tool_output'.
    """
    await page.go_back()
    return {"tool_output": f"Navigated back a page to {page.url}."}


async def to_google(page: Page)->dict:
    """Used to navigate to google.com.

    Args:
        page (Page): The page to navigate to google.com in.

    Returns:
        dict: The value as str with the message that the navigation is complete, with key 'tool_output'.
    """
    await page.goto("https://www.google.com/")
    return {"tool_output": "Navigated to google.com."}


async def to_user(query:str)->dict:
    """Used to hand over the control to the user. In any case where a user intervention is needed, call this function.

    Args:
        query (str): The query to ask the user. Examples: 1. 'Can you please login to the website?', 2. 'I seem to be stuck. Can you help me navigate?', 3. 'I cannot download the file. Can you download it for me?'

    Returns:
        dict: The value as str with the response from the user, with key 'tool_output'.
    """
    display_text = f"{query}. Enter 'exit' to exit: "
    response = input(display_text)
    response_text = f"AI: {query}\nUser: {response}"
    return {'tool_output':response_text}


def agent_router(state: AgentState):
    """Routing function for the agent"""
    message = state.get('scratchpad')[-1]
    if message.additional_kwargs:
        function_name = message.additional_kwargs['function_call']['name']
        if function_name == OutputOrders.__name__:
            return 'structure_orders'
        elif function_name == CompleteTask.__name__:
            return '__end__'
        else:
            return function_name
    else:
        return '__end__'