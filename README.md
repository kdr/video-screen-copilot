# Video Screen Copilot

A tool to record your screen, index it with CloudGlue AI, and ask questions about what you've seen on your screen using the Model Context Protocol (MCP).

## Prerequisites

- [CloudGlue](https://cloudglue.dev) API key
- Node.js (for the MCP server)
- Python 3.x (for the screen recording server)

## Project Components

This project consists of two main components:

### 1. Screen Recording Server (cg-session-upload)

A Flask-based server that records your screen and sends the recordings to CloudGlue for indexing.

#### Setup

1. Navigate to the `cg-session-upload` directory:
   ```bash
   cd cg-session-upload
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your CloudGlue API key and collection ID:
   ```
   CLOUDGLUE_API_KEY=your_api_key_here
   TARGET_COLLECTION_ID=your_collection_id_here
   ```

#### Usage

To start the server and record 70% of your screen:
```bash
python continuous_server.py --percentage 70
```

API endpoints:
- `/start` - Start recording
- `/stop` - Stop recording
- `/set_percentage/<int:percentage>` - Set screen recording percentage
- `/recent_recordings` - Get list of recent recordings

### 2. MCP Server (visual-screen-copilot-mcp-server)

A Node.js server implementing the Model Context Protocol to allow LLMs to access your screen recording data.

#### Setup

1. Navigate to the `visual-screen-copilot-mcp-server` directory:
   ```bash
   cd visual-screen-copilot-mcp-server
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the project:
   ```bash
   npm run build
   ```

## Integration with MCP

To use this project with an MCP-compatible AI assistant, add the following configuration to your MCP setup:

```json
{
    "visual-screen-copilot-mcp-server": {
      "command": "node",
      "args": [
        "/path/to/visual-screen-copilot-mcp-server/build/index.js",
        "--api-key",
        "your_cloudglue_api_key_here",
        "--target-collection-id",
        "your_screen_recording_collection_id_here"
      ]
    }
}
```

## Workflow

1. Start the screen recording server with `python continuous_server.py`
2. Navigate to `/start` to begin recording your screen
3. Use your computer normally
4. Navigate to `/stop` when you're done
5. The recording will be processed and indexed by CloudGlue
6. Use the MCP server to allow AI assistants to access and answer questions about your screen recordings

## License

YOLO
