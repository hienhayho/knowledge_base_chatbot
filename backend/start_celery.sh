#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Set ENV_STAGE to 1 if it is not already set or if no argument is provided
: ${ENV_STAGE:=0}

# Get the current user's username
USER_NAME=$(whoami)

# Set ENV_STAGE and FLOWER_PORT based on the provided argument or default
if [ "$ENV_STAGE" -eq 0 ]; then
  LOG_LEVEL="DEBUG"
  WORKER_NAMING="$USER_NAME"_kb_worker_local@%h
  QUEUE_NAME="$USER_NAME"_kb_queue_local
  ENV_STAGE=0
  AUTOSCALE="3,1"
  echo "celery-workers: Running in DEBUG mode"
elif [ "$ENV_STAGE" -eq 2 ]; then
  LOG_LEVEL="DEBUG"
  WORKER_NAMING=kb_worker_develop@%h
  QUEUE_NAME=kb_queue_develop 
  ENV_STAGE=2
  AUTOSCALE="3,1"
  echo "celery-workers: Running in DEVELOP mode"
elif [ "$ENV_STAGE" -eq 1 ]; then
  LOG_LEVEL="WARNING"
  WORKER_NAMING=kb_worker_prod@%h
  QUEUE_NAME=kb_queue_prod 
  ENV_STAGE=1
  AUTOSCALE="15,2"
  echo "celery-workers: Running in PRODUCTION mode"
else
  echo "celery-workers: Invalid mode provided, allowed values: 0 (debug), 1 (production), 2 (staging/develop)"
  exit 1
fi


# set QUEUE_NAME to environment variable 
export QUEUE_NAME="$QUEUE_NAME"
echo "celery-workers queue: QUEUE_NAME=$QUEUE_NAME"


# Run celery with the specified log level
if [ -x "$(command -v celery)" ]; then
  celery -A src worker -l "$LOG_LEVEL" \
    -Q "$QUEUE_NAME" \
    --autoscale="$AUTOSCALE" \
    -n "$WORKER_NAMING" \
    -E -P gevent \
    --without-gossip --without-mingle 
else
  echo 'Error: celery could not be found' >&2
  exit 1
fi