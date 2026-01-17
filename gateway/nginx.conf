# Lightweight multi-stage Dockerfile for API Gateway (Nginx)
FROM nginx:1.27-alpine

# Set up logging and cache directories with proper permissions
RUN mkdir -p /var/log/nginx \
             /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp && \
    touch /var/log/nginx/api_auth.log \
          /var/log/nginx/api_posts.log \
          /var/log/nginx/api_categories.log \
          /var/log/nginx/api_comments.log && \
    chown -R nginx:nginx /var/log/nginx /var/cache/nginx

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

