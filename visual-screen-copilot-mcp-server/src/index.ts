#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CloudGlue } from "@aviaryhq/cloudglue-js";
import * as dotenv from "dotenv";
import { parseArgs } from "node:util";

// Import tool registrations
import { registerDetailRecentScreenRecording } from "./tools/detail-recent-screen-recording.js";

// Parse command line arguments
const { values: args } = parseArgs({
  options: {
    "api-key": {
      type: "string",
    },
    "target-collection-id": {
      type: "string",
    },
  },
});

// Load environment variables from .env file
dotenv.config();

const cgClient = new CloudGlue({
  apiKey: args["api-key"] || process.env.CLOUDGLUE_API_KEY,
});

// Create server instance
const server = new McpServer({
  name: "visual-screen-copilot-mcp-server",
  version: "4.2.0",
  capabilities: {
    resources: {},
    tools: {},
  },
});

// Register all tools
const collectionId = args["target-collection-id"] || process.env.TARGET_COLLECTION_ID;
if (!collectionId) {
  console.error("Error: target-collection-id is required either as an argument or in the .env file");
  process.exit(1);
}
registerDetailRecentScreenRecording(server, cgClient, collectionId);

// Run server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("CloudGlue MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
