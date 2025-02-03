import streamlit as st
import pandas as pd
import numpy as np
from glob import glob
from pathlib import Path

#from tests import *
#
#test_map = {"Aldo": Aldo,
#            "TestPulse": TestPulse,
#            "ExtTestPulse": ExtTestPulse,
#            "DiscCalibration0": DiscCalibration_0,
#            "DiscCalibration1": DiscCalibration_1,
#            "DiscCalibration2": DiscCalibration_2,
#            "DiscCalibration3": DiscCalibration_3,
#            "QDCCalibration0": QDCCalibration_0,
#            "QDCCalibration1": QDCCalibration_1,
#            "QDCCalibration2": QDCCalibration_2,
#            "QDCCalibration3": QDCCalibration_3,
#            "QDCCalibration4": QDCCalibration_4,
#            "QDCCalibration5": QDCCalibration_5,
#            "QDCCalibration6": QDCCalibration_6,
#            "QDCCalibration7": QDCCalibration_7,
#            "TDCCalibration": TDCCalibration}
#
#
#      
#class TestResult:
#
#    def __init__(self,
#                path: str | Path = "",
#                tests: list[str] = ["Aldo",
#                                    "TestPulse",
#                                    "ExtTestPulse",
#                                    "DiscCalibration0",
#                                    "DiscCalibration1",
#                                    "DiscCalibration2",
#                                    "DiscCalibration3",
#                                    "QDCCalibration0",
#                                    "QDCCalibration1",
#                                    "QDCCalibration2",
#                                    "QDCCalibration3",
#                                    "QDCCalibration4",
#                                    "QDCCalibration5",
#                                    "QDCCalibration6",
#                                    "QDCCalibration7",
#                                    "TDCCalibration"],
#                ) -> None:
#      
#        self.path = path
#        self.tests = tests
#
#        # for each test assert that the corresponding file exists
#        for test in self.tests:
#            datafile = test_map[test](test_result_dir=self.path).datafile
#            if not datafile.exists(): 
#                raise FileNotFoundError(f"File {datafile} not found in {self.path}")
#
#        self.serial_files = [f for f in Path(self.path).rglob('SN_3*.txt')]
#        assert len(self.serial_files) > 0, "No serial files found in the directory"
#
#        self.tester_to_serial = {}
#        for f in self.serial_files: 
#            sn = int(f.stem.split(" ")[-1])
#            with open(f, "r") as file:
#                tester = int(file.read().strip())
#            self.tester_to_serial[tester] = sn
#
#
#    def get_data(self,
#                test: str,
#                filename: str = ""
#                ) -> pd.DataFrame:
#        if test not in self.tests:
#            raise ValueError(f"Test {test} not in {self.tests}")
#        
#        test_args = {"test_result_dir": self.path,
#                    "tester_to_serial": self.tester_to_serial}
#        if filename != "":
#            test_args["filename"] = filename
#            return test_map[test](**test_args).get_data()
#        else:
#            return test_map[test](**test_args).get_data()
#
#        
#    def get_passing_info(self,
#                        test: str
#                        ) -> pd.DataFrame:
#        if test not in self.tests:
#            raise ValueError(f"Test {test} not in {self.tests}")
#
#        test_args = {"test_result_dir": self.path,
#                    "tester_to_serial": self.tester_to_serial}
#        return test_map[test](**test_args).get_passing_info()
#
#
#class YieldComputer:
#    
#    def __init__(self,
#                 tests: list,
#                 base_dir: str | Path) -> None:
#        self.tests = tests
#        self.base_dir = base_dir
#        
#
#    def get_test_result_dirs(self,
#                             base_dir: str):
#        test_result_dirs = [d for d in Path(self.base_dir).glob("2024*") if d.is_dir()]
#        return sorted(test_result_dirs, key=lambda x: int(x.stem))
#
#
#    def merge_dataframes_for_test(self,
#                                  test: str):
#        test_result_dirs = self.get_test_result_dirs(self.base_dir)
#        merged_dataframe = pd.DataFrame()
#        skipped = []
#        for d in test_result_dirs:
#            try: 
#                tr = TestResult(path=d)
#            except FileNotFoundError as e:
#                skipped.append(d)
#                continue
#            data = tr.get_passing_info(test)
#            if not merged_dataframe.empty and any(data["SN"].isin(merged_dataframe["SN"])):
#                merged_dataframe = merged_dataframe[~merged_dataframe["SN"].isin(data["SN"])]
#            merged_dataframe = pd.concat([merged_dataframe, data], ignore_index=True)
#        merged_dataframe.set_index("SN", inplace=True)
#        #print(f"Skipped {len(skipped)} directories:")
#        #pprint(skipped)
#        return merged_dataframe
#
#
#    def get_yield_data(self):
#        return pd.concat([self.merge_dataframes_for_test(test).rename(columns={"test_pass": f"{test}_pass"})
#                          for test in self.tests], axis=1)
#
#
#class Plotter:
#    
#    def __init__(self,
#                 tests: list,
#                 base_dir: str | Path) -> None:
#        self.tests = tests
#        self.base_dir = base_dir
#        
#
#    def get_test_result_dirs(self,
#                             base_dir: str):
#        test_result_dirs = [d for d in Path(self.base_dir).glob("2024*") if d.is_dir()]
#        return sorted(test_result_dirs, key=lambda x: int(x.stem))
#
#
#    def merge_dataframes_for_test(self,
#                                  test: str):
#        test_result_dirs = self.get_test_result_dirs(self.base_dir)
#        merged_dataframe = pd.DataFrame()
#        skipped = []
#        for d in test_result_dirs:
#            try: 
#                tr = TestResult(path=d)
#            except FileNotFoundError as e:
#                skipped.append(d)
#                continue
#            data = tr.get_data(test)
#            if not merged_dataframe.empty and any(data["SN"].isin(merged_dataframe["SN"])):
#                merged_dataframe = merged_dataframe[~merged_dataframe["SN"].isin(data["SN"])]
#            merged_dataframe = pd.concat([merged_dataframe, data], ignore_index=True)
#        merged_dataframe.set_index("SN", inplace=True)
#        return merged_dataframe
#
#
#
#test_result_dirs = [d for d in Path("/eos/user/a/aboletti/TOFHIR2C_validation/tmp_calibration_data").glob("2024*") if d.is_dir()]
## assert that the dirs are sorted by their timestamps (yyyymmddhhmm)
#test_result_dirs = sorted(test_result_dirs, key=lambda x: int(x.stem))
#test_result_dirs

# define base url name
# baseurl = "https://tofhir2-feboards.app.cern.ch"
baseurl = "http://localhost:8501"

#trs = []
#for d in test_result_dirs:
#    try:
#        tr = TestResult(d)
#        trs.append(tr)
#    except FileNotFoundError as e:
#        print(e)
#        continue
#
## Generate summary df 
#
#yc = YieldComputer(tests=["Aldo",
#                          "DiscCalibration0",
#                          "DiscCalibration1",
#                          "DiscCalibration2",
#                          "DiscCalibration3",
#                          "QDCCalibration0",
#                          "QDCCalibration1",
#                          "QDCCalibration2",
#                          "QDCCalibration3",
#                          "QDCCalibration4",
#                          "QDCCalibration5",
#                          "QDCCalibration6",
#                          "QDCCalibration7",
#                          "TDCCalibration"],
#                   base_dir="/eos/user/a/aboletti/TOFHIR2C_validation/tmp_calibration_data")

yield_df = pd.read_csv("yield.csv", index_col="SN") 
# Create a placeholder DataFrame
st.subheader('Summary of all boards')

st.dataframe(yield_df,
             column_config={
                **{col: col for col in yield_df.columns if col != "link"},
                    "link": st.column_config.LinkColumn("Link"),
             },
             hide_index=False,
)

st.subheader("Individual Yields")

yield_map = {col.split("_")[0]: f"{(yield_df[col].sum()/len(yield_df)):.2%}" for col in yield_df.columns if col.endswith("_pass")}
yield_map_df = pd.DataFrame(yield_map.items(), columns=["Test", "Yield"]).set_index("Test")
st.dataframe(yield_map_df)

st.subheader("Overall Yield")

test_yield_df = yield_df[[col for col in yield_df if col.endswith("test_pass")]]
total_yield = (test_yield_df.sum(axis=1) == len(test_yield_df.columns)).sum()/len(test_yield_df)

st.write(f"Overall yield: {total_yield:.2%}")

