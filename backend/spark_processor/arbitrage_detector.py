from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

class ArbitrageDetector:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("ArbitrageDetector") \
            .getOrCreate()
        
        # Seuils de configuration
        self.min_arbitrage_percentage = 0.5  # 0.5% minimum
        self.max_latency_seconds = 10        # 10 secondes max de latence
        self.min_volume_usd = 1000          # 1000$ minimum de volume
    
    def detect_arbitrage_opportunities(self):
        """Détecte les opportunités d'arbitrage en temps réel"""
        
        # Lecture du flux unifié de tous les exchanges
        kafka_df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", "all-exchanges") \
            .load()
        
        # Schema pour les données multi-exchange
        exchange_schema = StructType([
            StructField("exchange", StringType()),
            StructField("symbol", StringType()),
            StructField("price", DoubleType()),
            StructField("volume", DoubleType()),
            StructField("timestamp", StringType()),
            StructField("trade_id", StringType())
        ])
        
        # Parse JSON et nettoyage
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), exchange_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")
        
        # Filtrage des symboles supportés et conversion timestamp
        clean_df = parsed_df.filter(
            col("symbol").isin(["btcusdt", "ethusd", "ethusdt", "btcusd"])
        ).withColumn(
            "normalized_symbol", 
            regexp_replace(col("symbol"), "(usd|usdt)", "")
        ).withColumn(
            "event_time", 
            to_timestamp(col("timestamp"))
        )
        
        # Fenêtre glissante pour détecter les arbitrages
        windowed_df = clean_df \
            .withWatermark("event_time", "30 seconds") \
            .groupBy(
                window(col("event_time"), "5 seconds"),
                col("normalized_symbol")
            ) \
            .agg(
                collect_list(struct(
                    col("exchange"),
                    col("price"),
                    col("volume"),
                    col("event_time")
                )).alias("exchange_data")
            )
        
        # Calcul des opportunités d'arbitrage
        arbitrage_df = windowed_df.select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("normalized_symbol"),
            self.calculate_arbitrage_udf(col("exchange_data")).alias("arbitrage_info")
        ).filter(
            col("arbitrage_info.arbitrage_percentage") > self.min_arbitrage_percentage
        )
        
        return arbitrage_df
    
    def calculate_arbitrage_udf(self, exchange_data_col):
        """UDF pour calculer les opportunités d'arbitrage"""
        from pyspark.sql.functions import udf
        from pyspark.sql.types import StructType, StructField, StringType, DoubleType
        
        def calculate_arbitrage(exchange_data):
            if not exchange_data or len(exchange_data) < 2:
                return None
            
            # Groupe par exchange et calcule prix moyen
            exchange_prices = {}
            for trade in exchange_data:
                exchange = trade['exchange']
                price = float(trade['price'])
                volume = float(trade['volume'])
                
                if exchange not in exchange_prices:
                    exchange_prices[exchange] = {'total_value': 0, 'total_volume': 0}
                
                exchange_prices[exchange]['total_value'] += price * volume
                exchange_prices[exchange]['total_volume'] += volume
            
            # Calcule prix moyen pondéré par volume
            avg_prices = {}
            for exchange, data in exchange_prices.items():
                if data['total_volume'] > 0:
                    avg_prices[exchange] = data['total_value'] / data['total_volume']
            
            if len(avg_prices) < 2:
                return None
            
            # Trouve le prix min et max
            min_exchange = min(avg_prices, key=avg_prices.get)
            max_exchange = max(avg_prices, key=avg_prices.get)
            min_price = avg_prices[min_exchange]
            max_price = avg_prices[max_exchange]
            
            # Calcule le pourcentage d'arbitrage
            arbitrage_percentage = ((max_price - min_price) / min_price) * 100
            
            # Estime le volume disponible (minimum des deux exchanges)
            min_volume = min(
                exchange_prices[min_exchange]['total_volume'],
                exchange_prices[max_exchange]['total_volume']
            )
            
            return {
                'buy_exchange': min_exchange,
                'sell_exchange': max_exchange,
                'buy_price': min_price,
                'sell_price': max_price,
                'arbitrage_percentage': arbitrage_percentage,
                'potential_volume': min_volume,
                'potential_profit_usd': (max_price - min_price) * min_volume
            }
        
        return_schema = StructType([
            StructField("buy_exchange", StringType()),
            StructField("sell_exchange", StringType()),
            StructField("buy_price", DoubleType()),
            StructField("sell_price", DoubleType()),
            StructField("arbitrage_percentage", DoubleType()),
            StructField("potential_volume", DoubleType()),
            StructField("potential_profit_usd", DoubleType())
        ])
        
        return udf(calculate_arbitrage, return_schema)(exchange_data_col)
    
    def start_arbitrage_detection(self):
        """Lance la détection d'arbitrage en streaming"""
        arbitrage_stream = self.detect_arbitrage_opportunities()
        
        # Prépare les données pour Kafka
        output_df = arbitrage_stream.select(
            col("normalized_symbol").alias("key"),
            to_json(struct(
                col("normalized_symbol").alias("symbol"),
                col("window_start"),
                col("window_end"),
                col("arbitrage_info.buy_exchange"),
                col("arbitrage_info.sell_exchange"),
                col("arbitrage_info.buy_price"),
                col("arbitrage_info.sell_price"),
                col("arbitrage_info.arbitrage_percentage"),
                col("arbitrage_info.potential_volume"),
                col("arbitrage_info.potential_profit_usd"),
                current_timestamp().alias("detection_time")
            )).alias("value")
        )
        
        # Écrit vers topic Kafka
        query = output_df.writeStream \
            .outputMode("append") \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("topic", "arbitrage-opportunities") \
            .option("checkpointLocation", "/tmp/spark-checkpoint-arbitrage") \
            .start()
        
        return query

if __name__ == "__main__":
    detector = ArbitrageDetector()
    query = detector.start_arbitrage_detection()
    query.awaitTermination()