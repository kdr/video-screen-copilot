"""
python continuous_server.py --percentage 70
"""

import os
import subprocess
import time
import datetime

import threading
import signal
import argparse
import logging
from flask import Flask, jsonify
from cloudglue import CloudGlue
from dotenv import load_dotenv

load_dotenv('dot.env')
TARGET_COLLECTION_ID = os.getenv('TARGET_COLLECTION_ID')
cgClient = CloudGlue(api_key=os.getenv('CLOUDGLUE_API_KEY'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('screen_recorder.log')
    ]
)
logger = logging.getLogger('screen_recorder')

app = Flask(__name__)

# Configuration
OUTPUT_DIR = "recordings"
# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Track recording state
recording_state = {
    "is_active": False,
    "recordings": [],
    "stop_event": threading.Event(),
    "screen_percentage": 100  # Default to full screen
}

def handle_shutdown(sig, frame):
    logger.info("Shutting down, cleaning up ffmpeg processes...")
    # Kill any running ffmpeg processes
    subprocess.run(["pkill", "-f", "ffmpeg"], stderr=subprocess.PIPE)
    # Stop the recording process
    recording_state["stop_event"].set()
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def post_process_recording(session_id, file_path, timestamp=None):
    """
    Perform post-processing on the recorded file.
    This function runs in its own thread and can make network calls.
    
    Args:
        session_id: The session ID of the recording
        file_path: The path to the recorded file
        timestamp: The timestamp when recording was started (format: 'HH:MM:SS')
    """
    logger.info(f"Starting post-processing for session {session_id}...")
    
    recording_info = next((r for r in recording_state["recordings"] if r["session_id"] == session_id), None)
    if recording_info:
        recording_info["post_processing_status"] = "in_progress"
    
    try:
        metadata = {
            "source": "screen_recorder"
        }
        
        # Add timestamp to metadata if provided
        if timestamp:
            metadata["recorded_at"] = timestamp
            
        f = cgClient.files.upload(
            file_path,
            metadata=metadata,
            # optionally waiting until finish
            wait_until_finish=True,
            poll_interval=1
        )
        logger.info(f"Uploaded file to CloudGlue: {f.id}")
        cgClient.collections.add_video(collection_id=TARGET_COLLECTION_ID, file_id=f.id)
        cgClient.extract.create(
            url=f.uri,
            prompt="Extract programs and websites that appear on screen",
            schema={
                'programs': {
                    'name': '<string>', 
                    'applicationType': '<string>',                    
                },
                'websites': {
                    'name': '<string>',
                    'url': '<string>',
                    'description': '<string>',
                }
            }
        )
        
        # Update status on completion
        if recording_info:
            recording_info["post_processing_status"] = "completed"
        logger.info(f"Post-processing completed for session {session_id}")
        
    except Exception as e:
        # Handle any errors in post-processing
        if recording_info:
            recording_info["post_processing_status"] = "error"
            recording_info["post_processing_error"] = str(e)
        logger.error(f"Error in post-processing for session {session_id}: {str(e)}")

def record_screen(session_id):
    """
    Record the screen with the current percentage setting.
    Uses FFmpeg's built-in crop filter with iw (input width) and ih (input height) variables
    to ensure we always get the full height regardless of display settings.
    """
    # Get output filename based on timestamp
    output_file = os.path.join(OUTPUT_DIR, f"recording_{session_id}.mp4")
    
    # Get percentage from recording state
    percentage = recording_state["screen_percentage"]
    
    logger.info(f"Starting recording (percentage: {percentage}%)")
    
    start_time = time.time()
    
    # Single FFmpeg command that handles both recording and cropping
    # Using iw (input width) and ih (input height) ensures we work with the actual captured dimensions
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "avfoundation",
        "-framerate", "30",
        "-i", "1:",  # Screen index 1, no audio
        "-t", "10",  # Record for 10 seconds
    ]
    
    # Add cropping filter if not capturing the full screen
    if percentage < 100:
        # This will crop to X% of the input width while keeping full height
        ffmpeg_cmd.extend([
            "-vf", f"crop=iw*{percentage/100}:ih:0:0"
        ])
    
    # Add output options
    ffmpeg_cmd.extend([
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-y",
        output_file
    ])
    
    logger.info(f"Running FFmpeg: {' '.join(ffmpeg_cmd)}")
    
    # Run the command
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    
    duration = time.time() - start_time
    logger.info(f"FFmpeg process completed in {duration:.2f} seconds")
    
    if process.returncode == 0:
        logger.info(f"Recording successful")
        create_recording_info(session_id, output_file, duration, percentage)
        return True
    else:
        logger.error(f"Error recording screen: {stderr}")
        with open(f"ffmpeg_error_{session_id}.log", "w") as f:
            f.write(stderr)
        
        recording_info = {
            "session_id": session_id,
            "status": "error",
            "error": "Failed to record screen",
            "timestamp": time.time()
        }
        recording_state["recordings"].append(recording_info)
        return False

def create_recording_info(session_id, output_file, duration, percentage):
    """Create a recording info entry and start post-processing"""
    # Generate a timestamp in the format 'HH:MM:SS'
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    recording_info = {
        "session_id": session_id,
        "status": "completed",
        "file": output_file,
        "absolute_path": os.path.abspath(output_file),
        "duration": duration,
        "screen_percentage": percentage,
        "post_processing_status": "pending",
        "timestamp": time.time(),
        "formatted_timestamp": current_time
    }
    
    recording_state["recordings"].append(recording_info)
    
    # Start post-processing in a separate thread
    threading.Thread(
        target=post_process_recording,
        args=(session_id, os.path.abspath(output_file), current_time),
        daemon=True
    ).start()

def continuous_recording_process():
    """
    Process that records a 10-second video every 10 seconds
    until the stop event is triggered.
    """
    logger.info("Starting continuous recording process...")
    
    while not recording_state["stop_event"].is_set():
        session_id = int(time.time())
        record_screen(session_id)
        
        # Wait for the next 10-second interval
        # (but check for stop event every second)
        for _ in range(10):
            if recording_state["stop_event"].is_set():
                break
            time.sleep(1)
    
    logger.info("Continuous recording process stopped.")
    recording_state["is_active"] = False

@app.route('/', methods=['GET'])
def home():
    host = "localhost:5002"
    percentage = recording_state["screen_percentage"]
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Continuous Screen Recorder API</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                border-bottom: 1px solid #ccc;
                padding-bottom: 10px;
            }}
            .endpoint {{
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 20px;
            }}
            pre {{
                background-color: #f1f1f1;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            code {{
                font-family: monospace;
            }}
            .info {{
                background-color: #e7f3fe;
                border-left: 6px solid #2196F3;
                padding: 10px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>Continuous Screen Recorder API Documentation</h1>
        
        <div class="info">
            <p><strong>Current Configuration:</strong> Recording the left {percentage}% of the screen</p>
        </div>
        
        <div class="endpoint">
            <h2>Start Continuous Recording</h2>
            <p>Starts continuous recording process (10-second videos every 10 seconds).</p>
            <pre><code>curl -X GET http://{host}/start</code></pre>
            <p>Returns: JSON with status information.</p>
            <pre><code>{{
  "status": "started",
  "message": "Continuous recording started"
}}</code></pre>
        </div>
        
        <div class="endpoint">
            <h2>Stop Continuous Recording</h2>
            <p>Stops the continuous recording process.</p>
            <pre><code>curl -X GET http://{host}/stop</code></pre>
            <p>Returns: JSON with status information.</p>
            <pre><code>{{
  "status": "stopped",
  "message": "Continuous recording stopped",
  "recordings_count": 5
}}</code></pre>
        </div>
        
        <div class="endpoint">
            <h2>Get Recent Recordings</h2>
            <p>Retrieves the 3 most recent completed recordings.</p>
            <pre><code>curl -X GET http://{host}/recent_recordings</code></pre>
            <p>Returns: JSON with list of recent recordings.</p>
            <pre><code>{{
  "count": 3,
  "recordings": [
    {{
      "session_id": 1621234567,
      "status": "completed",
      "file": "/absolute/path/to/recordings/recording_1621234567.mp4",
      "screen_percentage": {percentage},
      "duration": 10.5,
      "post_processing_status": "completed",
      "timestamp": 1621234567.89
    }},
    ...
  ]
}}</code></pre>
        </div>
        
        <div class="endpoint">
            <h2>Set Screen Percentage</h2>
            <p>Changes the percentage of the screen to record (left side).</p>
            <pre><code>curl -X GET http://{host}/set_percentage/50</code></pre>
            <p>Returns: JSON with updated configuration.</p>
            <pre><code>{{
  "status": "success",
  "message": "Screen percentage set to 50%"
}}</code></pre>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/start', methods=['GET'])
def start():
    # Check if recording is already active
    if recording_state["is_active"]:
        return jsonify({
            "status": "error", 
            "message": "Continuous recording is already active"
        }), 400
    
    # Reset the stop event
    recording_state["stop_event"].clear()
    recording_state["is_active"] = True
    
    # Start continuous recording in background thread
    threading.Thread(
        target=continuous_recording_process,
        daemon=True
    ).start()
    
    return jsonify({
        "status": "started", 
        "message": "Continuous recording started",
        "screen_percentage": recording_state["screen_percentage"]
    })

@app.route('/stop', methods=['GET'])
def stop():
    # Check if recording is active
    if not recording_state["is_active"]:
        return jsonify({
            "status": "error", 
            "message": "No active recording to stop"
        }), 400
    
    # Signal the recording process to stop
    recording_state["stop_event"].set()
    
    # Wait a bit for the process to stop cleanly
    time.sleep(1)
    
    return jsonify({
        "status": "stopped", 
        "message": "Continuous recording stopped",
        "recordings_count": len(recording_state["recordings"])
    })

@app.route('/recent_recordings', methods=['GET'])
def recent_recordings():
    # Find all completed recordings
    completed = [
        recording for recording in recording_state["recordings"]
        if recording.get("status") == "completed"
    ]
    
    # Sort by timestamp in descending order and take the latest 3
    recent = sorted(completed, key=lambda x: x["timestamp"], reverse=True)[:3]
    
    return jsonify({
        "count": len(recent),
        "recordings": recent
    })

@app.route('/set_percentage/<int:percentage>', methods=['GET'])
def set_percentage(percentage):
    # Validate the percentage
    if percentage < 0 or percentage > 100:
        return jsonify({
            "status": "error",
            "message": "Percentage must be between 0 and 100"
        }), 400
    
    # Update the recording state
    recording_state["screen_percentage"] = percentage
    
    return jsonify({
        "status": "success",
        "message": f"Screen percentage set to {percentage}%"
    })

if __name__ == '__main__':
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Continuous Screen Recorder Server')
    parser.add_argument('--percentage', type=int, default=100, 
                        help='Percentage of the screen to record (0-100, left side)')
    parser.add_argument('--port', type=int, default=5002,
                        help='Port to run the server on')
    
    args = parser.parse_args()
    
    # Validate percentage
    if args.percentage < 0 or args.percentage > 100:
        logger.error("Error: Percentage must be between 0 and 100")
        exit(1)
    
    # Set the screen percentage in the recording state
    recording_state["screen_percentage"] = args.percentage
    
    logger.info(f"Starting server recording {args.percentage}% of the left side of the screen")
    app.run(debug=True, host='0.0.0.0', port=args.port) 