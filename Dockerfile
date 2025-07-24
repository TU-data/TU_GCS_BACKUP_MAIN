# Use an official lightweight Python image.
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# Install uv, the fast Python installer
RUN pip install uv

# Copy only the dependency configuration file
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv pip sync pyproject.toml --system

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
# Use uvicorn to run the FastAPI application.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]