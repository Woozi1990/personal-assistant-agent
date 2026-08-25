from langgraph.constants import START, END
from langgraph.graph import StateGraph

from agent.executor import Executor
from agent.model import Model
from agent.state import AgentState


class AgentGraph:
    def __init__(self, model: Model, executor: Executor):
        self._model = model
        self._executor = executor

    def build(self, checkpointer=None):
        graph = StateGraph(AgentState)

        graph.add_node("model", self._model.invoke)
        graph.add_node("executor", self._executor.invoke)

        graph.add_edge(START, "model")
        graph.add_conditional_edges(
            "model",
            self._route_after_model,
            {
                "executor": "executor",
                "end": END
            }
        )
        graph.add_edge("executor", "model")

        return graph.compile(checkpointer=checkpointer)

    @staticmethod
    def _route_after_model(state: AgentState):
        last_message = state["messages"][-1]

        if last_message.tool_calls:
            return "executor"
        return "end"
