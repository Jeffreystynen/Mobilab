# Use a base image with Python
FROM python:3.10-slim

# Set environment variables for Flask
ENV FLASK_APP=main.py

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the Flask port
EXPOSE 5000

# Command to run the application
CMD ["flask", "run"]
