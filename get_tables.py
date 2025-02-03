import pandas as pd
import re
import os
import pickle
import tqdm
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

        self.sn_regex = re.compile(r"SN_3211[\s_]0[\s_]03[\s_]0[\s_]00[\s_]([\d]+)\.txt")
        self.serial_files = [f for f in Path(self.path).rglob('SN_3211*.txt')]
        # make sure that the last split has numbers in front of the stem
        self.serial_files = [f for f in self.serial_files if self.sn_regex.match(f.name)]
        assert len(self.serial_files) > 0, "No serial files found in the directory"

        self.tester_to_serial = {}
        for f in self.serial_files: 
            if " " in f.stem:
                sn = int(f.stem.split(" ")[-1])
            else:
                sn = int(f.stem.split("_")[-1])
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
        
        def get_test_result_dirs(base_dir: str):
            test_result_dirs = [d for d in Path(base_dir).glob("2024*") if d.is_dir()]
            # assert that the dirs are sorted by their timestamps (yyyymmddhhmm)
            test_result_dirs = sorted(test_result_dirs, key=lambda x: int((x.stem).strip("_")))
            # filter out the dirs that do not contain a file called "detailed_results.tsv"
            test_result_dirs = [d for d in test_result_dirs if (d / "detailed_results.tsv").exists()]
            sn_regex = re.compile(r"SN_3211[\s_]0[\s_]03[\s_]0[\s_]00[\s_]([\d]+)\.txt")
            test_result_dirs_good_format = [d for d in test_result_dirs if
                            len(sn_regex.findall("".join([str(p) for p in Path(d).rglob("SN_3211*.txt")]))) == 8]
            print(f"Found {len(test_result_dirs_good_format)} directories with the correct format")
            test_result_dirs_bad_format = [d for d in test_result_dirs if d not in test_result_dirs_good_format]
            print(f"Found {len(test_result_dirs_bad_format)} directories with the wrong format")
            return sorted(test_result_dirs_good_format, key=lambda x: int(x.stem))
        
        self.test_result_dirs = get_test_result_dirs(self.base_dir)


    def merge_dataframes_for_test(self,
                                  test: str):
        merged_dataframe = pd.DataFrame()
        skipped = []
        for d in self.test_result_dirs:
            print(d)
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
        return merged_dataframe


    def get_yield_data(self):
        result = []
        for test in self.tests:
            print(f"Processing test {test}")
            result.append(self.merge_dataframes_for_test(test).rename(columns={"test_pass": f"{test}_pass"}))
        return pd.concat(result, axis=1)


class Plotter:
    
    def __init__(self,
                 tests: list,
                 base_dir: str | Path) -> None:
        self.tests = tests
        self.base_dir = base_dir
        

        def get_test_result_dirs(base_dir: str):

            test_result_dirs = [d for d in Path(base_dir).glob("2024*") if d.is_dir()]
            # assert that the dirs are sorted by their timestamps (yyyymmddhhmm)
            test_result_dirs = sorted(test_result_dirs, key=lambda x: int((x.stem).strip("_")))
            # filter out the dirs that do not contain a file called "detailed_results.tsv"
            test_result_dirs = [d for d in test_result_dirs if (d / "detailed_results.tsv").exists()]
            sn_regex = re.compile(r"SN_3211[\s_]0[\s_]03[\s_]0[\s_]00[\s_]([\d]+)\.txt")
            test_result_dirs_good_format = [d for d in test_result_dirs if
                            len(sn_regex.findall("".join([str(p) for p in Path(d).rglob("SN_3211*.txt")]))) == 8]
            print(f"Found {len(test_result_dirs_good_format)} directories with the correct format")
            test_result_dirs_bad_format = [d for d in test_result_dirs if d not in test_result_dirs_good_format]
            print(f"Found {len(test_result_dirs_bad_format)} directories with the wrong format")
            return sorted(test_result_dirs_good_format, key=lambda x: int(x.stem))
        
        self.test_result_dirs = get_test_result_dirs(self.base_dir)


    def merge_dataframes_for_test(self,
                                  test: str):
        merged_dataframe = pd.DataFrame()
        skipped = []
        for d in self.test_result_dirs:
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
                        required=False,
                        default="/eos/user/a/aboletti/TOFHIR2C_validation/calibration_data_v2p1/",
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
    
    #    yc = YieldComputer(tests=tests, base_dir=base_dir)
    #
    #    yield_df = yc.get_yield_data()
    #    # add link col
    #    # yield_df["link"] = yield_df.index.map(lambda x: f"http://localhost:8501/board_{x:04d}")
    #    yield_df.sort_index(inplace=True)
    #    if not os.path.exists(output_dir):
    #        os.makedirs(output_dir)
    #    yield_df.to_csv(f"{output_dir}/yield.csv")

    # check if some tests are already in the output directory
    # if so, don't process them again (if overwrite is False)
    if os.path.exists(f"{output_dir}"):
        existing_tests = [f.replace(".h5", "") for f in str(Path(f"{output_dir}").rglob("*.h5"))] 
        for test in tests:
            if test in existing_tests:
                tests.remove(test)

    p = Plotter(tests=tests, base_dir=base_dir)
    merged_dfs = {}
    for test in tqdm(tests):
        merged_dfs[test] = p.merge_dataframes_for_test(test)

    # keep track of the unique SNs
    unique_sns = {} 
    for test, df in merged_dfs.items():
        if not os.path.exists(f"{output_dir}"):
            os.makedirs(f"{output_dir}")
        #df.to_csv(f"{output_dir}/testdata/{test}.csv")
        unique_sns[test] = df.index.unique()
        df.to_hdf(f"{output_dir}/{test}.h5", key='data', mode='w', format='table', data_columns=True)
    
    # check if the unique SNs are the same for all tests
    print("Unique SNs for each test")
    print({test: len(sns) for test, sns in unique_sns.items()})
    # store the unique SNs in a file
    with open(f"{output_dir}/unique_sns.pkl", "wb") as file:
        # merge all the unique SNs with reduce and set.union
        all_sns = set().union(*unique_sns.values())
        pickle.dump(list(all_sns), file)
    print(f"Unique SNs stored in {output_dir}/unique_sns.pkl")
    

if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    main(args.base_dir, args.tests, args.output_dir)

