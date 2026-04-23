# Frontend Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arguments
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY app/package*.json ./

# Install dependencies
RUN npm install

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy source code
COPY app/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY ../nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]