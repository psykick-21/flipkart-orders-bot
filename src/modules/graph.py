from langgraph.graph import StateGraph, END
from src.modules.struct import AgentState
from src.modules.runnables import agent_chain, update_scratchpad, click_node, type_text_node, scroll_node, wait, go_back_node, to_google_node, structure_orders, to_user_node
from src.modules.functions import agent_router
from langgraph.graph.state import CompiledStateGraph


def build_flipkart_scraper_graph()->CompiledStateGraph:
    """Builds the flipkart scraper graph.

    Returns:
        CompiledStateGraph: The compiled state graph.
    """

    builder = StateGraph(AgentState)

    builder.add_node('agent', agent_chain)
    builder.set_entry_point('agent')

    builder.add_node('update_scratchpad', update_scratchpad)
    builder.add_edge('update_scratchpad', 'agent')

    tools_dict = {
        'click':click_node,
        'type_text':type_text_node,
        'scroll':scroll_node,
        'wait':wait,
        'go_back':go_back_node,
        'to_google':to_google_node,
        'structure_orders': structure_orders,
        'to_user': to_user_node
    }

    for node_name, tool in tools_dict.items():
        builder.add_node(node_name, tool)
        builder.add_edge(node_name, 'update_scratchpad')

    builder.add_conditional_edges(
        'agent',
        agent_router,
        {
            '__end__': END,
            'CompleteTask': END,
            'structure_orders':'structure_orders',
            'click':'click',
            'type_text':'type_text',
            'scroll':'scroll',
            'wait':'wait',
            'go_back':'go_back',
            'to_google':'to_google',
            'to_user':'to_user'
        }
    )

    graph = builder.compile()

    return graph