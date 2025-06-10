# Base image
FROM python:latest

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Command to run the script
CMD ["python", "weekly_report.py"]