FROM parsafadaeei/telegram-bot:latest

RUN apk add --no-cache aria2 curl unzip nodejs ffmpeg && \
    curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip && \
    unzip rclone-current-linux-amd64.zip && \
    cp rclone-*-linux-amd64/rclone /usr/bin/rclone && \
    chmod +x /usr/bin/rclone && \
    rm -rf rclone-* && \
    pip install -U yt-dlp "yt-dlp[default]" --break-system-packages

WORKDIR /app
CMD ["python3", "main.py"]
