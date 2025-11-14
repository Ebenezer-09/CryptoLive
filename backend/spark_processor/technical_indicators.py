from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from pyspark.sql.types import *

def calculate_rsi(df, period=14):
    """Calcule l'indicateur RSI (Relative Strength Index)"""
    window_spec = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-period, 0)
    
    # Calcul des gains et pertes
    df_with_changes = df.withColumn(
        "price_change", 
        col("price") - lag("price").over(Window.partitionBy("symbol").orderBy("timestamp"))
    )
    
    df_with_gains = df_with_changes.withColumn(
        "gain", when(col("price_change") > 0, col("price_change")).otherwise(0)
    ).withColumn(
        "loss", when(col("price_change") < 0, -col("price_change")).otherwise(0)
    )
    
    # Moyennes mobiles des gains/pertes
    df_with_avg = df_with_gains.withColumn(
        "avg_gain", avg("gain").over(window_spec)
    ).withColumn(
        "avg_loss", avg("loss").over(window_spec)
    )
    
    # Calcul RSI
    rsi_df = df_with_avg.withColumn(
        "rs", col("avg_gain") / col("avg_loss")
    ).withColumn(
        "rsi", 100 - (100 / (1 + col("rs")))
    )
    
    return rsi_df

def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """Calcule l'indicateur MACD (Moving Average Convergence Divergence)"""
    window_fast = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-fast_period, 0)
    window_slow = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-slow_period, 0)
    window_signal = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-signal_period, 0)
    
    macd_df = df.withColumn(
        "ema_fast", avg("price").over(window_fast)
    ).withColumn(
        "ema_slow", avg("price").over(window_slow)
    ).withColumn(
        "macd_line", col("ema_fast") - col("ema_slow")
    ).withColumn(
        "signal_line", avg("macd_line").over(window_signal)
    ).withColumn(
        "macd_histogram", col("macd_line") - col("signal_line")
    )
    
    return macd_df

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calcule les Bandes de Bollinger"""
    window_spec = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-period, 0)
    
    bb_df = df.withColumn(
        "sma", avg("price").over(window_spec)
    ).withColumn(
        "price_std", stddev("price").over(window_spec)
    ).withColumn(
        "upper_band", col("sma") + (col("price_std") * std_dev)
    ).withColumn(
        "lower_band", col("sma") - (col("price_std") * std_dev)
    ).withColumn(
        "bb_position", (col("price") - col("lower_band")) / (col("upper_band") - col("lower_band"))
    )
    
    return bb_df

# Fonction principale d'enrichissement
def enrich_with_indicators(df):
    """Enrichit les données avec tous les indicateurs techniques"""
    df_rsi = calculate_rsi(df)
    df_macd = calculate_macd(df_rsi)
    df_bb = calculate_bollinger_bands(df_macd)
    
    return df_bb.select(
        "symbol", "price", "timestamp",
        "rsi", "macd_line", "signal_line", "macd_histogram",
        "upper_band", "lower_band", "bb_position"
    )