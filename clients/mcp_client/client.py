#!/usr/bin/env python3

import asyncio
import os
import sys
import json
from typing import Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration, GenerateContentConfig

load_dotenv()  # Load API keys from .env


class MCPClient:
    def __init__(self):
        """Initialize the MCP client and Gemini API client."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")

        self.genai_client = genai.Client(api_key=gemini_api_key)

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server with stdio transport."""
        command = "python" if server_script_path.endswith('.py') else "node"
        server_params = StdioServerParameters(command=command, args=[server_script_path])
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # Fetch tool list from server
        response = await self.session.list_tools()
        tools = response.tools

        # LLM instruction: Tell Gemini to use only allowed directory and not ask user
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        self.function_declarations = convert_mcp_tools_to_gemini(tools)

    async def process_query(self, query: str) -> str:
        user_prompt_content = types.Content(
            role='user',
            parts=[types.Part.from_text(
                "Always use the allowed directory for all file operations. Never ask the user for path input.\n\n" + query
            )]
        )

        response = self.genai_client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=[user_prompt_content],
            config=GenerateContentConfig(
                tools=self.function_declarations,
            ),
        )

        final_text = []

        for candidate in response.candidates:
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if isinstance(part, types.Part):
                        if part.function_call:
                            tool_name = part.function_call.name
                            tool_args = part.function_call.args
                            print(f"\n[Calling tool: {tool_name} with args {tool_args}]")

                            try:
                                result = await self.session.call_tool(tool_name, tool_args)
                                tool_output = {"result": result.content}
                            except Exception as e:
                                tool_output = {"error": str(e)}

                            tool_response = types.Part.from_function_response(
                                name=tool_name,
                                response=tool_output
                            )
                            tool_content = types.Content(
                                role='tool',
                                parts=[tool_response]
                            )

                            # Follow-up generation
                            response = self.genai_client.models.generate_content(
                                model='gemini-2.0-flash-001',
                                contents=[user_prompt_content, part, tool_content],
                                config=GenerateContentConfig(
                                    tools=self.function_declarations
                                )
                            )
                            final_text.append(response.candidates[0].content.parts[0].text)
                        else:
                            final_text.append(part.text)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Interactive CLI loop for user queries."""
        print("\nMCP Client Started! Type 'quit' to exit.")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
            response = await self.process_query(query)
            print("\n" + response)

    async def cleanup(self):
        await self.exit_stack.aclose()


def clean_schema(schema):
    if isinstance(schema, dict):
        schema.pop("title", None)
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    return schema


def convert_mcp_tools_to_gemini(mcp_tools):
    gemini_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema)
        function_declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters
        )
        gemini_tools.append(Tool(function_declarations=[function_declaration]))
    return gemini_tools


async def main():
    """Start the client and connect to a known server script."""
    client = MCPClient()
    try:
        # 🔧 Hardcoded or configured script path to avoid CLI args
        server_script_path = "./filesystem_server.py"  # Change if needed
        await client.connect_to_server(server_script_path)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
