FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S highway && \
    adduser -S highway -u 1001

# Change ownership
RUN chown -R highway:highway /app
USER highway

# Expose ports
EXPOSE 9000 9001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:9001/api/v1/status', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

# Start
CMD ["node", "vortex.js", "--web"]
