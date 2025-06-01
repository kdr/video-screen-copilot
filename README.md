# Video Screen Copilot

A tool to record your screen, index it with CloudGlue AI, and ask questions about what you've seen on your screen using the Model Context Protocol (MCP).

Demo videos: [▶️ YouTube Playlist](https://www.youtube.com/watch?v=wjD4Dz2HZpc&list=PL5TLz9GcWHcgYltVOZgc2Jl5Xi1ZCeLlh)

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

Start the server with your preferred options:

```bash
# Using environment variables from .env file
python continuous_server.py --percentage 70

# Explicitly providing API key and collection ID
python continuous_server.py --percentage 70 --api-key your_api_key_here --collection-id your_collection_id_here

# Additional options
python continuous_server.py --port 5002 --percentage 70
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

## Screen shots

<img width="932" alt="image" src="https://github.com/user-attachments/assets/3c6b3854-f209-4e1a-acab-01c9e7eb779c" />

<img width="940" alt="image" src="https://github.com/user-attachments/assets/8946ab8d-7918-4eb2-9b7b-5437833f1249" />

Deep Research Over Screen Recording - [Claude Conversation](https://claude.ai/share/a25b0a5e-737c-48f5-b821-6abdba2d0668)

<img width="719" alt="image" src="https://github.com/user-attachments/assets/36998ca3-124f-4bed-a506-a6c083fa80a6" />

<img width="702" alt="image" src="https://github.com/user-attachments/assets/f3c6f614-d255-440e-8ab2-12c7762b6fba" />

<img width="686" alt="image" src="https://github.com/user-attachments/assets/46e59cc4-c5fd-4244-8d85-213866b6bf74" />

<img width="719" alt="image" src="https://github.com/user-attachments/assets/5c86636a-2990-41a8-a575-98c285f994f2" />


<img width="885" alt="image" src="https://github.com/user-attachments/assets/5da3cf07-b59c-4d92-a3ed-fca0498c49bc" />


## Hackathon

<img src="https://images.lumacdn.com/cdn-cgi/image/format=auto,fit=cover,dpr=2,background=white,quality=75,width=400,height=400/event-covers/2t/a94f6b73-8b4a-42f8-8f03-bca3e5a1d1d6.png">

[World's Biggest MCP Hackathon](https://lu.ma/t4zeld9m)

* Saturday, May 17, 2025
