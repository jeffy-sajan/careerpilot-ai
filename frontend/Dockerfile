# ────────────────────────────────────────────
# Stage 1 — Builder
# Install dependencies and build the Vite app.
# ────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first to leverage Docker layer caching.
# If package.json hasn't changed, npm install will be skipped on rebuild.
COPY package.json package-lock.json ./

RUN npm ci --frozen-lockfile

# Copy the rest of the application source
COPY . .

# Build the production bundle (outputs to /app/dist)
RUN npm run build

# ────────────────────────────────────────────
# Stage 2 — Production Server
# Serve the built assets with Nginx.
# ────────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Copy built assets from the builder stage into nginx's serve directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx config (SPA routing support, gzip, etc.)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Nginx runs in foreground mode inside container
CMD ["nginx", "-g", "daemon off;"]
