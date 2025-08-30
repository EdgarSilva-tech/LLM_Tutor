from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from graph.graph import graph
from opik.integrations.langchain import OpikTracer
from langgraph.types import Command


app = FastAPI()
graph = graph()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(f"Data type: {type(data)}")

        opik_tracer = OpikTracer(graph=graph.get_graph(xray=True))
        config = {"configurable": {"thread_id": "1"},
                "callbacks": [opik_tracer]}
        events = graph.stream(
            {"messages": [{"role": "user", "content": f"{data}"}]},
            config,
            stream_mode="values",
        )
        for event in events:
            print(f"Event: {event}/n")
            for node_id, value in event.copy().items():
                print(f"Id: {node_id}, Value: {value}")
                if node_id == "__interrupt__":
                    questions = "".join(graph.get_state(config).values["quizz_questions"]).replace("  ", "").split("\n")
                    for question in questions:
                        answer = input(f"{question} ")
                        event["student_response"] = answer
                        graph.invoke(Command(resume=answer), config=config)
            if "messages" in event:
                print(f"Graph output type: {type(event["messages"][-1])}")
                await websocket.send_text(str(event["messages"][-1].pretty_print()))
