# Use a base image with Python
FROM python:3.10-slim

# Set environment variables for Flask
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y \
    libgirepository-1.0-1 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    gir1.2-pango-1.0 \
    && apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the Flask port
EXPOSE 5000

# Command to run the application using Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
