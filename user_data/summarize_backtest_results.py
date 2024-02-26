import os
import json
from datetime import datetime

def list_result_files(folder_path):
    """
    List and sort all relevant JSON result files in the specified folder, excluding .last_result.json and .meta.json files.
    """
    files = [f for f in os.listdir(folder_path) if f.endswith('.json') and not f.endswith('.last_result.json') and not f.endswith('.meta.json')]
    # Assuming file names include sortable dates, sort the list
    files.sort()
    return files

def process_file(file_path):
    """
    Open and process a single JSON file, extracting the necessary metrics.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
        strategy_data = data['strategy']['FlowerPowerX']
        
        # Extract required information
        start_date = datetime.strptime(strategy_data['backtest_end'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m")
        metrics = {
            "wins": strategy_data['wins'],
            "losses": strategy_data['losses'],
            "draws": strategy_data['draws'],
            "losing_days": strategy_data['losing_days'],
            "draw_days": strategy_data['draw_days'],
            "winning_days": strategy_data['winning_days'],
            "trades_per_day": strategy_data['trades_per_day'],
            "total_trades": strategy_data['total_trades'],
            "profit_usd": strategy_data['profit_total_abs'],
            "start_balance": strategy_data['starting_balance'],
            "final_balance": strategy_data['final_balance'],
            "winrate": strategy_data['winrate'],
            "max_drawdown": strategy_data['max_drawdown'],
            "drawdown_start": strategy_data['drawdown_start'],
            "drawdown_end": strategy_data['drawdown_end'],
            "cagr": strategy_data['cagr'],
            "sortino": strategy_data['sortino'],
            "sharpe": strategy_data['sharpe'],
            "calmar": strategy_data['calmar'],
            "percent_profit_month": strategy_data['profit_total'],
            "market_change": strategy_data['market_change']
        }

        return start_date, metrics

def aggregate_results(results):
    """
    Aggregate metrics from all processed files.
    """
    aggregated = {
        "total_wins": sum(item['wins'] for item in results.values()),
        "total_losses": sum(item['losses'] for item in results.values()),
        "total_draws": sum(item['draws'] for item in results.values()),
        "total_profit_usd": sum(item['profit_usd'] for item in results.values()),
        "total_trades": sum(item['total_trades'] for item in results.values()),
    }
    aggregated['average_winrate'] = sum(item['winrate'] for item in results.values()) / len(results)
    return aggregated

def print_summary(month, metrics):
    """
    Print a summary for a single result dictionary.
    """
    print(f"| {month} | {metrics['wins']} | {metrics['losses']} | {metrics['draws']} | {metrics['losing_days']} | {metrics['draw_days']} | {metrics['winning_days']} | {metrics['trades_per_day']:.2f} | {metrics['total_trades']} | {metrics['profit_usd']:.2f} | {metrics['start_balance']:.2f} | {metrics['final_balance']:.2f} | {metrics['winrate']:.2%} | {metrics['max_drawdown']:.2f} | {metrics['drawdown_start']} | {metrics['drawdown_end']} | {metrics['cagr']:.2f} | {metrics['sortino']:.2f} | {metrics['sharpe']:.2f} | {metrics['calmar']:.2f} |{metrics['percent_profit_month']:.2f} | {metrics['market_change']:.2f} |")

def print_aggregated_summary(aggregated):
    """
    Print the aggregated summary of all results.
    """
    print("\nAggregated Summary:")
    print(f"Total Wins: {aggregated['total_wins']}")
    print(f"Total Losses: {aggregated['total_losses']}")
    print(f"Total Draws: {aggregated['total_draws']}")
    print(f"Total Trades: {aggregated['total_trades']}")
    print(f"Total Profit USD: {aggregated['total_profit_usd']:.2f}")
    print(f"Average Winrate: {aggregated['average_winrate']:.2%}")

def print_header():
    print("| Month | Wins | Losses | Draws | Losing Days | Draw Days | Winning Days | Trades Per Day | Total Trades | Profit USD | Start Balance | Final Balance | Winrate | Max Drawdown | Drawdown Start | Drawdown End | CAGR | Sortino | Sharpe | Calmar | % Profit Month | Market Change |")

def main(folder_path):
    files = list_result_files(folder_path)
    if not files:
        print("No result files found.")
        return
    
    results = {}
    print_header()
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        month, metrics = process_file(file_path)
        results[month] = metrics
        print_summary(month, metrics)
    
    aggregated = aggregate_results(results)
    print_aggregated_summary(aggregated)

if __name__ == "__main__":
    folder_path = "backtest_results"  # Change this to your actual folder path
    main(folder_path)
