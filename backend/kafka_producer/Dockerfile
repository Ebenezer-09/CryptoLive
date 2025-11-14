FROM python:3.10
WORKDIR /app
COPY producer_binance.py .
RUN pip install kafka-python websocket-client
CMD ["python", "producer_binance.py"]
