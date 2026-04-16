FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY auto_reply.py login.py ./

# Railway will mount a persistent volume here (optional but recommended)
VOLUME ["/data"]

CMD ["python", "-u", "auto_reply.py"]
