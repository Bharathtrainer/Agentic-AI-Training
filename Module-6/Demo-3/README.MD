Terminal 1: Start the MCP Server (The Tools)
Open your first terminal.

Navigate to your project root folder:

PowerShell
cd "C:\Users\nbhar\Downloads\Agentic -Training-Demo\Module-6\Demo-3\enterprise-mcp-weather"
Start the server:

PowerShell
python mcp_server.py
(Leave this window open and running in the background).

Terminal 2: Run the Enterprise Agent (The Brain)
Open a second terminal.

Navigate to the exact same project folder:

PowerShell
cd "C:\Users\nbhar\Downloads\Agentic -Training-Demo\Module-6\Demo-3\enterprise-mcp-weather"
Run the agent module:

PowerShell
python -m app.agent