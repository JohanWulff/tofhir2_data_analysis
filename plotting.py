from hist import Hist, Stack
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

def plot_tdc(data: pd.DataFrame,
             savepath: str = "") -> None:
    binnings = {"t0" : [-0.2, 0.3, 50],
                "a0" : [20, 120, 50],
                "a1" : [450, 650, 50],
                "a2" : [-20, 1, 21],
                "sigma": [0.002, 0.01, 40]}

    for col in ['t0', *[f"a{i}" for i in range(0, 3)], 'sigma']:
        stack_dict = {}
        fig, ax = plt.subplots()
        for bid in data["branch"].unique():
            hist = Hist.new.Regular(bins=binnings[col][2],
                                    start=binnings[col][0],
                                    stop=binnings[col][1],
                                    name=col,
                                    underflow=True,
                                    overflow=True,
                                    ).Double()
            hist.fill(data[data["branch"] == bid][f"{col}"])
            stack_dict[f"Branch:{bid}"] = hist
        stack = Stack.from_dict(stack_dict)
        stack.plot(stack=True,
                    ax=ax,
                    color=[plt.cm.tab10(i) for i in range(len(stack_dict))],
                    histtype="fill")
        ax.set_ylabel("Entries")
        ax.set_title(f"TDCCalibration")
        ax.legend()
        ax.grid(alpha=0.3)
        ax.set_yscale("log")
        if savepath != "":
            if not os.path.exists(savepath):
                os.makedirs(savepath)
            plt.savefig( f"{savepath}/tdc_{col}.pdf")
            plt.close()
        else:
            plt.show()



def plot_qdc(data: pd.DataFrame,
             savepath: str = "") -> None:
    binnings = {"trim" : [2, 44, 42],
                "p0" : [40, 80, 40],
                "p1" : [-2, 3, 50],
                "p2" : [-0.5, 0.5, 20],
                "p3" : [-0.02, 0.02, 20],
                "sigma": [0,25, 25]}

    for col in ['trim', *[f"p{i}" for i in range(0, 4)], 'sigma']:
        fig, ax = plt.subplots()
        hist = Hist.new.Regular(bins=binnings[col][2],
                                start=binnings[col][0],
                                stop=binnings[col][1],
                                name=col,
                                underflow=True,
                                overflow=True,
                                ).Double()
        plot_col = data[f"{col}"]
        hist.fill(plot_col)
        hist.plot(stack=True, ax=ax, histtype="fill",
                  label="min: {0:.2f},\nmax: {1:.2f}".format(plot_col.min(), plot_col.max()))
        ax.set_ylabel("Entries")
        ax.set_title(f"QDCCalibration")
        ax.set_yscale("log")
        ax.legend()
        ax.grid(alpha=0.3)
        if savepath != "":
            if not os.path.exists(savepath):
                os.makedirs(savepath)
            plt.savefig( f"{savepath}/qdc_{col}.pdf")
            plt.close()
        else:
            plt.show()


def plot_testpulse(data: pd.DataFrame,
                   savepath: str = "") -> None:
    for i, col in enumerate(['amplitude', 'time_resolution', 'energy_mean', 'energy_rms']):
        fig, ax = plt.subplots()
        ax.plot(data[f"channelID"],data[f"{col}"],'.')
        delta_y = data[f"{col}"].max() - data[f"{col}"].min()
        if delta_y > 1000:
            ax.set_yscale("log")
        ax.set_xlabel("Channel ID")
        ax.set_ylabel(col)
        plt.grid(alpha=0.5)
        plt.show()

        fig, ax = plt.subplots()
        sns.histplot(data[f"{col}"], label=col)
        mean, std = data[f"{col}"].mean(), data[f"{col}"].std()
        ax.legend([col+f" (mean: {mean:.2f}, std: {std:.2f})"])
        ax.set_xlabel(col)
        ax.set_ylabel("Counts")
        plt.grid(alpha=0.3)
        if savepath != "":
            if not os.path.exists(savepath):
                os.makedirs(savepath)
            plt.savefig( f"{savepath}/testpulse_{col}.pdf")
            plt.close()
        else:
            plt.show()


def plot_disc_calibration(data: pd.DataFrame,
                          savepath: str = "") -> None:
    plots = ["noise", "zero"]
    for p in plots:
        plot_cols = [f"{p}_{col}" for col in ["T1", "T2", "E"]]
        fig, ax = plt.subplots()
        for col in plot_cols:
            ax.plot(
                data["channelID"], data[f"{col}"], '.', label=col.split("_")[-1])
        ax.set_xlabel("Channel ID")
        ax.set_ylabel("DAC Units")
        plt.grid(alpha=0.3)
        plt.legend()
        if savepath != "":
            if not os.path.exists(savepath):
                os.makedirs(savepath)
            plt.savefig( f"{savepath}/disc_calibration_{p}.pdf")
            plt.close()
        else:
            plt.show()

        
def plot_pt_1000(data:pd.DataFrame,
                 savepath: str = "") -> None:
    