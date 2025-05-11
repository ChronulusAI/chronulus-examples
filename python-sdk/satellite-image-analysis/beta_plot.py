import os
import json

import numpy as np
import matplotlib.pyplot as plt
from chronulus.prediction import BinaryPredictionSet
from scipy.stats import beta


def beta_mean(a, b, negate=False):
    return b/(a+b) if negate else a/(a+b)


def plot_beta_distributions(params_list, x_range=(0, 1), num_points=1000, labels=None,
                            title="Beta Distributions", figsize=(10, 6),
                            colors=None, alpha=0.7, grid=True, legend_loc='best',
                            negate=False,
                            ax=None,
                            ):
    """
    Plot multiple beta distributions on a single figure.

    Parameters:
    -----------
    params_list : list of tuples
        List of (alpha, beta) tuples defining each beta distribution
    x_range : tuple, optional
        Range of x values to plot (default: (0, 1))
    num_points : int, optional
        Number of points to evaluate the distributions (default: 1000)
    labels : list of str, optional
        Labels for each distribution in the legend (default: None)
    title : str, optional
        Title of the plot (default: "Beta Distributions")
    figsize : tuple, optional
        Figure size (width, height) in inches (default: (10, 6))
    colors : list, optional
        List of colors for each distribution (default: None, uses matplotlib defaults)
    alpha : float, optional
        Transparency of the plots (default: 0.7)
    grid : bool, optional
        Whether to display grid lines (default: True)
    legend_loc : str, optional
        Location of the legend (default: 'best')

    Returns:
    --------
    fig, ax : tuple
        The figure and axes objects
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    x = np.linspace(x_range[0], x_range[1], num_points)

    # Generate default labels if none provided
    if labels is None:
        if negate:

            labels = [f"α={a:.1f}, β={b:.1f}, prob={100 * a / (a + b):2.2f}" for b, a in params_list]
        else:
            labels = [f"α={a:.1f}, β={b:.1f}, prob={100 * a / (a + b):2.2f}" for a, b in params_list]

            # Plot each distribution
    for i, (a, b) in enumerate(params_list):
        if negate:
            y = beta.pdf(x, b, a)
        else:
            y = beta.pdf(x, a, b)
        color = None if colors is None else colors[i]
        ax.plot(x, y, label=labels[i], alpha=alpha, color=color)

    # Set plot details
    ax.set_title(title)
    ax.set_xlabel('x')
    ax.set_ylabel('Probability Density')
    if grid:
        ax.grid(alpha=0.3)
    ax.legend(loc=legend_loc)

    plt.tight_layout()
    return ax


def plot_prediction_set(prediction_set, output_file: str, negate=False, figsize=(12, 4)):
    experts = [tuple(pred.opinion_set.beta_params.dict().values()) for pred in prediction_set.predictions]
    positive = [tuple(pred.opinion_set.positive.beta_params.dict().values()) for pred in prediction_set.predictions]
    negative = [tuple(pred.opinion_set.negative.beta_params.dict().values()) for pred in prediction_set.predictions]
    consensus = [tuple(prediction_set.beta_params.dict().values())]
    fig, ax = plt.subplots(2, 2, figsize=(figsize[0] * 2, figsize[1] * 2))

    ax1 = plot_beta_distributions(
        positive,
        labels=[f"Expert {i + 1} - {100 * beta_mean(a, b, negate):2.2f}%" for i, (a, b) in enumerate(positive)],
        title="Positive Framing",
        figsize=figsize,
        negate=negate,
        ax=ax[0, 0]
    )
    ax2 = plot_beta_distributions(
        negative,
        labels=[f"Expert {i + 1} - {100 * beta_mean(a, b, negate):2.2f}%" for i, (a, b) in enumerate(negative)],
        title="Negative Framing",
        figsize=figsize,
        negate=negate,
        ax=ax[0, 1]
    )
    ax3 = plot_beta_distributions(
        experts,
        labels=[f"Expert {i + 1} - {100 * beta_mean(a, b, negate):2.2f}%" for i, (a, b) in enumerate(experts)],
        title="Consensus over framings",
        figsize=figsize,
        negate=negate,
        ax=ax[1, 0]
    )
    ax4 = plot_beta_distributions(
        consensus,
        labels=[f"Consensus - {100 * beta_mean(a, b, negate):2.2f}%" for i, (a, b) in enumerate(consensus)],
        title="Consensus over experts",
        figsize=figsize,
        negate=negate,
        ax=ax[1, 1]
    )

    plt.savefig(output_file)


def save_predictions(prediction_set: BinaryPredictionSet, output_path: str ):
    os.makedirs(output_path, exist_ok=True)
    plot_prediction_set(prediction_set, f"{output_path}/prediction_set.png", figsize=(8, 4))

    with open(f"{output_path}/output.txt", "w") as f:
        output = prediction_set.text
        lines = [
            f"{prediction_set.prob} with Beta({prediction_set.beta_params.alpha}, {prediction_set.beta_params.beta})",
            output
        ]
        final_output = "\n\n".join(lines)
        f.write(final_output)

    json_str = json.dumps(prediction_set.to_dict(), indent=2)
    with open(f"{output_path}/output.json", "w") as f:
        f.write(json_str)