#!/bin/sh
set -e

# Replace API URL in built files if REACT_APP_API_URL is provided at runtime
if [ ! -z "$REACT_APP_API_URL" ]; then
    echo "Updating API URL to: $REACT_APP_API_URL"
    
    # Find and replace in JavaScript files
    find /usr/share/nginx/html/static/js -name "*.js" -exec sed -i "s|http://localhost:5000/api|${REACT_APP_API_URL}|g" {} +
    
    # Also update in main files
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|http://localhost:5000/api|${REACT_APP_API_URL}|g" {} +
fi

# Execute the main command
exec "$@"
