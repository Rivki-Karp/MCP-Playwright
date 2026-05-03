import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any

import httpx
from anthropic import Anthropic
from client import MCPClient
from dotenv import load_dotenv

# Loading environment variables
load_dotenv()

class ChatHost:
    """
    Host manager for multiple MCP clients, coordinating tool discovery 
    and LLM interaction via the Anthropic API.
    """
    def __init__(self):
        # Initializing both USA and Israel weather servers as MCP clients
        self.mcp_clients: list[MCPClient] = [
            MCPClient("./weather_USA.py"),
            MCPClient("./weather_Israel.py")
        ]
        self.tool_clients: dict[str, tuple[MCPClient, str]] = {}
        self.clients_connected = False
        self.exit_stack = AsyncExitStack()
        
        # Netfree-compatible transport settings
        transport = httpx.HTTPTransport(verify=False)
        self.anthropic = Anthropic(http_client=httpx.Client(transport=transport))

    async def connect_mcp_clients(self):
        """Connects all configured MCP clients once to ensure availability."""
        if self.clients_connected:
            return

        for client in self.mcp_clients:
            if client.session is None:
                await client.connect_to_server()

        if not self.mcp_clients:
            raise RuntimeError("No MCP clients are connected.")

        self.clients_connected = True

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """
        Collects tools from all connected MCP clients and maps them with a unique prefix.
        Prevents naming collisions between different servers.
        """
        await self.connect_mcp_clients()
        self.tool_clients = {}
        available_tools: list[dict[str, Any]] = []

        for client in self.mcp_clients:
            if client.session is None:
                print(f"Warning: MCP client {client.client_name} is not connected, skipping.")
                continue

            try:
                response = await client.session.list_tools()
                for tool in response.tools:
                    # Create a unique name for each tool based on its origin server
                    exposed_name = f"{client.client_name}__{tool.name}"
                    if exposed_name in self.tool_clients:
                        raise RuntimeError(f"Duplicate tool name detected: {exposed_name}")

                    self.tool_clients[exposed_name] = (client, tool.name)
                    available_tools.append(
                        {
                            "name": exposed_name,
                            "description": f"[{client.client_name}] {tool.description}",
                            "input_schema": tool.inputSchema,
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to get tools from {client.client_name}: {str(e)}")
                continue

        if not available_tools:
            raise RuntimeError("No tools available from any MCP client.")

        return available_tools

    async def process_query(self, query: str) -> str:
        """
        Processes a user query by determining which tools to use and executing them.
        Implements a loop to handle multiple sequential tool calls.
        """
        messages = [{"role": "user", "content": query}]
        available_tools = await self.get_available_tools()
        final_text = []

        while True:
            # Send context to the LLM to decide on the next action[cite: 1]
            response = self.anthropic.messages.create(
                model="claude-haiku-4-5", 
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            assistant_message_content = []
            tool_results = []
            saw_tool_use = False

            for content in response.content:
                assistant_message_content.append(content)

                if content.type == 'text':
                    final_text.append(content.text)
                    continue

                if content.type == 'tool_use':
                    saw_tool_use = True
                    tool_name = content.name
                    tool_args = content.input

                    if tool_name not in self.tool_clients:
                        raise RuntimeError(f"Unknown tool requested by model: {tool_name}")

                    # Route the tool call to the specific MCP client[cite: 1]
                    client, original_tool_name = self.tool_clients[tool_name]
                    if client.session is None:
                        raise RuntimeError(f"MCP client {client.client_name} is not connected.")

                    # Execute the automated action (e.g., Playwright automation)[cite: 1]
                    result = await client.session.call_tool(original_tool_name, tool_args)
                    
                    # Update local logs and tool result payload[cite: 1]
                    # We only return text content for simplicity in the chat view
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content,
                        }
                    )

            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })

            if not saw_tool_use:
                break

            # Add results back to context for the LLM to generate a final answer[cite: 1]
            messages.append({
                "role": "user",
                "content": tool_results
            })

        return "\n".join(final_text)
    
    async def chat_loop(self):
        """Interactive terminal loop for user communication."""
        print("\n--- Weather MCP Assistant Active ---")
        print("Both USA (API) and Israel (Browser-based) sources are connected.")
        print("Type 'quit' or 'exit' to end the session.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    break
                
                response = await self.process_query(query)
                print("\n" + response)
                
            except Exception as e:
                print(f"\nchat_loop Error: {str(e)}")
                
    async def cleanup(self):
        """Releases all resources and closes browser instances safely."""
        for client in reversed(self.mcp_clients):
            await client.cleanup()
        await self.exit_stack.aclose()
        
async def main():
    host = ChatHost()
    try:
        await host.chat_loop()
    finally:
        await host.cleanup()
        
if __name__ == "__main__":
    asyncio.run(main())