from flask import Flask, request, jsonify, current_app # Import current_app
import subprocess
import logging
from werkzeug.exceptions import RequestEntityTooLarge

# Logging config
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
logger.debug(f"Set MAX_CONTENT_LENGTH at startup: {app.config['MAX_CONTENT_LENGTH']}")

@app.route("/upload", methods=["POST"])
def upload():
    logger.debug(f"Received request: Content-Length={request.content_length}")
    logger.debug(f"Request context MAX_CONTENT_LENGTH: {current_app.config.get('MAX_CONTENT_LENGTH')}")
    if hasattr(request, 'max_content_length'):
         logger.debug(f"Request object max_content_length: {request.max_content_length}")

    try:
        # Access request.data to ensure body processing is triggered
        data_to_pipe = request.data 
        logger.debug(f"Successfully read request.data, length: {len(data_to_pipe)}")

        curl_process = subprocess.Popen(
            ["curl", "-X", "POST", "-T", "-", "http://localhost:5600"], # Ensure target service is running
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = curl_process.communicate(input=data_to_pipe, timeout=60)
        logger.debug(f"curl stdout: {stdout.decode('utf-8', errors='ignore')}")
        logger.debug(f"curl stderr: {stderr.decode('utf-8', errors='ignore')}")

        # Check internal curl exit code
        if curl_process.returncode != 0:
            logger.error(f"Internal curl process failed with code {curl_process.returncode}")
            return jsonify({"error": "Internal curl processing failed", "details": stderr.decode('utf-8', errors='ignore')}), 500

        return stdout, 200, {"Content-Type": "application/json"} # Or whatever the target service returns
    except subprocess.TimeoutExpired:
        logger.error("Subprocess timed out")
        return jsonify({"error": "parser timed out"}), 504
    except RequestEntityTooLarge:
        # This might not be hit if the global error handler catches it first,
        # but good for defense-in-depth.
        logger.error(f"RequestEntityTooLarge caught within upload view. Content-Length={request.content_length}")
        return jsonify(error="Replay file too large (view)"), 413
    except Exception as e:
        logger.error(f"An unexpected error occurred in upload view: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    # e is the RequestEntityTooLarge exception object
    logger.error(f"413 error triggered by errorhandler. Request Content-Length={request.content_length}")
    logger.error(f"In errorhandler - app.config['MAX_CONTENT_LENGTH']: {app.config.get('MAX_CONTENT_LENGTH')}")
    logger.error(f"In errorhandler - current_app.config['MAX_CONTENT_LENGTH']: {current_app.config.get('MAX_CONTENT_LENGTH')}")
    if hasattr(request, 'max_content_length'):
        logger.error(f"In errorhandler - request.max_content_length: {request.max_content_length}")
    # The exception 'e' itself might have useful properties, though often just a description
    logger.error(f"Exception details: {e}") 
    return jsonify(error="Replay file too large (errorhandler)"), 413

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    logger.debug("Starting wrapper API on port 5700")
    app.run(host="0.0.0.0", port=5700)