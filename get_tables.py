import pandas as pd
import os
from pathlib import Path 

from tests import *

test_map = {"Aldo": Aldo,
            "TestPulse": TestPulse,
            "ExtTestPulse": ExtTestPulse,
            "DiscCalibration0": DiscCalibration_0,
            "DiscCalibration1": DiscCalibration_1,
            "DiscCalibration2": DiscCalibration_2,
            "DiscCalibration3": DiscCalibration_3,
            "QDCCalibration0": QDCCalibration_0,
            "QDCCalibration1": QDCCalibration_1,
            "QDCCalibration2": QDCCalibration_2,
            "QDCCalibration3": QDCCalibration_3,
            "QDCCalibration4": QDCCalibration_4,
            "QDCCalibration5": QDCCalibration_5,
            "QDCCalibration6": QDCCalibration_6,
            "QDCCalibration7": QDCCalibration_7,
            "TDCCalibration": TDCCalibration,
            "Tec": Tec,
            "CaInit": CaInit,
            "Pt_1000": Pt_1000}


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
                                    "TDCCalibration",
                                    "Tec",
                                    "Pt_1000",
                                    "CaInit"],
                ) -> None:
      
        self.path = path
        self.tests = tests

        # for each test assert that the corresponding file exists
        for test in self.tests:
            datafile = test_map[test](test_result_dir=self.path).datafile
            if not datafile.exists(): 
                raise FileNotFoundError(f"File {datafile} not found in {self.path}")

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
        else:
            return test_map[test](**test_args).get_data()

        
    def get_passing_info(self,
                        test: str
                        ) -> pd.DataFrame:
        if test not in self.tests:
            raise ValueError(f"Test {test} not in {self.tests}")

        test_args = {"test_result_dir": self.path,
                    "tester_to_serial": self.tester_to_serial}
        return test_map[test](**test_args).get_passing_info()


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
        skipped = []
        for d in test_result_dirs:
            try: 
                tr = TestResult(path=d)
            except FileNotFoundError as e:
                skipped.append(d)
                continue
            data = tr.get_passing_info(test)
            if not merged_dataframe.empty and any(data["SN"].isin(merged_dataframe["SN"])):
                merged_dataframe = merged_dataframe[~merged_dataframe["SN"].isin(data["SN"])]
            merged_dataframe = pd.concat([merged_dataframe, data], ignore_index=True)
        merged_dataframe.set_index("SN", inplace=True)
        #print(f"Skipped {len(skipped)} directories:")
        #pprint(skipped)
        return merged_dataframe


    def get_yield_data(self):
        result = []
        for test in self.tests:
            try:
                result.append(self.merge_dataframes_for_test(test).rename(columns={"pass": f"{test}_pass"}))
            except Exception as e:
                print(f"Error in test {test}: {e}")
                continue
        return pd.concat(result, axis=1)


class Plotter:
    
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
        skipped = []
        for d in test_result_dirs:
            try: 
                tr = TestResult(path=d)
            except FileNotFoundError as e:
                skipped.append(d)
                continue
            data = tr.get_data(test)
            if not merged_dataframe.empty and any(data["SN"].isin(merged_dataframe["SN"])):
                merged_dataframe = merged_dataframe[~merged_dataframe["SN"].isin(data["SN"])]
            merged_dataframe = pd.concat([merged_dataframe, data], ignore_index=True)
        merged_dataframe.set_index("SN", inplace=True)
        return merged_dataframe



def make_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Get tables for TOFHIR2C calibration tests")
    parser.add_argument("--base_dir",
                        type=str,
                        required=True,
                        default="/eos/user/a/aboletti/TOFHIR2C_validation/tmp_calibration_data/",
                        help="Base directory for the test results")
    parser.add_argument("--tests",
                        type=str,
                        nargs="+",
                        required=False,
                        default=[test for test in test_map.keys()],
                        help="Tests to be considered")
    parser.add_argument("--output_dir",
                        type=str,
                        default="output",
                        help="Output directory")
    return parser


def main(base_dir: str,
         tests: list[str],
         output_dir: str = "output"):
    test_result_dirs = [d for d in Path(base_dir).glob("2024*") if d.is_dir()]
    # assert that the dirs are sorted by their timestamps (yyyymmddhhmm)
    test_result_dirs = sorted(test_result_dirs, key=lambda x: int(x.stem))
    test_result_dirs

    trs = []
    for d in test_result_dirs:
        try:
            tr = TestResult(d)
            trs.append(tr)
        except FileNotFoundError as e:
            print(e)
            continue

    yc = YieldComputer(tests=tests, base_dir=base_dir)

    yield_df = yc.get_yield_data()
    # add link col
    # yield_df["link"] = yield_df.index.map(lambda x: f"http://localhost:8501/board_{x:04d}")
    yield_df.sort_index(inplace=True)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    yield_df.to_csv(f"{output_dir}/yield.csv")

    plotter = Plotter(tests=tests, base_dir=base_dir)
    merged_dfs = {test: plotter.merge_dataframes_for_test(test) for test in plotter.tests}
    for test, df in merged_dfs.items():
        if not os.path.exists(f"{output_dir}/testdata"):
            os.makedirs(f"{output_dir}/testdata")
        df.to_csv(f"{output_dir}/testdata/{test}.csv")
    

if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    main(args.base_dir, args.tests)

