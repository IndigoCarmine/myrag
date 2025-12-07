FROM python:3.10-slim

WORKDIR /app

# Install build dependencies potentially needed for some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies
# Note: For GPU support in production you might want a different base image (e.g. nvidia/cuda)
# or install torch with cuda support specifically.
# For local simple usage, this installs standard torch.
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
