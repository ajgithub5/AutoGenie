# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Expose ports for Streamlit (8501) and FastAPI (8000)
EXPOSE 8501 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV BACKEND_URL=http://localhost:8000

# Create a startup script
RUN echo '#!/bin/bash\n\
python main.py &\n\
sleep 5\n\
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0' > /app/start.sh && \
chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
