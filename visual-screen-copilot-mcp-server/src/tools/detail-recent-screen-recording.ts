import { z } from "zod";
import { CloudGlue } from "@aviaryhq/cloudglue-js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export const schema = {

};

// Define extract type
interface Extract {
  job_id: string;
  status: string;
  url?: string;
  data?: {
    file_id?: string;
    [key: string]: any;
  };
  [key: string]: any;
}

// Function to format current time as HH:MM:SS
function getCurrentTimeFormatted(): string {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

export function registerDetailRecentScreenRecording(
  server: McpServer,
  cgClient: CloudGlue,
  collection_id: string,
) {
  server.tool(
    "detail_recent_screen_recording",
    "User has their screen recorded constently by trusted copilot software. This tool returns the details of the most recent screen recording for LLM to use as context in its response.",
    schema,
    async ({  }) => {
      const files = await cgClient.collections.listVideos(collection_id, {
        limit: 12,
      });

      // // Get all extracts first
      // let allExtracts: Extract[] = [];
      // try {
      //   const extractsResponse = await cgClient.extract.listExtracts();
      //   if (extractsResponse && extractsResponse.data) {
      //     allExtracts = extractsResponse.data as Extract[];
      //   }
      // } catch (error) {
      //   console.error("Error fetching extracts:", error);
      // }

      // Process each file to get additional information
      const processedFiles = await Promise.all(
        files.data
          .filter(file => file.status === "completed")
          .map(async (file) => {
            const fileInfo = await cgClient.files.getFile(file.file_id);
            
            // Fetch the video description
            const description = await cgClient.collections.getDescription(
              collection_id,
              file.file_id,
            );
            
            // Find the most recent extract for this file
            // Assuming extracts have some way to identify which file they're for
            // This could be through metadata, job_id, or some other identifier
            // const fileExtract = allExtracts.find(extract => 
            //   extract.data && 
            //   extract.data.file_id === file.file_id
            // );
            
            return {
              metadata: fileInfo.metadata,
              description: description,
              // Include extract data if found
              // extract: fileExtract ? {
              //   extract_data: fileExtract.data || {},
              //   extract_status: fileExtract.status,
              //   job_id: fileExtract.job_id
              // } : null
            };
          })
      );

      // Create the response object with current time and processed files
      const responseObject = {
        current_time: getCurrentTimeFormatted(),
        recent_screen_recordings: processedFiles
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(responseObject),
          },
        ],
      };
    },
  );
}
