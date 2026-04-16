FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY auto_reply.py login.py ./

# Mount a Railway volume at /data via the dashboard (Settings -> Volumes)
# to persist greeted_users.json across redeploys.

CMD ["python", "-u", "auto_reply.py"]
