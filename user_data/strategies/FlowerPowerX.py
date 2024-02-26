# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair, informative)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class FlowerPowerX(IStrategy):
    
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.04

    # Trailing stoploss
    trailing_stop = True
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.010  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Strategy parameters
    # tbd

    # Optional order type mapping.
    order_types = {
        'entry': 'market',
        'exit': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }
    
    @property
    def plot_config(self):
        return {
            'main_plot': {
                'neckline_upper_1h': {'color': 'orange'},
                'neckline_1h': {'color': 'blue'},
                'neckline_lower_1h': {'color': 'orange'},
            },
            'subplots': {
                "hs": {
                    'bullish_hs_1h': {'color': 'green'},
                    'bearish_hs_1h': {'color': 'red'}
                },
                "rsi": {
                    'rsi_1h': {'color': 'orange'},
                    'rsi_ma_1h': {'color': 'blue'}
                },
                "volume": {
                    'volume_1h': {'color': 'orange'},
                    'volume_ma_1h': {'color': 'blue'}
                }
            }
        }
    
    @informative('1h')
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = detect_head_and_shoulders(dataframe)
        #dataframe['rsi'] = ta.RSI(dataframe)
        #dataframe['rsi_ma'] = dataframe['rsi'].rolling(window=20).mean()
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['neckline_upper'] = dataframe['neckline'] + dataframe['atr']
        dataframe['neckline_lower'] = dataframe['neckline'] - dataframe['atr']
        #dataframe['volume_ma'] = dataframe['volume'].rolling(window=20).mean()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['bullish_hs_1h'] == 1) &
                (qtpylib.crossed_above(dataframe['close'], dataframe['neckline_lower_1h'])) &
                (dataframe['close'] < dataframe['neckline_upper_1h']) 

                # NOTE: Reduces Drawdown a little but on the other hand side number of trades and winrate are slightly reduced too
                # & (dataframe['volume_ma_1h'].shift(12) < dataframe['volume_ma_1h'])
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['close'], dataframe['neckline_upper_1h'])) 
            ),
            'exit_long'] = 1
        return dataframe

def find_pivot_highs(dataframe, leftbars, rightbars):
    """Find pivot highs in the dataframe."""
    highs = dataframe['high']
    pivot_highs = highs[(highs.shift(leftbars) < highs) & (highs.shift(-rightbars) < highs)]
    return pivot_highs

def find_pivot_lows(dataframe, leftbars, rightbars):
    """Find pivot lows in the dataframe."""
    lows = dataframe['low']
    pivot_lows = lows[(lows.shift(leftbars) > lows) & (lows.shift(-rightbars) > lows)]
    return pivot_lows

def detect_head_and_shoulders(dataframe, leftbars=4, rightbars=4, threshold=10):
    dataframe['bullish_hs'] = 0
    dataframe['bearish_hs'] = 0
    dataframe['neckline'] = np.nan  # Initialize with NaN

    pivot_highs = find_pivot_highs(dataframe, leftbars, rightbars)
    pivot_lows = find_pivot_lows(dataframe, leftbars, rightbars)

    for i in range(len(dataframe)):
        if i < leftbars or i > len(dataframe) - rightbars - 1:
            continue
        
        # Check for Bullish Inverse Head and Shoulders Pattern
        if i in pivot_lows.index and i - 1 in pivot_lows.index and i + 1 in pivot_lows.index:
            if pivot_lows[i] < pivot_lows[i - 1] and pivot_lows[i] < pivot_lows[i + 1]:
                neckline_value = (dataframe.at[i-rightbars, 'high'] + dataframe.at[i+leftbars, 'high']) / 2
                for j in range(threshold + 1):
                    if i+j >= len(dataframe):
                        break
                    # Reset bearish pattern if previously detected
                    dataframe.at[i+j, 'bearish_hs'] = 0
                    dataframe.at[i+j, 'bullish_hs'] = 1
                    dataframe.at[i+j, 'neckline'] = neckline_value

        # Check for Bearish Head and Shoulders Pattern
        if i in pivot_highs.index and i - 1 in pivot_highs.index and i + 1 in pivot_highs.index:
            if pivot_highs[i] > pivot_highs[i - 1] and pivot_highs[i] > pivot_highs[i + 1]:
                neckline_value = (dataframe.at[i-rightbars, 'low'] + dataframe.at[i+leftbars, 'low']) / 2
                for j in range(threshold + 1):
                    if i+j >= len(dataframe) or dataframe.at[i+j, 'bearish_hs'] == 1:
                        break
                    # Reset bullish pattern if previously detected
                    dataframe.at[i+j, 'bullish_hs'] = 0
                    dataframe.at[i+j, 'bearish_hs'] = 1
                    dataframe.at[i+j, 'neckline'] = neckline_value

    return dataframe
