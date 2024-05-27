from typing import Sequence, TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage
from playwright.async_api import Page
import operator
from langchain_core.pydantic_v1 import BaseModel, Field


class BBox(TypedDict):
    """Defines the datatype for bounding boxes"""
    x: float
    y: float
    text: str
    type: str
    ariaLabel: str


class AgentState(TypedDict):
    """Defines the datatype for the agent state"""
    page: Page
    input: str
    img: str
    bboxes: Sequence[BBox]
    scratchpad: Annotated[Sequence[BaseMessage],operator.add]
    bbox_descriptions: Sequence[str]
    tool_output: str


class CompleteTask(BaseModel):
    """Call this when the given task is completed."""
    answer: str = Field("The answer when the task is complete. 'COMPLETED' when the task is a navigation task, else it will be the content of the answer which the user requested for.")


class Order(TypedDict):
    """The structure of an order"""
    product_name: str = Field(description="The name of the product")
    product_price: int = Field(description="The price of the product")
    delivery_status: Literal[0,1,2,3] = Field(description="Delivery status of the product. If delivered, then 1. If not delivered, then 0. If the product is refunded, then 2. If cancelled, then 3.")


class OutputOrders(BaseModel):
    """Call this to save the extracted orders in a structured format. This will be used to save the orders in the database. MUST BE CALLED BEFORE CALLING CompleteTask."""
    orders: Sequence[Order] = Field(description="The list of orders")