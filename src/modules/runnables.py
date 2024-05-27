from langchain_openai import ChatOpenAI
from langchain_core.runnables import chain
from src.modules.helper import mark_page
from src.modules.struct import AgentState, CompleteTask, OutputOrders
from src.modules.helper import read_file
from typing import Callable
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.prompts.image import ImagePromptTemplate
from langchain_core.runnables import Runnable
from src.modules.functions import click, type_text, scroll, wait, go_back, to_google, to_user
import json


# <-------------------- AGENT RUNNABLES -------------------->

@chain
async def annotate(state: AgentState)->AgentState:
    """Captures the screenshot of the page and annotates the elements on the page. Uses the mark_page helper function. To be used as a runnable inside the agent chain. All the relevant information is stored in the state.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        AgentState: The state of the agent with the annotated page screenshot and the bounding boxes.
    """
    marked_page = await mark_page.with_retry().ainvoke(state["page"])
    return {**state, **marked_page}


@chain
def format_descriptions(state: AgentState)->AgentState:
    """Formats the descriptions of the bounding boxes and returns the state with the formatted descriptions. To be used as a runnable inside the agent chain. All the relevant information is stored in the state.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        AgentState: The state of the agent with the formatted descriptions of the bounding boxes.
    """
    labels = []
    for i, bbox in enumerate(state["bboxes"]):
        text = bbox.get("ariaLabel","")
        if not text.strip():
            text = bbox["text"]
        el_type = bbox.get("type","")
        labels.append(f'{i} (<{el_type}/>): "{text}"')
    bbox_descriptions = "Valid Bounding Boxes:\n" + "\n".join(labels)
    return {**state, "bbox_descriptions": bbox_descriptions}


system_prompt = read_file("src/prompts/system_prompt.txt")


prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_prompt),
    HumanMessagePromptTemplate.from_template('{input}'),
    MessagesPlaceholder(variable_name='scratchpad', optional=True),
    HumanMessagePromptTemplate(prompt=[
        ImagePromptTemplate(input_variables=['img'], template={'url': 'data:image/png;base64,{img}'}),
        PromptTemplate(input_variables=['bbox_descriptions'], template='{bbox_descriptions}'),
    ])
])


functions_list = [click, type_text, scroll, wait, go_back, to_google, to_user]
llm = ChatOpenAI(model="gpt-4o", max_tokens=4096).bind_functions(functions_list+[CompleteTask,OutputOrders])


def create_agent_with_prompt(runnable:Runnable)->Callable:
    @chain
    async def func(state:AgentState)->AgentState:
        result = await runnable.ainvoke(state)
        if not result.tool_calls and (
            not result.content
            or isinstance(result.content,list)
            and not result.content[0].get('text')
        ):
            messages = [AIMessage(content="Seems like my last response did not have any tool calls or content. I need to check my response", additional_kwargs={})]
            print(f"This was the invokation result:\n{result}")
            return {**state, 'scratchpad': messages}
        
        else:
            return {**state, 'scratchpad': [result]}
    return func


agent = create_agent_with_prompt(runnable = prompt|llm)
agent_chain = annotate | format_descriptions | agent


# <-------------------- HELPER RUNNABLES -------------------->

@chain
def update_scratchpad(state: AgentState)->AgentState:
    """Update the scratchpad with the latest message post the tool execution. The output of the tool will be formatted as a SystemMessage, to be consumed by the agent chain. This helper function will be used in the graph as a node, which will be connected to the output of the tool execution. The output of this node will go into the agent chain.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        AgentState: The state of the agent with the latest message in the scratchpad.
    """
    message = state.get('scratchpad')[-1]
    tool_output = state.get('tool_output')
    if message.additional_kwargs:
        # tool_call_id = message.id
        return_message = SystemMessage(content=tool_output) #tool_call_id=tool_call_id
    else:
        return_message = HumanMessage(content="No tool was called in your last action. Please recheck your last action.")
    return {**state, "scratchpad": [return_message]}


# <-------------------- TOOL RUNNABLES -------------------->

@chain
async def type_text_node(state: AgentState)->dict:
    """This is the node executable for the type_text tool. It will be used as a node in the graph, which will call the type_text function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the type_text function.
    """
    message = state['scratchpad'][-1]
    ai_kwargs = eval(message.additional_kwargs['function_call']['arguments'])
    state_kwargs = {
        'page': state['page'],
        'bboxes': state['bboxes']
    }
    result = await type_text(**ai_kwargs, **state_kwargs)
    return result


@chain
async def click_node(state: AgentState)->dict:
    """This is the node executable for the click tool. It will be used as a node in the graph, which will call the click function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the click function.
    """
    message = state['scratchpad'][-1]
    ai_kwargs = eval(message.additional_kwargs['function_call']['arguments'])
    state_kwargs = {
        'page': state['page'],
        'bboxes': state['bboxes']
    }
    result = await click(**ai_kwargs, **state_kwargs)
    return result


@chain
async def scroll_node(state: AgentState)->dict:
    """This is the node executable for the scroll tool. It will be used as a node in the graph, which will call the scroll function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the scroll function.
    """
    message = state['scratchpad'][-1]
    ai_kwargs = eval(message.additional_kwargs['function_call']['arguments'])
    state_kwargs = {
        'page': state['page'],
        'bboxes': state['bboxes']
    }
    result = await scroll(**ai_kwargs, **state_kwargs)
    return result


@chain
async def go_back_node(state: AgentState)->dict:
    """This is the node executable for the go_back tool. It will be used as a node in the graph, which will call the go_back function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the go_back function.
    """
    result = await go_back(state['page'])
    return result


@chain
async def to_google_node(state: AgentState)->dict:
    """This is the node executable for the to_google tool. It will be used as a node in the graph, which will call the to_google function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the to_google function.
    """
    result = await to_google(state['page'])
    return result


@chain
async def structure_orders(state: AgentState)->dict:
    """This is the node executable for the structure_orders tool. It will be used as a node in the graph, which will call the structure_orders function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the structure_orders function.
    """
    message = state.get('scratchpad')[-1]
    orders = eval(message.additional_kwargs['function_call']['arguments'])
    with open('orders.json','w') as f:
        json.dump(orders,f)
    return {'tool_output': 'Orders saved successfully'}


@chain
async def to_user_node(state: AgentState)->dict:
    """This is the node executable for the to_user tool. It will be used as a node in the graph, which will call the to_user function when the agent requires it.

    Args:
        state (AgentState): The state of the agent.

    Returns:
        dict: The result of the to_user function.
    """
    message = state['scratchpad'][-1]
    ai_kwargs = eval(message.additional_kwargs['function_call']['arguments'])
    response = await to_user(ai_kwargs)
    return response