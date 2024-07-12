
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from hist import Hist, Stack
import numpy as np


class Test:
    def __init__(self,
                 name: str = "",
                 filename: str = "",
                 test_result_dir: str = "",
                 header: int = 0,
                 index_col: int = None,
                 id_col: str = "chipID",
                 tester_to_serial: dict | None = None) -> None:
        self.name = name
        self.header = header
        self.index_col = index_col
        self.id_col = id_col
        self.tester_to_serial = tester_to_serial
        self.filename = filename
        self.datafile = Path(test_result_dir) / self.filename
        if not self.datafile.exists():
            raise FileNotFoundError(f"File {self.datafile} not found")


    def read_data(self):
        if self.name == "qdc_calibration":
            cols = pd.read_csv(self.datafile, sep="\t", header=self.header, index_col=self.index_col).columns
            if not ("p9" in cols):
                print("fixing QDC data")
                cols = [*[c.replace("# ", "") for c in cols[:-1]], 'p9', 'sigma']
                return pd.read_csv(self.datafile, sep="\t", header=None, skiprows=1, names=cols)

        if self.datafile.suffix == ".csv":
            return pd.read_csv(self.datafile, header=self.header, index_col=self.index_col)
        elif self.datafile.suffix == ".tsv":
            return pd.read_csv(self.datafile, sep="\t", header=self.header, index_col=self.index_col)
        else:
            raise ValueError("File format not supported")



class Aldo(Test):
    
    """
    gain = (220 + 5.11)/5.11
    if aldo_range == 0: # aldo is gain in my case
        slope_limits = (gain * 0.000445, gain * 0.000485)
        b_limits = (34, gain*0.86)
        inl_limits = (0, 5)
    else:
        slope_limits = (gain * 0.00089, gain * 0.00096)
        b_limits = (31, gain * 0.77)
        inl_limits = (0, 8)
    """
    def __init__(self,
                 name: str = "aldo",
                 filename: str = "aldo.tsv",
                 header: int = None,
                 index_col: int = None,
                 id_col: str | int = 0,
                 **kwargs) -> None:
        super().__init__(name=name,
                         filename=filename,
                         header=header,
                         index_col=index_col,
                         id_col=id_col,
                            **kwargs)


    def get_data(self):
        data = self.read_data()
        rename = {0: "tester_ID", 1: "asic_id", 2: "side", 3: "gain",
                4: "DAC", 5: "Vout", 6: "current"}
        data = data.rename(columns=rename)
        data["SN"] = data["tester_ID"].apply(lambda x: self.tester_to_serial[x])
        return data


    def get_reduced_data(self):
        data = self.get_data()

        def process_group(group):
            # Ensure DAC < 250
            fit_data = group[group.DAC < 250]
            slope, b = np.polyfit(fit_data.DAC, fit_data.Vout, 1)
            error = fit_data.Vout - (slope * fit_data.DAC + b)
            max_inl = max(abs(error)) / slope
            # Assuming there's only one unique SN per group
            SN = int(fit_data.SN.unique()[0])
            return pd.Series([slope, b, max_inl, SN], index=['slope', 'b', 'max_inl', 'SN'])

        groupby = data.groupby(['tester_ID', 'asic_id', 'side', 'gain'])
        reduced_df = groupby[data.columns.tolist()].apply(process_group).reset_index()


        gain = (220 + 5.11)/5.11
        aldo_limits = {0: {"slope": (gain*0.000445,gain*0.000485),
                            "b": (34, gain*0.86),
                            "inl": (0, 5)},
                        1: {"slope": (gain*0.00089, gain*0.00096),
                            "b": (31, gain*0.77),
                            "inl": (0, 8)}}
        def apply_conditions(group, aldo_limits):
            # Extract the limits for the current "gain" value from the group name
            limits = aldo_limits[group.name]
            # Apply conditions using vectorized operations
            conditions_met = (
                (group["slope"] > limits["slope"][0]) &
                (group["slope"] < limits["slope"][1]) &
                (group["b"] > limits["b"][0]) &
                (group["b"] < limits["b"][1]) &
                (group["max_inl"] > limits["inl"][0]) &
                (group["max_inl"] < limits["inl"][1])
            )
            return conditions_met

        # Group the DataFrame by "gain" and apply the conditions
        result = reduced_df.groupby("gain")[["slope", "b", "max_inl"]].apply(apply_conditions, aldo_limits=aldo_limits)

        reduced_df["pass"] = result.reset_index(level=0, drop=True)
        return reduced_df

class DiscCalibration(Test):
    """
    Disc calibration

    upper limits:
    noisecriteria = {
            0:[2, 1, 0.6], # disc range 0: t1, t2, energy
            1:[1,0.5,0.3],
            2:[0.67,0.33,0.3],
            3:[0.5, 0.25, 0.3]
    }
    zerocriteria = {
            0:[100, 50, 16], # disc range 0: add > 0 requirement to t1, t2 
            1:[50,25,8], # same
            2:[33,17,5], # same
            3:[25, 13, 4] # same
    }
    
    """
    def __init__(self,
                    name: str = "disc_calibration",
                    filename: str = "disc_calibration.tsv",
                    header: int = 0,
                    index_col: int = None,
                    **kwargs) -> None:
                    
        super().__init__(name=name,
                         filename=filename,
                         header=header,
                         index_col=index_col,
                         **kwargs)

    def get_data(self):
        data = self.read_data()
        # add SN 
        data["SN"] = data[self.id_col].apply(lambda x: self.tester_to_serial[x // 2])
        keeps = ["SN", self.id_col, "channelID",
                 *[f"{prefix}_{suffix}"
                   for prefix in ["noise", "zero"]
                   for suffix in ["T1", "T2", "E"]]]
        return data[keeps]


class TDCCalibration(Test):
    
    """
    TDC calibration
    requirements:
    sigma < 62.5 / 6250
    a1 > 440
    1.5*a1 + a0 < 1000
    
    """
    def __init__(self,
                 name: str = "TDCCalibration",
                 filename: str = "tdc_calibration.tsv",
                 header: int = 0,
                 index_col: int = None,
                 **kwargs) -> None:
        super().__init__(name=name,
                         filename=filename,
                         header=header,
                         index_col=index_col,
                         **kwargs)
        
    def get_data(self):
        data = self.read_data()
        # add asic_id
        data["SN"] = data[self.id_col].apply(lambda x: self.tester_to_serial[x // 2])
        keeps = ["SN", self.id_col, "channelID", "tacID",
                 "branch", "t0", *[f"a{i}" for i in range(0,3)], "sigma"]
        return data[keeps]

    def get_reduced_data(self):
        data = self.get_data()
        # apply conditions
        conditions = (data["sigma"] < 62.5 / 6250) & (data["a1"] > 440) & (1.5*data["a1"] + data["a0"] < 1000)
        data["pass"] = conditions
        return data

        
class TestPulse(Test):
    def __init__(self,
                 name: str = "test_pulse",
                 filename: str = "fetp_tres_scan.tsv",
                 header: int = None,
                 index_col: int = None,
                 id_col: str | int = 0,
                 **kwargs) -> None:
        super().__init__(name=name,
                         header=header,
                         filename=filename,
                         index_col=index_col,
                         id_col=id_col,
                         **kwargs)

    def get_data(self):
        data = self.read_data()
        # add SN
        data["SN"] = data[self.id_col].apply(lambda x: self.tester_to_serial[x // 2])
        keeps = ["SN", self.id_col, 1, 2, 3, 4, 5] 
        # rename 
        rename = {0: "chipID",
                  1: "channelID", 
                  2: "amplitude", 
                  3: "time_resolution",
                  4: "energy_mean", 
                  5: "energy_rms"}
        return data[keeps].rename(columns=rename)
    

class ExtTestPulse(TestPulse, Test):
    def __init__(self, name: str = "ext_test_pulse",
                 filename: str = "extp_tres_scan.tsv",
                 **kwargs) -> None:
        super().__init__(name,
                         filename,
                         **kwargs)

class QDCCalibration(Test):
    """
    QDC calibration
    requirements:

    p0 < 100
    -2 < p1 < 15
    """
    def __init__(self,
                 name="qdc_calibration",
                 filename: str="qdc_calibration.tsv",
                 header: int=0,
                 index_col: int | None = None,
                 **kwargs):

        super().__init__(name=name,
                         filename=filename,
                         header=header,
                         index_col=index_col,
                         **kwargs)
        
    def get_data(self):
        data = self.read_data()

        if "p9" not in data.columns:
            print("Fixing QDC data")
            cols = [*[c.replace("# ", "") for c in data.columns[:-1]], 'p9', 'sigma']
            data = pd.read_csv(self.datafile, sep="\t", header=None, skiprows=1, names=cols)
        # add SN
        data["SN"] = data[self.id_col].apply(lambda x: self.tester_to_serial[x // 2])
        keeps = ["SN", self.id_col, "trim",*[f"p{i}" for i in range(0, 4)], "sigma"]
        return data[keeps]
    
    def get_reduced_data(self):
        data = self.get_data()
        # apply conditions
        conditions = (data["p0"] < 100) & (data["p1"] > -2) & (data["p1"] < 15)
        data["pass"] = conditions
        return data
    
# qdc calibration has 8 settings

class QDCCalibration_0(QDCCalibration):
    """QDC calibration (Attenuation = 0)"""
    def __init__(self,
                name="qdc_calibration_0",
                filename: str = "qdc_calibration0.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
    
class QDCCalibration_1(QDCCalibration):
    """QDC calibration (Attenuation = 1)"""
    def __init__(self,
                name="qdc_calibration_1",
                filename: str = "qdc_calibration1.tsv",
                **kwargs):
       super().__init__(name,filename, **kwargs) 
    

class QDCCalibration_2(QDCCalibration):
    """QDC calibration (Attenuation = 2)"""
    def __init__(self,
                name="qdc_calibration_2",
                filename: str = "qdc_calibration2.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
            
class QDCCalibration_3(QDCCalibration):
    """QDC calibration (Attenuation = 3)"""
    def __init__(self,
                name="qdc_calibration_3",
                filename: str = "qdc_calibration3.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
                
class QDCCalibration_4(QDCCalibration):
    """QDC calibration (Attenuation = 4)"""
    def __init__(self,
                name="qdc_calibration_4",
                filename: str = "qdc_calibration4.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
                        
class QDCCalibration_5(QDCCalibration):
    """QDC calibration (Attenuation = 5)"""
    def __init__(self,
                name="qdc_calibration_5",
                filename: str = "qdc_calibration5.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
                                
class QDCCalibration_6(QDCCalibration):
    """QDC calibration (Attenuation = 6)"""
    def __init__(self,
                name="qdc_calibration_6",
                filename: str = "qdc_calibration6.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
                                        
class QDCCalibration_7(QDCCalibration):
    """QDC calibration (Attenuation = 7)"""
    def __init__(self,
                name="qdc_calibration_7",
                filename: str = "qdc_calibration7.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
        

# disc calibration has 4 settings
class DiscCalibration_0(DiscCalibration):
    """Disc calibration (Disc. Range = 0)"""
    def __init__(self,
                name="disc_calibration_0",
                filename: str = "disc_calibration0.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
    
    def get_reduced_data(self):
        data = self.get_data()
        # apply conditions
        conditions = ((data["noise_T1"] < 2) &
                     (data["noise_T2"] < 1) &
                     (data["noise_E"] < 0.6) &
                     (0 < data["zero_T1"] < 100) &
                     (0 < data["zero_T2"] < 50) &
                     (data["zero_E"] < 16))
        data["pass"] = conditions
        return data


class DiscCalibration_1(DiscCalibration):
    """Disc calibration (Attenuation = 1)"""
    def __init__(self,
                name="disc_calibration_1",
                filename: str = "disc_calibration1.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)

    def get_reduced_data(self):
        data = self.get_data()
        # apply conditions
        conditions = ((data["noise_T1"] < 1) &
                     (data["noise_T2"] < 0.5) &
                     (data["noise_E"] < 0.3) &
                     (0 < data["zero_T1"] < 50) &
                     (0 < data["zero_T2"] < 25) &
                     (data["zero_E"] < 8))
        data["pass"] = conditions
        return data
        
class DiscCalibration_2(DiscCalibration):
    """Disc calibration (Attenuation = 2)"""
    def __init__(self,
                name="disc_calibration_2",
                filename: str = "disc_calibration2.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)

    def get_reduced_data(self):
        data = self.get_data()
        # apply conditions
        conditions = ((data["noise_T1"] < 0.67) &
                     (data["noise_T2"] < 0.33) &
                     (data["noise_E"] < 0.3) &
                     (0 < data["zero_T1"] < 33) &
                     (0 < data["zero_T2"] < 17) &
                     (data["zero_E"] < 5))
        data["pass"] = conditions
        return data

class DiscCalibration_3(DiscCalibration):
    """Disc calibration (Attenuation = 3)"""
    def __init__(self,
                name="disc_calibration_3",
                filename: str = "disc_calibration3.tsv",
                **kwargs):
        super().__init__(name,filename, **kwargs)
    
    def get_data(self):
        data = self.get_data()
        # apply conditions
        conditions = ((data["noise_T1"] < 0.5) &
                        (data["noise_T2"] < 0.25) &
                        (data["noise_E"] < 0.3) &
                        (0 < data["zero_T1"] < 25) &
                        (0 < data["zero_T2"] < 13) &
                        (data["zero_E"] < 4))
        data["pass"] = conditions
        
        
class MergedTest():
    
    """
    Baseclass to represent the tests once they have been merged
    
    the tests should be able to read the merged testdata from a file.
    there should be a method to return the yield based on a given criteria
    """

    def __init__(self,
                 name: str | Test,
                 merged_data: str | Path | pd.DataFrame,) -> None:
        self.name = name if isinstance(name, str) else name.name
        if any(isinstance(merged_data, t) for t in [str, Path]):
            assert Path(merged_data).exists(), f"File {merged_data} not found"
            self.merged_data = pd.read_csv(merged_data)
        else:
            self.merged_data = merged_data
            
    