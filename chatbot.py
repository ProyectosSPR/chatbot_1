# your_module.py
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from psycopg import connect
import os
import logging
import db


@tool
def execute_sql_query(query: str):
    """
    Ejecuta una consulta SQL en la base de datos PostgreSQL y devuelve el resultado.
    """

    try:
        with connect(os.getenv("DATABASE_URL")) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()
                return str(result) if result else "No hay resultados."
    except Exception as e:
        return f"Error al ejecutar SQL: {str(e)}"


def chatbot_with_postgres(thread_id: str, query: str, prompt: str, model_name: str = "gpt-4o-mini", temperature: float = 0):
    if db.checkpointer is None:
        logging.warning("Checkpointer no inicializado, intentando iniciar base de datos manualmente.")
        db.init_db()

    tools = [execute_sql_query]
    model = ChatOpenAI(model_name=model_name, temperature=temperature)

    prompt_template = ChatPromptTemplate.from_messages([
        HumanMessage(content=prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    graph = create_react_agent(model, tools=tools, checkpointer=db.checkpointer)

    config = {"configurable": {"thread_id": thread_id}}
    input_messages = [HumanMessage(content=query)]
    formatted_input = prompt_template.invoke({"messages": input_messages})
    input_messages = formatted_input.to_messages()

    response = graph.invoke({"messages": input_messages}, config=config)
    chatbot_response = response["messages"][-1].content

    checkpoint = db.checkpointer.get(config)
    history = []

    if checkpoint and "channel_values" in checkpoint and "messages" in checkpoint["channel_values"]:
        history = [
            f"{msg.__class__.__name__}: {msg.content}"
            for msg in checkpoint["channel_values"]["messages"]
        ]

    return chatbot_response
