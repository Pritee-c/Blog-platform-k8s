# Lightweight multi-stage Dockerfile for API Gateway (Nginx)
FROM nginx:1.27-alpine

# Set up logging
RUN mkdir -p /var/log/nginx && \
    touch /var/log/nginx/api_auth.log \
          /var/log/nginx/api_posts.log \
          /var/log/nginx/api_categories.log \
          /var/log/nginx/api_comments.log && \
    chown -R nginx:nginx /var/log/nginx

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

