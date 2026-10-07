import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GROUP_ORDER = ["responder", "non-responder"]
GROUP_COLORS = {"responder": "#4C72B0", "non-responder": "#DD8452"}


def response_boxplot(cohort, results, path):
    populations = sorted(cohort["population"].unique())
    pvalues = results.set_index("population")["p_value"]

    fig, axes = plt.subplots(1, len(populations), figsize=(4 * len(populations), 4.5))
    for ax, population in zip(axes, populations):
        subset = cohort[cohort["population"] == population]
        data = [subset.loc[subset["group"] == g, "percentage"] for g in GROUP_ORDER]
        box = ax.boxplot(data, patch_artist=True, widths=0.6)
        for patch, group in zip(box["boxes"], GROUP_ORDER):
            patch.set_facecolor(GROUP_COLORS[group])
            patch.set_alpha(0.7)
        for median in box["medians"]:
            median.set_color("black")

        ax.set_xticks([1, 2], ["Responder", "Non-responder"])
        ax.set_title(f"{population}\np = {pvalues[population]:.3g}")
        ax.set_ylabel("Relative frequency (%)")

    fig.suptitle("Melanoma, miraclib, PBMC: responders vs non-responders")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
