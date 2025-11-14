from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, min, max, count, stddev, to_json, struct, window, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

spark = SparkSession.builder.appName("BinanceSparkStreaming").getOrCreate()

# Lecture du flux Kafka
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "binance-stream") \
    .load()

# Schéma pour les données Binance (champ "data" dans le message)
data_schema = StructType([
    StructField("s", StringType()),
    StructField("p", StringType()),
    StructField("E", StringType())
])

schema = StructType([
    StructField("stream", StringType()),
    StructField("data", data_schema)
])

# Parsing JSON et ajout timestamp (utiliser le timestamp de l'événement)
json_df = kafka_df.select(from_json(col("value").cast("string"), schema).alias("parsed"))
clean_df = json_df.select(
    col("parsed.data.s").alias("symbol"),
    col("parsed.data.p").cast("double").alias("price"),
    (col("parsed.data.`E`").cast("long") / 1000).cast("timestamp").alias("timestamp")
)

# Agrégation avancée : statistiques complètes par symbole (fenêtre glissante de 5 minutes)
windowed_agg = clean_df \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(
        col("symbol"),
        window(col("timestamp"), "5 minutes")
    ) \
    .agg(
        avg("price").alias("avg_price"),
        min("price").alias("min_price"),
        max("price").alias("max_price"),
        count("price").alias("trade_count"),
        stddev("price").alias("volatility")
    )

# Calcul de tendance : variation moyenne sur la fenêtre
trend_df = windowed_agg.withColumn(
    "trend", (col("max_price") - col("min_price")) / col("avg_price") * 100
)

# Préparer pour Kafka : clé = symbol, valeur = JSON avec toutes les métriques
agg_to_kafka = trend_df.select(
    col("symbol").alias("key"),
    to_json(struct(
        col("symbol"),
        col("avg_price"),
        col("min_price"),
        col("max_price"),
        col("trade_count"),
        col("volatility"),
        col("trend"),
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end")
    )).alias("value")
)

# Écriture dans le topic Kafka 'binance-agg'
query = agg_to_kafka.writeStream \
    .outputMode("update") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", "binance-agg") \
    .option("checkpointLocation", "/tmp/spark-checkpoint-agg") \
    .start()

query.awaitTermination()
