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
"""Tests for detailed_coverage_data_utils.py"""
import os

from experiment.measurer import detailed_coverage_data_utils

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'test_data')

# Expected Constants.
SUMMARY_JSON_FILE = 'cov_summary.json'
NUM_FUNCTION_IN_COV_SUMMARY = 3
NUM_COVERED_SEGMENTS_IN_COV_SUMMARY = 16
FILE_NAME = '/home/test/fuzz_no_fuzzer.cc'
FUNCTION_NAMES = ['main', '_Z3fooIfEvT_', '_Z3fooIiEvT_']
BENCHMARK = 'benchmark_1'
FUZZER = 'fuzzer_1'
TIMESTAMP = 900
TRIAL_ID = 2


def get_test_data_path(*subpaths):
    """Returns the path of |subpaths| relative to TEST_DATA_PATH."""
    return os.path.join(TEST_DATA_PATH, *subpaths)


def test_extract_segments_and_functions_from_summary_json_for_segments(fs):
    """Tests that segments and functions from summary json properly extracts the
     information and also test for integrity of fuzzer, benchmark and function
     ids in segment_df for a given summary json file."""

    summary_json_file = get_test_data_path(SUMMARY_JSON_FILE)
    fs.add_real_file(summary_json_file, read_only=False)

    trial_specific_coverage_data = detailed_coverage_data_utils.\
        DetailedCoverageData()

    trial_specific_coverage_data = (
        detailed_coverage_data_utils.
        extract_segments_and_functions_from_summary_json(
            summary_json_file, BENCHMARK, FUZZER, TRIAL_ID, TIMESTAMP,
            trial_specific_coverage_data))

    # Assert length of resulting data frame is as expected.
    assert len(trial_specific_coverage_data.segment_df) == 16
    assert len(trial_specific_coverage_data.function_df) == 3
