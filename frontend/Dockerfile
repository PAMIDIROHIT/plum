# =====================================================================
# Dockerfile for Plum OPD Adjudication Next.js Frontend
# =====================================================================

# Use an official Node.js runtime as the base image (Node 18 is stable and compatible)
FROM node:18-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker layer caching
COPY package*.json ./

# Install npm dependencies inside the container
RUN npm ci --legacy-peer-deps

# Copy the rest of the frontend source files
COPY . .

# Expose the default port for Next.js dev/prod server
EXPOSE 3000

# Set environment variable to allow Next.js telemetry disable
ENV NEXT_TELEMETRY_DISABLED=1

# Start the Next.js development server by default
CMD ["npm", "run", "dev"]
