# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Bangkok

# Install dotenv if not already installed
RUN pip install python-dotenv

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose the port for the bot
EXPOSE 5000

# Default command to run bot.py
CMD ["python", "-m", "discord_bot.bot"]
