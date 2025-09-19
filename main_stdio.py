import sys
import json
import asyncio
import logging
import threading

from agent.mcp_agent import MCPAgent
from services.tool_registry import ToolRegistry
from memory.mcp_memory import MCPMemoryManager
from agent.prompt_template import generate_prompt

# Configure logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self):
        # Initialize tools, memory, and agent
        self.tools = ToolRegistry()
        self.memory = MCPMemoryManager()
        self.agent = MCPAgent(self.tools, self.memory, generate_prompt)
        
        # Async queue to communicate between thread and asyncio loop
        self.queue = asyncio.Queue()
        self.loop = asyncio.new_event_loop()  # Create dedicated event loop

    def start_stdin_reader(self):
        """Start a thread to read stdin and push lines to the async queue."""
        def reader():
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        continue  
                    line = line.strip()
                    if line.startswith("\ufeff"):
                        line = line.encode("utf-8").decode("utf-8-sig").strip()
                    asyncio.run_coroutine_threadsafe(self.queue.put(line), self.loop)
                except Exception:
                    logger.exception("Error reading stdin")
        t = threading.Thread(target=reader, daemon=True)
        t.start()

    async def process_messages(self):
        """Process messages from the queue indefinitely."""
        while True:
            line = await self.queue.get()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                logger.error("Invalid JSON: %s", line)
                continue

            req_id = request.get("id")
            try:
                # Handle request using MCPAgent
                result = await self.agent.handle_request(request)
                
                if req_id is not None:
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                    sys.stdout.write(json.dumps(response, separators=(",",":"))+ "\n")
                    sys.stdout.flush()
                    
            except Exception as e:
                logger.exception("Error in MCPAgent")
                if req_id is not None:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32000,
                            "message": str(e),
                            "data": {"type": e.__class__.__name__}
                        }
                    }
                    sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                    sys.stdout.flush()

    def run(self):
        """Start the MCP stdio server (Windows-safe)."""
        self.start_stdin_reader()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.process_messages())
        except Exception:
            logger.exception("Fatal error in MCP stdio server")
        finally:
            self.loop.close()


if __name__ == "__main__":
    # Windows asyncio fix
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    server = MCPServer()
    server.run()
