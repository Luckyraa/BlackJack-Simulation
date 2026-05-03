"""
Blackjack Simulation: Generic framework for running multiple strategy comparisons.
Provides a clean interface for running simulations with different strategies and generating reports.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import matplotlib.colors as mcolors
from scipy.stats import norm

from strategy_table import Strategy, ExplicitTableStrategy, NaiveStrategy, CustomTableStrategy
from blackjack_simulator import BlackjackSimulator


@dataclass
class SimulationConfig:
    """Configuration for blackjack simulation runs."""
    num_hands: int = 10**4
    rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.rules is None:
            self.rules = {
                'allow_splits': True,
                'double_after_split': True,
                'dealer_hits_soft_17': False
            }


@dataclass
class StrategyConfig:
    """Configuration for a strategy to be tested."""
    name: str
    strategy_class: type
    description: str
    color: str = 'blue'


class SimulationRunner:
    """Generic simulation runner that can test multiple strategies."""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.results: Dict[str, BlackjackSimulator] = {}
    
    def add_strategy(self, strategy_config: StrategyConfig) -> None:
        """Add a strategy to be tested."""
        strategy_instance = strategy_config.strategy_class()
        simulator = BlackjackSimulator(
            self.config.num_hands, 
            strategy_instance, 
            self.config.rules
        )
        self.results[strategy_config.name] = {
            'simulator': simulator,
            'config': strategy_config
        }
    
    def run_all(self) -> None:
        """Run simulations for all added strategies."""
        for name, data in self.results.items():
            print(f"Running simulation for {name}...")
            data['simulator'].run()
        print("All simulations complete!")
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all strategies."""
        stats = {}
        for name, data in self.results.items():
            sim = data['simulator']
            
            # Calculate total number of results (including split hands)
            total_results = (sim.stats['win'] + sim.stats['lose'] + sim.stats['push'] + 
                           sim.stats['win_blackjack'] + sim.stats['lose_blackjack'] + 
                           sim.stats['surrender'])
            
            stats[name] = {
                'total_hands': self.config.num_hands,
                'total_results': total_results,
                'wins': sim.stats['win'],
                'losses': sim.stats['lose'],
                'pushes': sim.stats['push'],
                'blackjack_wins': sim.stats['win_blackjack'],
                'blackjack_losses': sim.stats['lose_blackjack'],
                'surrenders': sim.stats['surrender'],
                'total_money': sim.stats['money'],
                'total_bet': sim.stats['total_bet'],
                'avg_return_per_hand': sim.stats['money'] / self.config.num_hands,
                'win_rate': sim.stats['win'] / total_results,
                'money_curve': sim.stats['money_curve'],
                'strategy_table_frequencies': sim.stats['strategy_table_frequencies'],
                'strategy_table_wins': sim.stats['strategy_table_wins'],
            }
        return stats


class ReportGenerator:
    """Generates various types of reports from simulation results."""
    
    @staticmethod
    def write_text_report(stats: Dict[str, Dict[str, Any]], filename: str = 'results.txt') -> None:
        """Write a comprehensive text report."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("BLACKJACK STRATEGY COMPARISON REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            for strategy_name, data in stats.items():
                f.write(f"STRATEGY: {strategy_name.upper()}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Initial hands played: {data['total_hands']:,}\n")
                f.write(f"Total results (including splits): {data['total_results']:,}\n")
                
                # Calculate total wins (regular + blackjack)
                total_wins = data['wins'] + data['blackjack_wins']
                total_losses = data['losses'] + data['blackjack_losses'] + data['surrenders']
                total_win_rate = total_wins / data['total_results']
                total_lose_rate = total_losses / data['total_results']
                draw_rate = data['pushes'] / data['total_results']
                
                f.write(f"Regular Wins: {data['wins']:,} ({data['wins']/data['total_results']:.2%})\n")
                f.write(f"Blackjack Wins: {data['blackjack_wins']:,} ({data['blackjack_wins']/data['total_results']:.2%})\n")
                f.write(f"Total Wins: {total_wins:,} ({total_win_rate:.2%})\n")
                f.write(f"Regular Losses: {data['losses']:,} ({data['losses']/data['total_results']:.2%})\n")
                f.write(f"Blackjack Losses: {data['blackjack_losses']:,} ({data['blackjack_losses']/data['total_results']:.2%})\n")
                f.write(f"Surrenders: {data['surrenders']:,} ({data['surrenders']/data['total_results']:.2%})\n")
                f.write(f"Total Losses: {total_losses:,} ({total_lose_rate:.2%})\n")
                f.write(f"Pushes: {data['pushes']:,} ({draw_rate:.2%})\n")
                f.write(f"Total money won/lost: ${data['total_money']:,.2f}\n")
                f.write(f"Total bet: ${data['total_bet']:,.2f}\n")
                f.write(f"Average return per hand: ${data['avg_return_per_hand']:.4f}\n")
                f.write(f"ROI: {(data['total_money'] / data['total_bet'] * 100):.2f}%\n")
                f.write("\n")
    
    @staticmethod
    def write_json_report(stats: Dict[str, Dict[str, Any]], filename: str = 'results.json') -> None:
        """Write results in JSON format for programmatic access."""
        # Convert numpy arrays to lists for JSON serialization
        json_stats = {}
        for strategy_name, data in stats.items():
            json_stats[strategy_name] = data.copy()
            # Handle money_curve - it might be a list or numpy array
            money_curve = data['money_curve']
            if hasattr(money_curve, 'tolist'):
                json_stats[strategy_name]['money_curve'] = money_curve.tolist()
            else:
                json_stats[strategy_name]['money_curve'] = money_curve
            # Convert tuple keys to strings for JSON serialization
            if 'strategy_table_frequencies' in data:
                strategy_freq = {}
                for (row, col), freq in data['strategy_table_frequencies'].items():
                    strategy_freq[f"{row},{col}"] = freq
                json_stats[strategy_name]['strategy_table_frequencies'] = strategy_freq
            if 'strategy_table_wins' in data:
                strategy_wins = {}
                for (row, col), wins in data['strategy_table_wins'].items():
                    strategy_wins[f"{row},{col}"] = wins
                json_stats[strategy_name]['strategy_table_wins'] = strategy_wins
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_stats, f, indent=2, default=str)
    
    @staticmethod
    def plot_money_curves(stats: Dict[str, Dict[str, Any]], 
                         strategy_configs: Dict[str, StrategyConfig],
                         filename: str = 'money_vs_hands.png') -> None:
        """Plot money curves for all strategies."""
        plt.figure(figsize=(12, 8))
        
        for strategy_name, data in stats.items():
            config = strategy_configs[strategy_name]
            plt.plot(data['money_curve'], 
                    label=f"{config.name} ({data['avg_return_per_hand']:.4f})", 
                    color=config.color,
                    linewidth=2)
        
        plt.xlabel('Number of Hands Played')
        plt.ylabel('Money ($)')
        plt.title('Money as a Function of Number of Hands Played')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_strategy_table_heatmap(stats: Dict[str, Dict[str, Any]], 
                                   filename: str = 'strategy_table_heatmap.png') -> None:
        """Create a heatmap showing win probability of each hand type in the strategy table."""
        strategy = ExplicitTableStrategy()
        row_labels = strategy.row_labels
        col_labels = strategy.upcard_labels

        win_prob_matrix = np.full((len(row_labels), len(col_labels)), np.nan)

        # Find the optimal strategy data
        optimal_stats = None
        for name, data in stats.items():
            if 'Optimal' in name and 'strategy_table_wins' in data:
                optimal_stats = data
                break

        if optimal_stats is None:
            print("Warning: No optimal strategy with win tracking found for heatmap")
            return

        for (row, col), freq in optimal_stats['strategy_table_frequencies'].items():
            if 0 <= row < len(row_labels) and 0 <= col < len(col_labels):
                wins = optimal_stats['strategy_table_wins'].get((row, col), 0)
                if freq > 0:
                    win_prob_matrix[row, col] = wins / freq * 100  # Win probability in %

        plt.figure(figsize=(14, 10))
        norm = mcolors.Normalize(vmin=0, vmax=100)
        im = plt.imshow(win_prob_matrix, cmap='YlGnBu', aspect='auto', norm=norm)
        plt.xticks(range(len(col_labels)), col_labels)
        plt.yticks(range(len(row_labels)), row_labels)
        cbar = plt.colorbar(im)
        cbar.set_label('Win Probability (%)', rotation=270, labelpad=20)
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                winp = win_prob_matrix[i, j]
                if not np.isnan(winp):
                    plt.text(j, i, f'{winp:.2f}%', 
                             ha='center', va='center', fontsize=8, fontweight='bold', color='black')
        plt.xlabel('Dealer Upcard')
        plt.ylabel('Player Hand')
        plt.title('Empirical Win Probability (%) - Optimal Strategy')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_comparison_chart(stats: Dict[str, Dict[str, Any]], 
                            filename: str = 'strategy_comparison.png') -> None:
        """Create a bar chart comparing key metrics across strategies."""
        strategies = list(stats.keys())
        
        # Calculate all rates properly including blackjack wins/losses and surrenders
        win_rates = [(stats[s]['wins'] + stats[s]['blackjack_wins']) / stats[s]['total_results'] * 100 for s in strategies]
        draw_rates = [stats[s]['pushes'] / stats[s]['total_results'] * 100 for s in strategies]
        lose_rates = [(stats[s]['losses'] + stats[s]['blackjack_losses'] + stats[s]['surrenders']) / stats[s]['total_results'] * 100 for s in strategies]
        avg_returns = [stats[s]['avg_return_per_hand'] * 100 for s in strategies]  # as percentage
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Win/Draw/Lose rate comparison (stacked bars)
        x = range(len(strategies))
        colors = ['blue', 'red', 'green', 'orange', 'purple'][:len(strategies)]
        
        # Create stacked bars
        bars1 = ax1.bar(x, win_rates, label='Win Rate', color=[c for c in colors], alpha=0.8)
        bars2 = ax1.bar(x, draw_rates, bottom=win_rates, label='Draw Rate', 
                       color=[c for c in colors], alpha=0.6)
        bars3 = ax1.bar(x, lose_rates, bottom=[w + d for w, d in zip(win_rates, draw_rates)], 
                       label='Lose Rate', color=[c for c in colors], alpha=0.4)
        
        ax1.set_ylabel('Percentage (%)')
        ax1.set_title('Win/Draw/Lose Rate Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(strategies, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add percentage labels on bars
        for i, (bar1, bar2, bar3) in enumerate(zip(bars1, bars2, bars3)):
            # Win rate label
            height1 = bar1.get_height()
            if height1 > 2:  # Only show label if bar is tall enough
                ax1.text(bar1.get_x() + bar1.get_width()/2., height1/2,
                        f'{height1:.1f}%', ha='center', va='center', fontweight='bold')
            
            # Draw rate label
            height2 = bar2.get_height()
            if height2 > 2:  # Only show label if bar is tall enough
                ax1.text(bar2.get_x() + bar2.get_width()/2., bar2.get_y() + height2/2,
                        f'{height2:.1f}%', ha='center', va='center', fontweight='bold')
            
            # Lose rate label
            height3 = bar3.get_height()
            if height3 > 2:  # Only show label if bar is tall enough
                ax1.text(bar3.get_x() + bar3.get_width()/2., bar3.get_y() + height3/2,
                        f'{height3:.1f}%', ha='center', va='center', fontweight='bold')
        
        # Average return comparison
        bars4 = ax2.bar(strategies, avg_returns, color=colors)
        ax2.set_ylabel('Average Return per Hand (%)')
        ax2.set_title('Average Return Comparison')
        ax2.grid(True, alpha=0.3)
        for bar in bars4:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def plot_strategy_table_win_heatmap(stats: Dict[str, Dict[str, Any]], filename: str = 'strategy_table_win_heatmap.png') -> None:
        """Create a heatmap showing win probability of each hand type in the strategy table."""
        strategy = ExplicitTableStrategy()
        row_labels = strategy.row_labels
        col_labels = strategy.upcard_labels

        win_prob_matrix = np.full((len(row_labels), len(col_labels)), np.nan)

        # Find the optimal strategy data
        optimal_stats = None
        for name, data in stats.items():
            if 'Optimal' in name and 'strategy_table_wins' in data:
                optimal_stats = data
                break

        if optimal_stats is None:
            print("Warning: No optimal strategy with win tracking found for heatmap")
            return

        for (row, col), freq in optimal_stats['strategy_table_frequencies'].items():
            if 0 <= row < len(row_labels) and 0 <= col < len(col_labels):
                wins = optimal_stats['strategy_table_wins'].get((row, col), 0)
                if freq > 0:
                    win_prob_matrix[row, col] = wins / freq * 100  # Win probability in %

        plt.figure(figsize=(14, 10))
        norm = mcolors.Normalize(vmin=0, vmax=100)
        im = plt.imshow(win_prob_matrix, cmap='YlGnBu', aspect='auto', norm=norm)
        plt.xticks(range(len(col_labels)), col_labels)
        plt.yticks(range(len(row_labels)), row_labels)
        cbar = plt.colorbar(im)
        cbar.set_label('Win Probability (%)', rotation=270, labelpad=20)
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                winp = win_prob_matrix[i, j]
                if not np.isnan(winp):
                    plt.text(j, i, f'{winp:.2f}%', 
                             ha='center', va='center', fontsize=8, fontweight='bold', color='black')
        plt.xlabel('Dealer Upcard')
        plt.ylabel('Player Hand')
        plt.title('Empirical Win Probability (%) - Optimal Strategy')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def plot_strategy_table_frequency_heatmap(stats: Dict[str, Dict[str, Any]], filename: str = 'strategy_table_frequency_heatmap.png') -> None:
        """Create a heatmap showing frequency of each hand type in the strategy table."""
        strategy = ExplicitTableStrategy()
        row_labels = strategy.row_labels
        col_labels = strategy.upcard_labels

        freq_matrix = np.zeros((len(row_labels), len(col_labels)))

        # Find the optimal strategy data
        optimal_stats = None
        for name, data in stats.items():
            if 'Optimal' in name and 'strategy_table_frequencies' in data:
                optimal_stats = data
                break

        if optimal_stats is None:
            print("Warning: No optimal strategy with frequency tracking found for heatmap")
            return

        total_hands = optimal_stats['total_results']
        for (row, col), freq in optimal_stats['strategy_table_frequencies'].items():
            if 0 <= row < len(row_labels) and 0 <= col < len(col_labels):
                freq_matrix[row, col] = freq / total_hands * 100  # Convert to percentage

        plt.figure(figsize=(14, 10))
        norm = mcolors.LogNorm(vmin=max(freq_matrix.min(), 1e-3), vmax=freq_matrix.max())
        im = plt.imshow(freq_matrix, cmap='YlOrRd', aspect='auto', norm=norm)
        plt.xticks(range(len(col_labels)), col_labels)
        plt.yticks(range(len(row_labels)), row_labels)
        cbar = plt.colorbar(im)
        cbar.set_label('Frequency (%)', rotation=270, labelpad=20)
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                freq = freq_matrix[i, j]
                plt.text(j, i, f'{freq:.2f}%', 
                         ha='center', va='center', fontsize=8, fontweight='bold', color='black')
        plt.xlabel('Dealer Upcard')
        plt.ylabel('Player Hand')
        plt.title('Strategy Table Hand Frequencies (%) - Optimal Strategy')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def plot_strategy_table_win_minus_lose_heatmap(stats: Dict[str, Dict[str, Any]], filename: str = 'strategy_table_win_minus_lose_heatmap.png') -> None:
        """Create a heatmap showing win ratio minus lose ratio for each hand type in the strategy table."""
        strategy = ExplicitTableStrategy()
        row_labels = strategy.row_labels
        col_labels = strategy.upcard_labels

        win_minus_lose_matrix = np.full((len(row_labels), len(col_labels)), np.nan)

        # Find the optimal strategy data
        optimal_stats = None
        for name, data in stats.items():
            if 'Optimal' in name and 'strategy_table_wins' in data:
                optimal_stats = data
                break

        if optimal_stats is None:
            print("Warning: No optimal strategy with win tracking found for heatmap")
            return

        for (row, col), freq in optimal_stats['strategy_table_frequencies'].items():
            if 0 <= row < len(row_labels) and 0 <= col < len(col_labels):
                wins = optimal_stats['strategy_table_wins'].get((row, col), 0)
                # Count losses for this cell
                # Losses = freq - wins - pushes - surrenders
                pushes = 0
                surrenders = 0
                # If you want to track pushes/surrenders by cell, you would need to add that tracking
                # For now, we assume all non-wins are losses
                if freq > 0:
                    lose = freq - wins  # This will slightly overestimate losses if pushes/surrenders exist
                    win_minus_lose_matrix[row, col] = (wins - lose) / freq * 100

        plt.figure(figsize=(14, 10))
        norm = mcolors.TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)
        im = plt.imshow(win_minus_lose_matrix, cmap='coolwarm', aspect='auto', norm=norm)
        plt.xticks(range(len(col_labels)), col_labels)
        plt.yticks(range(len(row_labels)), row_labels)
        cbar = plt.colorbar(im)
        cbar.set_label('Win Ratio - Lose Ratio (%)', rotation=270, labelpad=20)
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                val = win_minus_lose_matrix[i, j]
                if not np.isnan(val):
                    plt.text(j, i, f'{val:.2f}%', 
                             ha='center', va='center', fontsize=8, fontweight='bold', color='black')
        plt.xlabel('Dealer Upcard')
        plt.ylabel('Player Hand')
        plt.title('Win Ratio Minus Lose Ratio (%) - Optimal Strategy')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()


def get_default_strategies() -> List[StrategyConfig]:
    """Get a list of default strategies to test."""
    return [
        # StrategyConfig(
        #     name="Naive Strategy", 
        #     strategy_class=NaiveStrategy,
        #     description="Hits on anything below 17, stands otherwise",
        #     color="red"
        # ),
        StrategyConfig(
            name="Optimal Strategy",
            strategy_class=ExplicitTableStrategy,
            description="Uses comprehensive strategy table for optimal play",
            color="green"
        ),
        StrategyConfig(
            name="Custom Strategy",
            strategy_class=CustomTableStrategy,
            description="User-editable strategy table for experiments",
            color="blue"
        )
    ]


def run_simulation(config: Optional[SimulationConfig] = None, 
                  strategies: Optional[List[StrategyConfig]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Run a complete simulation with the given configuration and strategies.
    
    Args:
        config: Simulation configuration, uses default if None
        strategies: List of strategies to test, uses default if None
        
    Returns:
        Dictionary containing statistics for all strategies
    """
    if config is None:
        config = SimulationConfig()
    
    if strategies is None:
        strategies = get_default_strategies()
    
    # Create and run simulations
    runner = SimulationRunner(config)
    for strategy_config in strategies:
        runner.add_strategy(strategy_config)
    
    runner.run_all()
    stats = runner.get_statistics()
    
    # Generate reports
    report_gen = ReportGenerator()
    report_gen.write_text_report(stats)
    report_gen.write_json_report(stats)
    report_gen.plot_money_curves(stats, {s.name: s for s in strategies})
    report_gen.plot_strategy_table_heatmap(stats)
    report_gen.plot_comparison_chart(stats)
    report_gen.plot_strategy_table_win_heatmap(stats)
    report_gen.plot_strategy_table_frequency_heatmap(stats)
    report_gen.plot_strategy_table_win_minus_lose_heatmap(stats)
    
    return stats


def run_gaussian_comparison(num_simulations=1000, num_hands=1000, filename='strategy_gaussian_comparison.png'):
    """
    Run multiple simulations for both Optimal and Custom strategies, plot Gaussian curves of final money.
    """
    from strategy_table import ExplicitTableStrategy, CustomTableStrategy
    from blackjack_simulator import BlackjackSimulator

    strategies = [
        ("Optimal Strategy", ExplicitTableStrategy, 'green'),
        ("Custom Strategy", CustomTableStrategy, 'blue'),
    ]
    results = {name: [] for name, _, _ in strategies}

    rules = {
        'allow_splits': True,
        'double_after_split': True,
        'dealer_hits_soft_17': False
    }

    for name, strat_cls, color in strategies:
        print(f"Running {num_simulations} simulations for {name}...")
        for i in range(num_simulations):
            sim = BlackjackSimulator(num_hands, strat_cls(), rules)
            sim.run()
            results[name].append(sim.stats['money'])

    # Compute means and stds
    stats = {}
    for name in results:
        arr = np.array(results[name])
        stats[name] = {
            'mean': np.mean(arr),
            'std': np.std(arr),
            'all': arr
        }
        print(f"{name}: mean = {stats[name]['mean']:.2f}, std = {stats[name]['std']:.2f}")

    # Plot Gaussian curves
    plt.figure(figsize=(10, 6))
    x_min = min(np.min(stats[name]['all']) for name in stats)
    x_max = max(np.max(stats[name]['all']) for name in stats)
    x = np.linspace(x_min, x_max, 1000)
    for name, _, color in strategies:
        mu = stats[name]['mean']
        sigma = stats[name]['std']
        plt.plot(x, norm.pdf(x, mu, sigma), label=f"{name} (μ={mu:.2f}, σ={sigma:.2f})", color=color, linewidth=2)
        # Optionally, plot histogram as well:
        plt.hist(stats[name]['all'], bins=40, density=True, alpha=0.2, color=color)
    plt.xlabel('Final Money after 1000 Hands')
    plt.ylabel('Probability Density')
    plt.title('Distribution of Final Money: Optimal vs Custom Strategy')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Gaussian comparison plot saved as {filename}")


if __name__ == "__main__":
    # Example usage with default settings
    print("Starting Blackjack Strategy Comparison...")
    stats = run_simulation()
    
    # Print summary to console
    print("\n" + "="*60)
    print("SIMULATION SUMMARY")
    print("="*60)
    for strategy_name, data in stats.items():
        print(f"\n{strategy_name}:")
        print(f"  Win Rate: {data['win_rate']:.2%}")
        print(f"  Avg Return: ${data['avg_return_per_hand']:.4f}")
        print(f"  Total Money: ${data['total_money']:,.2f}")
    
    print(f"\nResults saved to:")
    print(f"  - results.txt (detailed text report)")
    print(f"  - results.json (machine-readable data)")
    print(f"  - money_vs_hands.png (money curves)")
    print(f"  - strategy_table_heatmap.png (strategy table heatmap)")
    print(f"  - strategy_comparison.png (comparison charts)")
    print(f"  - strategy_table_win_heatmap.png (win probability heatmap)")
    print(f"  - strategy_table_frequency_heatmap.png (frequency heatmap)")
    print(f"  - strategy_table_win_minus_lose_heatmap.png (win minus lose heatmap)")
    print("\nRunning Gaussian comparison of strategies...")
    run_gaussian_comparison(num_simulations=10000, num_hands=1000) 