# Stage 1: The builder stage (named 'backend-builder')
FROM python:3.11-slim AS backend-builder

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Stage 2: Create the final, lightweight image
FROM python:3.11-slim
WORKDIR /app

# Copy the installed dependencies and scripts from the builder stage
# Referencing the 'backend-builder' stage.
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin/waitress-serve /usr/local/bin/

# Copy the entire application code directory to ensure all files are included
COPY --from=backend-builder /app /app

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application using Waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "main:app"]