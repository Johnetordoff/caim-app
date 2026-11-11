FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 BEAST_ONLY=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "numpy==2.2.6"
WORKDIR /app
COPY radio/broadcast/server.py ./radio/broadcast/server.py
COPY beast/ ./beast/
RUN python3 -m py_compile radio/broadcast/server.py beast/build_album.py
EXPOSE 10000
CMD ["sh","-c","python3 beast/build_album.py && exec python3 radio/broadcast/server.py"]
