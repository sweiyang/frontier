from core.http_client.http_client import http_client

class AgentConnector:
    def __init__(self):
        self.client = http_client

    def stream_chat(self, endpoint: str, messages: list):
        with self.client.stream(
            "POST",
            endpoint,
            json={"messages": messages}
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    def close(self):
        self.client.close()