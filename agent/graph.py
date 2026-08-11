from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt

from agent.prompts import SYSTEM_PROMPT
from agent.state import AgentState
from agent.tool_selector import ToolSelector


def build_graph(
        llm: ChatOpenAI,
        tools: list,
        checkpointer,
        confirmation_handler
):
    tool_selector = ToolSelector(llm=llm)

    async def select_tools_node(state: AgentState):
        messages = state["messages"]
        pending_action = state.get("pending_action")

        if pending_action is not None:
            last_messages = messages[-1]

            if isinstance(last_messages, HumanMessage):
                decision = confirmation_handler.classify(
                    user_input=last_messages.content,
                    pending_action=pending_action,
                )
                print("Pending action decision:", decision.decision)

                if decision.decision !="other":
                    return {
                        "confirmation_decision": decision.decision,
                    }

        selected_names = tool_selector.select(
            messages=state["messages"],
            tools=tools,
        )
        selected_names = [
            name for name in selected_names if name != "send_email"
        ]
        print("selected_names:", selected_names)

        return {
            "selected_tool_names": selected_names,
            "forced_tool_name": None,
            "confirmation_decision":None
        }
    def route_after_select_tools(state: AgentState):
        decision = state.get("confirmation_decision")

        if decision == "confirm":
            return "confirm"

        if decision == "modify":
            return "modify"

        if decision == "cancel":
            return "cancel"

        return "model"

    async def model_node(state: AgentState):
        selected_names = state["selected_tool_names"]

        selected_tools = [
            tool for tool in tools if tool.name in selected_names
        ]

        forced_tool_name = state.get("forced_tool_name")
        if forced_tool_name is not None:
            llm_with_tools = llm.bind_tools(
                selected_tools,
                tool_choice=forced_tool_name
            )
        else:
            llm_with_tools = llm.bind_tools(selected_tools)

        response = await llm_with_tools.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"]
        ])

        return {
            "messages": [response],
            "forced_tool_name": None,
        }

    def confirmation_node(state: AgentState):
        pending_action = state.get("pending_action")

        if pending_action is None:
            return {}

        user_response = interrupt({
            "type": "confirmation",
            "action": pending_action.action,
            "data": pending_action.data
        })

        decision = confirmation_handler.classify(
            user_input=user_response,
            pending_action=pending_action,
        )
        print("Confirmation decision:", decision.decision)

        return {
            "messages": [
                HumanMessage(content=user_response)
            ],
            "requires_confirmation": False,
            "confirmation_response": user_response,
            "confirmation_decision": decision.decision,
        }

    def route_after_confirmation(state: AgentState):
        decision = state.get("confirmation_decision")

        if decision == "confirm":
            return "confirm"
        if decision == "modify":
            return "modify"
        if decision == "cancel":
            return "cancel"
        return "other"

    def route_after_tools(state: AgentState):
        if state.get("requires_confirmation", False):
            return "confirmation"
        return "model"

    def confirm_action_node(state: AgentState):
        pending_action = state.get("pending_action")

        return {
            "selected_tool_names": [
                pending_action.action
            ],
            "forced_tool_name": pending_action.action,
            "requires_confirmation": False,
            "confirmation_decision": None,
            "confirmation_response": None,
        }

    def modify_action_node(state: AgentState):
        return {
            "selected_tool_names": [
                "update_draft"
            ],
            "forced_tool_name": "update_draft",
            "requires_confirmation": False,
            "confirmation_decision": None,
            "confirmation_response": None,
        }

    def cancel_action_node(state: AgentState):
        return {
            "messages": [
                AIMessage(content="已取消当前待确认的操作。")
            ],
            "pending_action": None,
            "requires_confirmation": False,
            "confirmation_decision": None,
            "confirmation_response": None,
        }

    def other_action_node(state: AgentState):
        return {
            "requires_confirmation": False,
            "confirmation_decision": None,
            "confirmation_response": None,
        }

    graph = StateGraph(AgentState)

    graph.add_node("select_tools", select_tools_node)
    graph.add_node("model", model_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("confirmation", confirmation_node)

    graph.add_node("confirm_action", confirm_action_node)
    graph.add_node("modify_action", modify_action_node)
    graph.add_node("cancel_action", cancel_action_node)
    graph.add_node("other_action", other_action_node)

    graph.add_edge(START, "select_tools")
    graph.add_conditional_edges(
        "select_tools",
        route_after_select_tools,
        {
            "confirm": "confirm_action",
            "modify": "modify_action",
            "cancel": "cancel_action",
            "model": "model",
        }
    )

    graph.add_edge("confirm_action", "model")
    graph.add_edge("modify_action", "model")
    graph.add_edge("cancel_action", END)
    graph.add_edge("other_action", "select_tools")

    graph.add_conditional_edges("model", tools_condition)
    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "confirmation": "confirmation",
            "model": "model"
        }
    )
    graph.add_conditional_edges(
        "confirmation",
        route_after_confirmation,
        {
            "confirm": "confirm_action",
            "modify": "modify_action",
            "cancel": "cancel_action",
            "other": "other_action"
        }
    )

    return graph.compile(checkpointer=checkpointer)
