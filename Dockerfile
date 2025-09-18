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
COPY --from=backend-builder /usr/local/bin/uvicorn /usr/local/bin/

# Copy the application source code and the frontend files
COPY --from=backend-builder /app/main.py /app/main.py
COPY --from=backend-builder /app/core /app/core
COPY --from=backend-builder /app/frontend /app/frontend

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
