#!/bin/sh

# Activate the virtual environment
source .venv/bin/activate

# Set ENV_STAGE to 1 if it is not already set or if no argument is provided
: ${ENV_STAGE:=1}

if [ "$ENV_STAGE" -eq 0 ]; then
  FLOWER_PORT=5001
  echo "celery-flowers-monitor: Running in DEBUG mode"
elif [ "$ENV_STAGE" -eq 2 ]; then
  FLOWER_PORT=5001
  echo "celery-flowers-monitor: Running in DEVELOP mode"
elif [ "$ENV_STAGE" -eq 1 ]; then
  FLOWER_PORT=5555
  echo "celery-flowers-monitor: Running in PRODUCTION mode"
else
  echo "celery-flowers-monitor: Invalid mode provided, allowed values: 0 (debug), 1 (production), 2 (staging/develop)"
  exit 1
fi

# # Check Celery workers availability
# until ! timeout 10s celery -A src inspect ping; do
#     >&2 echo "Celery workers not available"
#     sleep 5
# done

echo 'Starting flower'
celery -A src flower \
    --port="$FLOWER_PORT" \
    --basic-auth="admin:admin123@123,guest:Abc@123123"


# celery -A src flower --port=5555 --broker=redis://redis:6379/5
# "celery", "-A" ,"src.app.celery", "flower", "--port=5555", "--broker=redis://redis:6379/0"