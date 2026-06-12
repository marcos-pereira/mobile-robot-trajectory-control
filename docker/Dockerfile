FROM python:3.12-slim

LABEL maintainer="marcos-pereira"
LABEL description="Mobile robot trajectory control connecting to CoppeliaSim via ZMQ remote API"

WORKDIR /workspace

# Install Python dependencies (baked into the image; code is mounted at runtime)
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py", "parameters1.yaml"]
