FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "numpy==2.2.6"
WORKDIR /app
COPY radio/ ./radio/
RUN python3 -m py_compile radio/broadcast/build_audio.py radio/broadcast/server.py
EXPOSE 10000
CMD ["sh","-c","python3 radio/broadcast/build_audio.py && exec python3 radio/broadcast/server.py"]
