import asyncio
import json
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import httpx
from mcp import ClientSession
from mcp.client.auth import TokenStorage, OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthToken, OAuthClientInformationFull, OAuthClientMetadata
from pydantic import AnyUrl

from config import MS365_MCP_URL, MS365_CALLBACK_URL

CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 8080

TOKEN_CACHE_PATH = Path("credentials/microsoft_auth_token.json")
CLIENT_CACHE_PATH = Path("credentials/microsoft_auth_client.json")


class FileTokenStorage(TokenStorage):
    def __init__(self, token_path: Path = TOKEN_CACHE_PATH, client_path: Path = CLIENT_CACHE_PATH):
        self.token_path = token_path
        self.client_path = client_path


    async def get_tokens(self) -> OAuthToken:
        if not self.token_path.exists():
            return None

        data = json.loads(self.token_path.read_text(encoding="utf-8"))

        return OAuthToken.model_validate(data)

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.token_path.write_text(
            tokens.model_dump_json(indent=2),
            encoding="utf-8",
        )

    async def get_client_info(self) -> OAuthClientInformationFull:
        if not self.client_path.exists():
            return None

        data = json.loads(self.client_path.read_text(encoding="utf-8"))

        return OAuthClientInformationFull.model_validate(data)

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client_path.write_text(
            client_info.model_dump_json(indent=2),
            encoding="utf-8",
        )


async def redirect_handler(auth_url: str) -> None:
    webbrowser.open_new_tab(auth_url)


async def callback_handler() -> tuple[str, str | None]:
    loop = asyncio.get_running_loop()
    result = loop.create_future()

    async def handle_callback(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        request_line = await reader.readline()
        path = request_line.decode().split(" ")[1]

        query = parse_qs(urlparse(path).query)

        code = query.get("code", [None])[0]
        state = query.get("state", [None])[0]

        if code and not result.done():
            result.set_result((code, state))

        body = "Microsoft authentication completed. You can close this window."

        writer.write(
            (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode('utf-8'))}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}\r\n"
            ).encode()
        )

        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(
        handle_callback,
        CALLBACK_HOST,
        CALLBACK_PORT,
    )

    try:
        return await result
    finally:
        server.close()
        await server.wait_closed()


class MicrosoftMCPClient:
    def __init__(self, url: str = MS365_MCP_URL):
        self._url = url
        self.storage = FileTokenStorage()

    def _create_oauth_provider(self) -> OAuthClientProvider:
        return OAuthClientProvider(
            server_url=self._url,
            client_metadata=OAuthClientMetadata(
                client_name="Personal Assistant",
                redirect_uris=[
                    AnyUrl(MS365_CALLBACK_URL),
                ],
                grant_types=[
                    "authorization_code",
                    "refresh_token",
                ],
                response_types=["code"]
            ),
            storage=self.storage,
            redirect_handler=redirect_handler,
            callback_handler=callback_handler,
        )

    async def list_tools(self):
        oauth = self._create_oauth_provider()

        async with httpx.AsyncClient(auth=oauth) as http_client:
            async with streamable_http_client(
                    url=self._url,
                    http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(
                        read_stream=read_stream,
                        write_stream=write_stream,
                ) as session:
                    await session.initialize()
                    return await session.list_tools()

    async def call_tool(self, name: str, arguments: dict | None = None):
        oauth = self._create_oauth_provider()
        timeout = httpx.Timeout(
            connect=10.0,
            read=60.0,
            write=10.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(auth=oauth, timeout=timeout) as http_client:
            async with streamable_http_client(
                    url=self._url,
                    http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(
                        read_stream=read_stream,
                        write_stream=write_stream,
                ) as session:
                    await session.initialize()

                    return await session.call_tool(
                        name=name,
                        arguments=arguments or {},
                    )
