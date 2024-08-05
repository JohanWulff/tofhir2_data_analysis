
import streamlit as st
import pandas as pd
from hist import Hist, Stack
import matplotlib.pyplot as plt
from glob import glob

import sys
import os
sys.path.append("../")

basepath = "/eos/user/j/jowulff/MTD/combined_plots"

def plot_tdc(data: pd.DataFrame,
             col: str,
             title: str = "TDC Calibration")-> plt.Figure:
    binnings = {"t0" : [-0.2, 0.3, 50],
                "a0" : [20, 120, 50],
                "a1" : [450, 650, 50],
                "a2" : [-20, 1, 21],
                "sigma": [0.002, 0.01, 40]}
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
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_yscale("log")
    return fig


def plot_qdc(data: pd.DataFrame,
             col: str,
             title: str = "QDC Calibration") -> plt.Figure:
    binnings = {"trim" : [2, 44, 42],
                "p0" : [40, 80, 40],
                "p1" : [-2, 3, 50],
                "p2" : [-0.5, 0.5, 20],
                "p3" : [-0.02, 0.02, 20],
                "sigma": [0,25, 25]}

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
    ax.set_title(title)
    ax.set_yscale("log")
    ax.legend()
    ax.grid(alpha=0.3)
    return fig


def plot_disc(data: pd.DataFrame,
              plot: str) -> plt.Figure:
    
    assert plot in ["noise", "zero"]
    plot_cols = [f"{plot}_{col}" for col in ['T1', 'T2', 'E']]
    fig, ax = plt.subplots()
    for col in plot_cols:
        ax.plot(
            data["channelID"], data[f"{col}"], '.', label=col.split("_")[-1])
    ax.set_title(f"DiscCalibration {plot}")
    ax.set_xlabel("Channel ID")
    ax.set_ylabel("DAC Units")
    plt.grid(alpha=0.3)
    plt.legend()
    return fig
    
def plot_aldo(data: pd.DataFrame,
              aldo_id: int,
              aldo_side: int,) -> plt.Figure:
    assert aldo_id in [0, 1]
    assert aldo_side in [0, 1]

    data = 
    
    fig, ax = plt.subplots()
    
    

SN = "0101"
# strip the leading zeros
st.markdown(f"## Board {SN}")
st.markdown("### TDC Calibration")
tdc_data = pd.read_csv(os.path.join(basepath, "TDCCalibration.csv"))
tdc_data = tdc_data[tdc_data.SN == int(SN)]

tdc_cols = ['t0', *[f"a{i}" for i in range(0, 3)], 'sigma']

tdc_st_cols = st.columns(len(tdc_cols))
for col, st_col in zip(tdc_cols, tdc_st_cols):
    fig = plot_tdc(tdc_data, col, title=f"TDC Calibration {col}")
    with st_col:
        st.pyplot(fig)


st.markdown("### QDC Calibration")
for i, st_col in enumerate(st.columns(8)): 
    qdc_data = pd.read_csv(os.path.join(basepath, f"QDCCalibration{i}.csv"))
    qdc_data = qdc_data[qdc_data.SN == int(SN)]

    for col in ['trim', *[f"p{i}" for i in range(0, 4)], 'sigma']:
        fig = plot_qdc(qdc_data, col, title=f"QDCCalibration {i}")
        with st_col:
            st.pyplot(fig)
    
st.markdown("### Disc Calibration")
disc_data = pd.read_csv(os.path.join(basepath, "DiscCalibration0.csv"))
disc_data = disc_data[disc_data.SN == int(SN)]

for i, st_col in enumerate(st.columns(2)):
    fig = plot_disc(disc_data, ["noise", "zero"][i])
    with st_col:
        st.pyplot(fig)


st.markdown("### Aldo")
aldo_data = pd.read_csv(os.path.join(basepath, "Aldo.csv"))
aldo_data = aldo_data[aldo_data.SN == int(SN)]
