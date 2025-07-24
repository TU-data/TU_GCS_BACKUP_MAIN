# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# Install Rye
RUN pip install rye

# Copy dependency files
COPY pyproject.toml rye.lock* ./

# Install dependencies using Rye
RUN rye sync --no-lock

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
# Use uvicorn to run the FastAPI application.
# The host 0.0.0.0 makes the server accessible from outside the container.
# The port 8080 is a common choice for web applications.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
