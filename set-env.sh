#!/bin/bash

APP_NAME="jtlsnip"

# Check if DOKKU_HOST is passed as an argument, otherwise use the environment variable
if [ -z "$1" ]; then
  if [ -z "$DOKKU_HOST" ]; then
    echo "DOKKU_HOST is not set. Please provide it as an argument or set the environment variable."
    exit 1
  else
    HOST=$DOKKU_HOST
  fi
else
  HOST=$1
fi

# Path to the .env file
ENV_FILE="league.env"

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file $ENV_FILE does not exist."
  exit 1
fi

# Read each line from the .env file
while IFS= read -r line; do
  # Remove 'export ' prefix and split the line into key and value
  line="${line#export }"
  IFS='=' read -r key val <<< "$line"

  # Use SSH to set the config on the Dokku host
  ssh -t "$HOST" config:set "$APP_NAME" "$key=$val"
done < "$ENV_FILE"
