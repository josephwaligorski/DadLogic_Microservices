# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py ./

# Expose port 8080
EXPOSE 8080

# Run the Flask app
ENTRYPOINT ["python", "server.py"]