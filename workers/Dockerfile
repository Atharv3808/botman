FROM node:18-slim
WORKDIR /app
COPY . .
# Keep the container running for status check
CMD ["sh", "-c", "echo Worker started! && tail -f /dev/null"]
