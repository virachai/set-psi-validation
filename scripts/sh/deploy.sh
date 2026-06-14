#!/bin/bash

# Configuration
DEPLOY_DIR="data/deploy"
TIMESTAMP=$(date +"%Y%m%dT%H%M")
FILE_PATH="$DEPLOY_DIR/deploy_info_$TIMESTAMP.json"
API_KEY="90e2bc3e-5148-4dcb-aa74-285cebc9bbe5"

# Ensure directory exists
mkdir -p "$DEPLOY_DIR"

# 1. Run deploy
echo "Deploying project..."
npm run deploy:prod
if [ $? -ne 0 ]; then
    echo "Deployment failed!"
    exit 1
fi

# 2. Update deployment info
DEPLOY_INFO=$(clasp deployments | tail -n 1)
DEPLOY_ID=$(echo "$DEPLOY_INFO" | sed 's/- //g' | awk '{print $1}')

# Save to JSON
cat <<EOF > "$FILE_PATH"
{
  "timestamp": "$TIMESTAMP",
  "deployment_info": "$DEPLOY_INFO",
  "deployment_id": "$DEPLOY_ID",
  "status": "success",
  "command": "npm run deploy:prod"
}
EOF

# Update deployment_id.txt
echo "$DEPLOY_ID" > "data/deploy/deployment_id.txt"

echo "Deployment info saved to $FILE_PATH and data/deploy/deployment_id.txt"

# 3. Test the API
echo "Testing API endpoint..."
URL="https://script.google.com/macros/s/$DEPLOY_ID/exec"

RESPONSE=$(curl -L -G "$URL" \
  --data-urlencode "action=get_psi" \
  --data-urlencode "api_key=$API_KEY" \
  -s)

echo "Response: $RESPONSE"

# Validate response
if [[ "$RESPONSE" == *"success"* ]]; then
    echo "Test passed!"
else
    echo "Test failed!"
    exit 1
fi
