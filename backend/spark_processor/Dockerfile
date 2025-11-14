FROM apache/spark:3.4.1

WORKDIR /app

# Installer les dépendances Kafka pour Spark
RUN wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-10_2.12/3.4.1/spark-streaming-kafka-0-10_2.12-3.4.1.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar -P /opt/spark/jars/

# Créer le répertoire data avec les bonnes permissions
RUN mkdir -p /app/data && chmod 777 /app/data

COPY spark_stream.py .

CMD ["/opt/spark/bin/spark-submit", "--master", "local[*]", "spark_stream.py"]
