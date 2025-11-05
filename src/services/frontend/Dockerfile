# Frontend Dockerfile
# Simple nginx server for static HTML/JS

FROM nginx:alpine

# Copy static files
COPY index.html /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY config.js /usr/share/nginx/html/

# Copy nginx config (optional, using default for now)
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

# Update nginx to listen on 8080 instead of 80
RUN sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
