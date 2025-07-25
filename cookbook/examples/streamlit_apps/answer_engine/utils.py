from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import streamlit as st
from agents import get_sage
from agno.agent.agent import Agent
from agno.utils.log import logger

# Handle import error for older agno versions
try:
    from agno.models.response import ToolExecution
except ImportError:
    # Create a fallback ToolExecution class for compatibility
    @dataclass
    class ToolExecution:
        tool_name: Optional[str] = None
        tool_args: Optional[Dict[str, Any]] = None
        result: Optional[str] = None
        metrics: Optional[Dict[str, Any]] = None


def add_message(
    role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None
) -> None:
    """Safely add a message to the session state."""
    if "messages" not in st.session_state or not isinstance(
        st.session_state["messages"], list
    ):
        st.session_state["messages"] = []
    st.session_state["messages"].append(
        {"role": role, "content": content, "tool_calls": tool_calls}
    )


def restart_agent():
    """Reset the agent and clear chat history."""
    logger.debug("---*--- Restarting agent ---*---")
    st.session_state["sage"] = None
    st.session_state["sage_session_id"] = None
    st.session_state["messages"] = []
    st.rerun()


def export_chat_history():
    """Export chat history as markdown."""
    if "messages" in st.session_state:
        chat_text = "# Sage - Chat History\n\n"
        for msg in st.session_state["messages"]:
            role_label = "🤖 Assistant" if msg["role"] == "assistant" else "👤 User"
            chat_text += f"### {role_label}\n{msg['content']}\n\n"
        return chat_text
    return ""


def display_tool_calls(tool_calls_container, tools: List[ToolExecution]):
    """Display tool calls in a streamlit container with expandable sections.

    Args:
        tool_calls_container: Streamlit container to display the tool calls
        tools: List of tool call dictionaries containing name, args, content, and metrics
    """
    try:
        with tool_calls_container.container():
            for tool_call in tools:
                tool_name = tool_call.tool_name or "Unknown Tool"
                tool_args = tool_call.tool_args or {}
                content = tool_call.result or ""
                metrics = tool_call.metrics or {}

                # Add timing information
                execution_time_str = "N/A"
                try:
                    if metrics:
                        execution_time = (
                            metrics["time"]
                            if isinstance(metrics, dict)
                            else metrics.time
                        )
                        if execution_time is not None:
                            execution_time_str = f"{execution_time:.2f}s"
                except Exception as e:
                    logger.error(f"Error displaying tool calls: {str(e)}")
                    pass

                with st.expander(
                    f"🛠️ {tool_name.replace('_', ' ').title()} ({execution_time_str})",
                    expanded=False,
                ):
                    # Show query with syntax highlighting
                    if isinstance(tool_args, dict) and "query" in tool_args:
                        st.code(tool_args["query"], language="sql")

                    # Display arguments in a more readable format
                    if tool_args and tool_args != {"query": None}:
                        st.markdown("**Arguments:**")
                        st.json(tool_args)

                    if content:
                        st.markdown("**Results:**")
                        try:
                            st.json(content)
                        except Exception as e:
                            st.markdown(content)

    except Exception as e:
        logger.error(f"Error displaying tool calls: {str(e)}")
        tool_calls_container.error("Failed to display tool results")


def sidebar_widget() -> None:
    """Display a sidebar with sample user queries for Sage."""
    with st.sidebar:
        st.markdown("#### 📜 Try me!")
        if st.button("💡 US Tariffs"):
            add_message(
                "user",
                "Tell me about the tariffs the US is imposing in 2025",
            )
        if st.button("🤔 Reasoning Models"):
            add_message(
                "user",
                "Which is a better reasoning model: o3-mini or DeepSeek R1?",
            )
        if st.button("🤖 Tell me about Agno"):
            add_message(
                "user",
                "Tell me about Agno: https://github.com/agno-agi/agno and https://docs.agno.com",
            )
        if st.button("⚖️ Impact of AI Regulations"):
            add_message(
                "user",
                "Evaluate how emerging AI regulations could influence innovation, privacy, and ethical AI deployment in the near future.",
            )

        st.markdown("---")
        st.markdown("#### 🛠️ Utilities")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat"):
                restart_agent()
        with col2:
            fn = "sage_chat_history.md"
            if "sage_session_id" in st.session_state:
                fn = f"sage_{st.session_state.sage_session_id}.md"
            if st.download_button(
                "💾 Export Chat",
                export_chat_history(),
                file_name=fn,
                mime="text/markdown",
            ):
                st.sidebar.success("Chat history exported!")


def session_selector_widget(agent: Agent, model_id: str) -> None:
    """Display a session selector in the sidebar."""
    if agent.storage:
        agent_sessions = agent.storage.get_all_sessions()

        session_options = []
        for session in agent_sessions:
            session_id = session.session_id
            session_name = (
                session.session_data.get("session_name", None)
                if session.session_data
                else None
            )
            display_name = session_name if session_name else session_id
            session_options.append({"id": session_id, "display": display_name})

        selected_session = st.sidebar.selectbox(
            "Session",
            options=[s["display"] for s in session_options],
            key="session_selector",
        )

        selected_session_id = next(
            s["id"] for s in session_options if s["display"] == selected_session
        )

        if st.session_state.get("sage_session_id") != selected_session_id:
            logger.info(
                f"---*--- Loading {model_id} run: {selected_session_id} ---*---"
            )

            try:
                new_agent = get_sage(
                    model_id=model_id,
                    session_id=selected_session_id,
                )

                st.session_state["sage"] = new_agent
                st.session_state["sage_session_id"] = selected_session_id

                st.session_state["messages"] = []

                selected_session_obj = next(
                    (s for s in agent_sessions if s.session_id == selected_session_id),
                    None,
                )

                if (
                    selected_session_obj
                    and selected_session_obj.memory
                    and "runs" in selected_session_obj.memory
                ):
                    seen_messages = set()

                    for run in selected_session_obj.memory["runs"]:
                        if "messages" in run:
                            for msg in run["messages"]:
                                msg_role = msg.get("role")
                                msg_content = msg.get("content")

                                if not msg_content or msg_role == "system":
                                    continue

                                msg_id = f"{msg_role}:{msg_content}"

                                if msg_id in seen_messages:
                                    continue

                                seen_messages.add(msg_id)

                                if msg_role == "assistant":
                                    tool_calls = None
                                    if "tool_calls" in msg:
                                        tool_calls = msg["tool_calls"]
                                    elif "metrics" in msg and msg.get("metrics"):
                                        tools = run.get("tools")
                                        if tools:
                                            tool_calls = tools

                                    add_message(msg_role, msg_content, tool_calls)
                                else:
                                    # For user and other messages
                                    add_message(msg_role, msg_content)

                        elif (
                            "message" in run
                            and isinstance(run["message"], dict)
                            and "content" in run["message"]
                        ):
                            user_msg = run["message"]["content"]
                            msg_id = f"user:{user_msg}"

                            if msg_id not in seen_messages:
                                seen_messages.add(msg_id)
                                add_message("user", user_msg)

                            if "content" in run and run["content"]:
                                asst_msg = run["content"]
                                msg_id = f"assistant:{asst_msg}"

                                if msg_id not in seen_messages:
                                    seen_messages.add(msg_id)
                                    add_message("assistant", asst_msg, run.get("tools"))

                st.rerun()
            except Exception as e:
                logger.error(f"Error switching sessions: {str(e)}")
                st.sidebar.error(f"Error loading session: {str(e)}")


def rename_session_widget(agent: Agent) -> None:
    """Rename the current session of the agent and save to storage."""
    container = st.sidebar.container()
    session_row = container.columns([3, 1], vertical_alignment="center")

    # Initialize session_edit_mode if needed.
    if "session_edit_mode" not in st.session_state:
        st.session_state.session_edit_mode = False

    with session_row[0]:
        if st.session_state.session_edit_mode:
            new_session_name = st.text_input(
                "Session Name",
                value=agent.session_name,
                key="session_name_input",
                label_visibility="collapsed",
            )
        else:
            st.markdown(f"Session Name: **{agent.session_name}**")

    with session_row[1]:
        if st.session_state.session_edit_mode:
            if st.button("✓", key="save_session_name", type="primary"):
                if new_session_name:
                    agent.rename_session(new_session_name)
                    st.session_state.session_edit_mode = False
                    container.success("Renamed!")
        else:
            if st.button("✎", key="edit_session_name"):
                st.session_state.session_edit_mode = True


def about_widget() -> None:
    """Display an about section in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown(
        """
        Sage is a cutting-edge answer engine that delivers real-time insights and in-depth analysis on a wide range of topics.

        Built with:
        - 🚀 Agno
        - 💫 Streamlit
        """
    )


CUSTOM_CSS = """
    <style>
    /* Main Styles */
    .main-title {
        text-align: center;
        background: linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: bold;
        padding: 1em 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2em;
    }
    .stButton button {
        width: 100%;
        border-radius: 20px;
        margin: 0.2em 0;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .chat-container {
        border-radius: 15px;
        padding: 1em;
        margin: 1em 0;
        background-color: #f5f5f5;
    }
    .sql-result {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1em;
        margin: 1em 0;
        border-left: 4px solid #FF4B2B;
    }
    .status-message {
        padding: 1em;
        border-radius: 10px;
        margin: 1em 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
    }
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        .chat-container {
            background-color: #2b2b2b;
        }
        .sql-result {
            background-color: #1e1e1e;
        }
    }
    </style>
"""
