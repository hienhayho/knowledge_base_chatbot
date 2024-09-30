#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Set ENV_STAGE to the provided argument or default to 1
if [ -n "$1" ]; then
  ENV_STAGE=$1
else
  ENV_STAGE=1
fi




# Set the log level based on the value of ENV_STAGE
if [ "$ENV_STAGE" -eq 0 ]; then
  QUEUE_NAME="$USER_NAME"_kb_queue_local
  echo "app-dpe: Running in debug mode"
elif [ "$ENV_STAGE" -eq 1 ]; then
  QUEUE_NAME=kb_queue_prod 
  echo "app-dpe: Running in production mode"
elif [ "$ENV_STAGE" -eq 2 ]; then
  QUEUE_NAME=kb_queue_develop 
  echo "app-dpe: Running in develop mode (staging mode for deployment)"
else
  echo "app-dpe: Invalid mode provided"
  exit 1
fi

# Run python main.py and start celery in the background
sh -c "ENV_STAGE=$ENV_STAGE ./start_celery.sh & ENV_STAGE=$ENV_STAGE QUEUE_NAME=$QUEUE_NAME python app.py"