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

import pandas as pd

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
            self, benchmark, fuzzer, trial_id, file_name, line, column, time,
            recoreded_segments):
        """Adds an entry to the segment_df."""
        segment_entry = [
            benchmark, fuzzer, trial_id, time, file_name, line, column
        ]

        if [line, column] not in recoreded_segments:
            insert_series = pd.Series(segment_entry,
                                      index=self.segment_df.columns)
            self.segment_df = self.segment_df.append(insert_series,
                                                     ignore_index=True)

    def remove_redundant_entries(self):
        """Removes redundant entries in segment_df. Before calling this
        method, for each time stamp, segment_df contains all segments that are
        covered in this time stamp. After calling this method, for each time
        stamp, segment_df only contains segments that have been covered since
        the previous time stamp. This significantly reduces the size of the
        resulting CSV file."""
        try:
            # Drop duplicates but with different timestamps in segment data.
            self.segment_df = self.segment_df.sort_values(by=['time'])
            self.segment_df = self.segment_df.drop_duplicates(
                subset=self.segment_df.columns.difference(['time']),
                keep='first')

        except (ValueError, KeyError, IndexError):
            coverage_utils.logger.error(
                'Error occurred when removing duplicates.')


def extract_segments_and_functions_from_summary_json(
        # pylint: disable=too-many-arguments
        summary_json_file,
        benchmark,
        fuzzer,
        trial_id,
        time,
        trial_specific_coverage_data):
    """Return a trial-specific data frame container with segment and function
     coverage information given a trial-specific coverage summary json file."""

    recorded_segments = [[
        trial_specific_coverage_data.segment_df['line'][i],
        trial_specific_coverage_data.segment_df['column'][i]
    ] for i in trial_specific_coverage_data.segment_df.index]

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
                        time,
                        recorded_segments)

    except (ValueError, KeyError, IndexError):
        coverage_utils.logger.error(
            'Failed when extracting trial-specific segment and function '
            'information from coverage summary.')

    return trial_specific_coverage_data
