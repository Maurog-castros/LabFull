# Stage 1: Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy only package files for caching
COPY package*.json ./

# Install dependencies (if any)
RUN npm install --production || true

# Copy application files
COPY . .

# Stage 2: Production stage
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
