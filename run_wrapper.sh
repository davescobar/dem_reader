#!/bin/bash

# Start the Java parser in the background
java -jar /usr/src/parser/target/stats-0.1.0.jar 5600 &
JAVA_PID=$!

# Optional: Wait a bit to ensure it's listening
sleep 2

# Start the Python wrapper API with uvicorn
gunicorn -w 4 -b 0.0.0.0:5700 wrapper_api:app --timeout 120
