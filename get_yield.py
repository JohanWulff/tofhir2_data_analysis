# coding = utf-8
from pathlib import Path 

import pandas as pd

from tests import * #noqa
from plotting import plot_qdc, plot_tdc, plot_testpulse, plot_disc_calibration


test_map = {"Aldo": Aldo,
            "TestPulse": TestPulse,
            "ExtTestPulse": ExtTestPulse,
            "DiscCalibration0": DiscCalibration_0,
            "DiscCalibration1": DiscCalibration_1,
            "DiscCalibration2": DiscCalibration_2,
            "DiscCalibration3": DiscCalibration_3,
            "QDCCalibration0": QDCCalibration_0,
            "QDCCalibration1" : QDCCalibration_1,
            "QDCCalibration2" : QDCCalibration_2,
            "QDCCalibration3" : QDCCalibration_3,
            "QDCCalibration4" : QDCCalibration_4,
            "QDCCalibration5" : QDCCalibration_5,
            "QDCCalibration6" : QDCCalibration_6,
            "QDCCalibration7" : QDCCalibration_7,
            "TDCCalibration": TDCCalibration,
            }
            

class TestResult:

    def __init__(self,
                path: str | Path = "",
                tests: list[str] = ["Aldo",
                                    "TestPulse",
                                    "ExtTestPulse",
                                    "DiscCalibration0",
                                    "DiscCalibration1",
                                    "DiscCalibration2",
                                    "DiscCalibration3",
                                    "QDCCalibration0",
                                    "QDCCalibration1",
                                    "QDCCalibration2",
                                    "QDCCalibration3",
                                    "QDCCalibration4",
                                    "QDCCalibration5",
                                    "QDCCalibration6",
                                    "QDCCalibration7",
                                    "TDCCalibration"],
                ) -> None:
      
        self.path = path
        self.tests = tests

        # for each test assert that the corresponding file exists
        for test in self.tests:
            filename = test_map[test].filename
            if not Path(self.path).joinpath(filename).exists():
                raise FileNotFoundError(f"File {filename} not found in {self.path}")

        self.serial_files = [f for f in Path(self.path).rglob('SN_3*.txt')]
        assert len(self.serial_files) > 0, "No serial files found in the directory"

        self.tester_to_serial = {}
        for f in self.serial_files: 
            sn = int(f.stem.split(" ")[-1])
            with open(f, "r") as file:
                tester = int(file.read().strip())
            self.tester_to_serial[tester] = sn


    def get_data(self,
                test: str,
                filename: str = ""
                ) -> pd.DataFrame:
        if test not in self.tests:
            raise ValueError(f"Test {test} not in {self.tests}")
        
        test_args = {"test_result_dir": self.path,
                    "tester_to_serial": self.tester_to_serial}
        if filename != "":
            test_args["filename"] = filename
            return test_map[test](**test_args).get_data()


class YieldComputer:
    
    def __init__(self,
                 tests: list,
                 base_dir: str | Path) -> None:
        self.tests = tests
        self.base_dir = base_dir
        

    def get_test_result_dirs(self,
                             base_dir: str):
        test_result_dirs = [d for d in Path(self.base_dir).glob("2024*") if d.is_dir()]
        return sorted(test_result_dirs, key=lambda x: int(x.stem))


    def merge_dataframes_for_test(self,
                                  test: str):
        test_result_dirs = self.get_test_result_dirs(self.base_dir)
        merged_dataframe = pd.DataFrame()
        for d in test_result_dirs:
            try: 
                tr = TestResult(path=d)
            except FileNotFoundError as e:
                print(e)
                print(f"Skipping {d}")
                continue
            data = tr.get_data(test)
            if not merged_dataframe.empty and any(data["SN"].isin(merged_dataframe["SN"])):
                merged_dataframe = merged_dataframe[~merged_dataframe["SN"].isin(data["SN"])]
            merged_dataframe = pd.concat([merged_dataframe, data], ignore_index=True)
        merged_dataframe.reset_index(drop=True, inplace=True)
        return merged_dataframe
    
    def get_yield(self,
                  tests: list[str],):
        for test in tests:
            
    
    

        

base_dir = "/eos/user/a/aboletti/TOFHIR2C_validation/tmp_calibration_data"
# print the test dirs found in the base dir

# first create plots for each test

for test in test_map.keys():
    merged_df = merge_dataframes_for_test(test, base_dir)
    if test == "TDCCalibration":
        plot_tdc(merged_df, savepath=f"plots/{test}")
    elif "QDCCalibration" in test:
        plot_qdc(merged_df, savepath=f"plots/{test}")
    elif test == "TestPulse":
        plot_testpulse(merged_df, savepath=f"plots/{test}")
    elif test == "DiscCalibration":
        plot_disc_calibration(merged_df, savepath=f"plots/{test}")
    
    
    