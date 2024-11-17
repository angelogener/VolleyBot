FROM python:3.14.0a1-slim
ENV TZ="America/New_York"
WORKDIR /usr/src/app
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY ./ ./
CMD ["python", "main.py"]
