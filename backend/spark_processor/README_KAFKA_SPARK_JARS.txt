Problème détecté :
Le conteneur Spark s'arrête à cause de l'erreur :
  Caused by: java.lang.ClassNotFoundException: org.apache.spark.kafka010.KafkaConfigUpdater

Cela signifie que le connecteur Spark-Kafka n'est pas complet ou qu'il manque des dépendances.

Solution recommandée :
1. Ajouter les JARs suivants dans l'image Docker Spark :
   - spark-sql-kafka-0-10_2.12-3.4.1.jar
   - spark-streaming-kafka-0-10_2.12-3.4.1.jar
   - kafka-clients-3.4.0.jar
   - **commons-pool2-2.11.1.jar**
   - **spark-token-provider-kafka-0-10_2.12-3.4.1.jar**

2. Adapter le Dockerfile Spark comme suit :

RUN wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-10_2.12/3.4.1/spark-streaming-kafka-0-10_2.12-3.4.1.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar -P /opt/spark/jars/ && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar -P /opt/spark/jars/

3. Rebuild l'image Spark puis relancer le conteneur.

Sans ces JARs, Spark ne peut pas consommer Kafka en streaming.
