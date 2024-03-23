FROM python:3.10.11
RUN apt-get update && apt-get install -y iputils-ping
ADD . /app
# 删除 venv
RUN rm -rf /app/venv
RUN rm -rf /app/.idea
RUN rm -rf /app/html/.idea
RUN rm -rf /app/logs/*
WORKDIR /app
EXPOSE 8000
RUN pip install -r requirements.txt
CMD ["python", "./main.py", "-W"]