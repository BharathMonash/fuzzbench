# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility DetailedCoverageData class and functions for report generation on
segment and function coverage for the entire experiment
(all Fuzzer-benchmark-trial combinations)."""

import os
import hashlib

import pandas as pd

from common import experiment_path as exp_path
from common import filestore_utils
from experiment.measurer import coverage_utils


class DetailedCoverageData:  # pylint: disable=too-many-instance-attributes
    """Maintains segment and function coverage information, and writes this
    information to CSV files."""

    def __init__(self):
        """Constructor"""
        # Set by generate_data_frames_after_adding_all_entries().
        self.segment_df = pd.DataFrame(columns=[
            'benchmark', 'fuzzer', 'trial', 'time', 'file', 'line', 'column'
        ])
        self.function_df = pd.DataFrame(columns=[
            'benchmark', 'fuzzer', 'trial', 'time', 'function', 'hits'
        ])

    def add_function_entry(  # pylint: disable=too-many-arguments
            self, benchmark, fuzzer, trial_id, function, function_hits, time):
        """Adds an entry to the function_df."""
        function_entry = [
            benchmark, fuzzer, trial_id, time, function, function_hits
        ]
        insert_series = pd.Series(function_entry,
                                  index=self.function_df.columns)
        self.function_df = self.function_df.append(insert_series,
                                                   ignore_index=True)

    def add_segment_entry(  # pylint: disable=too-many-arguments
            self, benchmark, fuzzer, trial_id, file_name, line, column, time):
        """Adds an entry to the segment_df."""
        segment_entry = [
            benchmark, fuzzer, trial_id, time, file_name, line, column
        ]

        insert_series = pd.Series(segment_entry, index=self.segment_df.columns)
        self.segment_df = self.segment_df.append(insert_series,
                                                 ignore_index=True)

    def generate_csv_files(self, trial_specific_directory, trial_id, cycle):
        """Generates three compressed CSV files containing coverage information
        for all fuzzers, benchmarks, and trials. To maintain a small file size,
        all strings, such as file and function names, are referenced by id and
        resolved in 'names.csv'."""

        # Write CSV files to filestore.
        def csv_filestore_helper(file_name, df, file_type):
            """Helper method for storing csv files in filestore."""

            if file_type == 'function':
                src = os.path.join(trial_specific_directory, 'function',
                                   file_name)
            else:
                src = os.path.join(trial_specific_directory, 'segments',
                                   file_name)

            dst = exp_path.filestore(src)
            df.to_csv(src, index=False, compression='infer')
            filestore_utils.cp(src, dst)

        csv_filestore_helper('functions_{trial_id}_{cycle}.csv.gz',
                             self.function_df)
        csv_filestore_helper('segments_{trial_id}_{cycle}.csv.gz',
                             self.segment_df)


def extract_segments_and_functions_from_summary_json(  # pylint: disable=too-many-locals
        summary_json_file, benchmark, fuzzer, trial_id, time):
    """Return a trial-specific data frame container with segment and function
     coverage information given a trial-specific coverage summary json file."""

    trial_specific_coverage_data = DetailedCoverageData()

    try:
        coverage_info = coverage_utils.get_coverage_infomation(
            summary_json_file)
        # Extract coverage information for functions.
        for function_data in coverage_info['data'][0]['functions']:
            trial_specific_coverage_data.add_function_entry(
                benchmark, fuzzer, trial_id, function_data['name'],
                function_data['count'], time)

        # Extract coverage information for segments.
        for file in coverage_info['data'][0]['files']:
            for segment in file['segments']:
                if segment[2] != 0:  # Segment hits.
                    trial_specific_coverage_data.add_segment_entry(
                        benchmark,
                        fuzzer,
                        trial_id,
                        file['filename'],
                        segment[0],  # Segment line.
                        segment[1],  # Segment column.
                        time)

    except (ValueError, KeyError, IndexError):
        coverage_utils.logger.error(
            'Failed when extracting trial-specific segment and function '
            'information from coverage summary.')

    return trial_specific_coverage_data
