
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables
# In a real deployment, these would be set by the hosting provider
ENV FLASK_APP=wsgi:app
ENV SECRET_KEY="a_very_secret_and_random_key_that_should_be_changed_in_production"
ENV DATABASE="/data/notes.db"

# Create a volume for the database to persist data
VOLUME /data

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
