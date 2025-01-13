import numpy as np
import pandas as pd
from datetime import datetime

# Fetch data
def fetch_data():
    return read_csv()

def read_csv():
    data = pd.read_csv('./data_stocks_n/NIFTY50-15.csv')
    data = data[['date', 'open', 'low', 'high', 'close']]
    data.rename(columns={'date': 'Datetime'}, inplace=True)
    data['Datetime'] = pd.to_datetime(data['Datetime'], format='%Y-%m-%d %H:%M:%S%z')  # Adjust the format as needed
    data.set_index('Datetime', inplace=True)
    data.index = data.index.tz_localize(None)
    data = data.dropna()
    return data

def apply_strategy(df, sl_points=100):
    results = []
    df['Date'] = df.index.date  # Extract the date for grouping
    position = None
    points_gained = 0
    # Group data by each day
    grouped = df.groupby('Date')

    for date, group in grouped:
        # Filter the group to find the 10:00 AM candle
        entry_candle = group.between_time("10:00", "10:00")
        if entry_candle.empty:
            # Skip the day if 10:00 AM candle is not available
            continue

        entry_price = entry_candle.iloc[0]['close']  # Entry price at 10:00 AM
        sl_hit = False

        for i, row in group.iterrows():
            high = row['high']

            # Check if SL is hit
            if high >= entry_price + sl_points:  # SL for short position
                results.append({
                    'Date': date,
                    'Position': 'Short',
                    'Trade Outcome': 'SL Hit',
                    'Entry Price': entry_price,
                    'Exit Price': entry_price + sl_points,
                    'Points Gained': -(sl_points),  # Loss
                    'Exit Time': i
                })
                sl_hit = True
                break

        # If SL not hit, close at the last timestamp
        if not sl_hit:
            last_close = group.iloc[-1]['close']
            last_time = group.index[-1]
            position = 'Short'
            points_gained = entry_price - last_close
                
            results.append({
                'Date': date,
                'Position': position,
                'Trade Outcome': 'Closed End of Day',
                'Entry Price': entry_price,
                'Exit Price': last_close,
                'Points Gained': round(points_gained, 2),
                'Exit Time': last_time
            })

    return pd.DataFrame(results)


# Main function
def main():
    df = fetch_data()
    strategy_results = apply_strategy(df)

    # Separate the results into long and short positions
    long_results = strategy_results[strategy_results['Position'] == 'Long']
    short_results = strategy_results[strategy_results['Position'] == 'Short']

    # Calculate total points gained for long and short positions
    total_long_points = long_results['Points Gained'].sum()
    total_short_points = short_results['Points Gained'].sum()

    # Calculate Win Ratio
    total_trades = len(strategy_results)
    winning_trades = len(strategy_results[strategy_results['Points Gained'] > 0])
    win_ratio = winning_trades / total_trades if total_trades > 0 else 0

    # Calculate Maximum Drawdown
    equity_curve = strategy_results['Points Gained'].cumsum()  # Cumulative sum of points
    peak = equity_curve.cummax()  # Track the running maximum (peak)
    drawdown = equity_curve - peak  # Calculate the drawdown
    max_drawdown = drawdown.min()  # Maximum drawdown

    # Print results
    print("Total Points Gained (Long):", round(total_long_points, 2))
    print("Total Points Gained (Short):", round(total_short_points, 2))
    print("Win Ratio:", round(win_ratio, 2))
    print("Maximum Drawdown:", round(max_drawdown, 2))

    # Optionally save the results to a CSV file
    strategy_results.to_csv('strategy_results_short.csv', index=False)
    # print(strategy_results)


if __name__ == "__main__":
    main()
