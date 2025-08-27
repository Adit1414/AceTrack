# backend/Dockerfile

# Use an official Python runtime
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app /app

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]