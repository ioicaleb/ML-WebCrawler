# Use an official, lightweight Python runtime image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Crucial: Tell Python to include the root directory when resolving package names
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Install system dependencies required for Flet's headless system backend
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libmpv2 \
    libsecret-1-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker's build cache layers
COPY requirements.txt .

# Install Flet optimized explicitly for cloud-web servers
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "flet[web]"

# Copy the rest of your application code into the container
COPY . .

# Expose the default Flet web port
EXPOSE 8502

# Run the app targeting main.py inside your src/ folder
CMD ["python", "src/main.py"]