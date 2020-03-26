#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018-2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: EPL-2.0
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

from argparse import ArgumentParser
from common import platform_util
from common.utils.validators import (check_positive_number, check_valid_filename, check_valid_file_or_dir,
                                     check_valid_folder, check_positive_number_or_equal_to_negative_one)


class BaseBenchmarkUtil(object):
    """Base benchmark util class"""
    MODEL_INITIALIZER = "model_init"

    def __init__(self, platform_util_obj=None):
        self._common_arg_parser = None
        self._define_args()
        self.args, _ = self._common_arg_parser.parse_known_args()
        # currently used for testing, need to be able to pass in mocked values
        # TODO: but also, why is this class not inheriting PlatformUtil?
        self._platform_util = platform_util_obj or platform_util.PlatformUtil(self.args)
        self._validate_args()

    def _define_args(self):
        """define args for the benchmark interface shared by FP32 and int8
        models"""

        # only require the arg, if we aren't just printing out --help
        required_arg = "--help" not in sys.argv

        self._common_arg_parser = ArgumentParser(
            add_help=False, description="Parse args for base benchmark "
                                        "interface")

        self._common_arg_parser.add_argument(
            "-f", "--framework",
            help="Specify the name of the deep learning framework to use.",
            dest="framework", default=None, required=required_arg)

        self._common_arg_parser.add_argument(
            "-r", "--model-source-dir",
            help="Specify the models source directory from your local machine",
            nargs="?", dest="model_source_dir", type=check_valid_folder)

        self._common_arg_parser.add_argument(
            "-p", "--precision",
            help="Specify the model precision to use: fp32, int8, or bfloat16",
            required=required_arg, choices=["fp32", "int8", "bfloat16"],
            dest="precision")

        self._common_arg_parser.add_argument(
            "-mo", "--mode", help="Specify the type training or inference ",
            required=required_arg, choices=["training", "inference"], dest="mode")

        self._common_arg_parser.add_argument(
            "-m", "--model-name", required=required_arg,
            help="model name to run benchmarks for", dest="model_name")

        self._common_arg_parser.add_argument(
            "-b", "--batch-size",
            help="Specify the batch size. If this parameter is not specified "
                 "or is -1, the largest ideal batch size for the model will "
                 "be used",
            dest="batch_size", default=-1,
            type=check_positive_number_or_equal_to_negative_one)

        self._common_arg_parser.add_argument(
            "--mpi_num_processes", type=check_positive_number,
            help="The number of MPI processes",
            dest="mpi", default=None)

        self._common_arg_parser.add_argument(
            "--mpi_num_processes_per_socket", type=check_positive_number,
            help="Specify how many MPI processes to launch per socket",
            dest="num_mpi", default=1)

        self._common_arg_parser.add_argument(
            "-d", "--data-location",
            help="Specify the location of the data. If this parameter is not "
                 "specified, the benchmark will use random/dummy data.",
            dest="data_location", default=None, type=check_valid_file_or_dir)

        self._common_arg_parser.add_argument(
            "-i", "--socket-id",
            help="Specify which socket to use. Only one socket will be used "
                 "when this value is set. If used in conjunction with "
                 "--num-cores, all cores will be allocated on the single "
                 "socket.",
            dest="socket_id", type=int, default=-1)

        self._common_arg_parser.add_argument(
            "-n", "--num-cores",
            help="Specify the number of cores to use. If the parameter is not"
                 " specified or is -1, all cores will be used.",
            dest="num_cores", type=int, default=-1)

        self._common_arg_parser.add_argument(
            "--num-instances", type=check_positive_number,
            help="Specify the number of instances to run.",
            dest="num_instances", default=1)

        self._common_arg_parser.add_argument(
            "-a", "--num-intra-threads", type=check_positive_number,
            help="Specify the number of threads within the layer",
            dest="num_intra_threads", default=None)

        self._common_arg_parser.add_argument(
            "-e", "--num-inter-threads", type=check_positive_number,
            help="Specify the number threads between layers",
            dest="num_inter_threads", default=None)

        self._common_arg_parser.add_argument(
            "-np", "--num-processes", type=check_positive_number,
            help="Specify the number of processes to run on as mpirun '-np' "
                 "input for multi-instance execution. ",
            dest="num_processes", default=1)

        self._common_arg_parser.add_argument(
            "-ppn", "--num-processes-per-node", type=check_positive_number,
            help="Specify the number of processes per node as mpirun '-ppn' "
                 "input for multi-instance execution. ",
            dest="num_processes_per_node", default=1)

        self._common_arg_parser.add_argument(
            "-ts", "--num-train-steps", type=check_positive_number,
            help="Specify the number of training steps ",
            dest="num_train_steps", default=1)

        self._common_arg_parser.add_argument(
            "--data-num-intra-threads", type=check_positive_number,
            help="The number intra op threads for the data layer config",
            dest="data_num_intra_threads", default=None)

        self._common_arg_parser.add_argument(
            "--data-num-inter-threads", type=check_positive_number,
            help="The number inter op threads for the data layer config",
            dest="data_num_inter_threads", default=None)

        self._common_arg_parser.add_argument(
            "-c", "--checkpoint",
            help="Specify the location of trained model checkpoint directory. "
                 "If mode=training model/weights will be written to this "
                 "location. If mode=inference assumes that the location points"
                 " to a model that has already been trained. Note that using "
                 "checkpoint files for inference is being deprecated, in favor "
                 "of using frozen graphs.",
            dest="checkpoint", default=None, type=check_valid_folder)

        self._common_arg_parser.add_argument(
            "-g", "--in-graph", help="Full path to the input graph ",
            dest="input_graph", default=None, type=check_valid_filename)


        self._common_arg_parser.add_argument(
            "-k", "--benchmark-only",
            help="For benchmark measurement only. If neither --benchmark-only "
                 "or --accuracy-only are specified, it will default to run "
                 "benchmarking.",
            dest="benchmark_only", action="store_true")

        self._common_arg_parser.add_argument(
            "--accuracy-only",
            help="For accuracy measurement only.  If neither --benchmark-only "
                 "or --accuracy-only are specified, it will default to run "
                 "benchmarking.",
            dest="accuracy_only", action="store_true")

        self._common_arg_parser.add_argument(
            "--output-results",
            help="Writes inference output to a file, when used in conjunction "
                 "with --accuracy-only and --mode=inference.",
            dest="output_results", action="store_true")

        # Note this can't be a normal boolean flag, because we need to know when the user
        # does not explicitly set the arg value so that we can apply the appropriate
        # default value, depending on the the precision.
        self._common_arg_parser.add_argument(
            "--disable-tcmalloc",
            help="When TCMalloc is enabled, the google-perftools are installed (if running "
                 "using docker) and the LD_PRELOAD environment variable is set to point to "
                 "the TCMalloc library file. The TCMalloc memory allocator produces better "
                 "performance results with smaller batch sizes. This flag disables the use of "
                 "TCMalloc when set to True. For int8 benchmarking, TCMalloc is enabled by "
                 "default (--disable-tcmalloc=False). For other precisions, the flag is "
                 "--disable-tcmalloc=True by default.",
            dest="disable_tcmalloc", choices=["True", "False"],
            default=None
        )

        self._common_arg_parser.add_argument(
            "--tcmalloc-large-alloc-report-threshold",
            help="Sets the TCMALLOC_LARGE_ALLOC_REPORT_THRESHOLD environment variable to "
                 "the specified value. The environment variable sets the threshold (in bytes) "
                 "for when large memory allocation messages will be displayed.",
            dest="tcmalloc_large_alloc_report_threshold", default=2147483648, type=int
        )

        self._common_arg_parser.add_argument(
            "-v", "--verbose", help="Print verbose information.",
            dest="verbose", action="store_true")

        self._common_arg_parser.add_argument(
            "--output-dir",
            help="Folder to dump output into. The output directory will default to "
                 "'models/benchmarks/common/tensorflow/logs' if no path is specified.",
            default="/models/benchmarks/common/tensorflow/logs")

        # Allow for additional command line args after --
        self._common_arg_parser.add_argument(
            "model_args", nargs="*",
            help="Additional command line arguments (prefix flag start with"
                 " '--').")

    def _validate_args(self):
        """validate the args and initializes platform_util"""
        # check if socket id is in socket number range
        num_numas = self._platform_util.num_numa_nodes
        args = self.args
        if not -1 <= args.socket_id < num_numas:
            raise ValueError("Socket id must be within NUMA number range: "
                             "[0, {}].".format(num_numas - 1))

        # check number of cores
        num_logical_cores_per_socket = \
            self._platform_util.num_cores_per_socket * \
            self._platform_util.num_threads_per_core
        # if a socket_id is specified, only count cores from one socket
        system_num_cores = num_logical_cores_per_socket if \
            args.socket_id != -1 else num_logical_cores_per_socket * \
            self._platform_util.num_cpu_sockets
        num_cores = args.num_cores

        if (num_cores <= 0) and (num_cores != -1):
            raise ValueError(
                "Core number must be greater than 0 or -1. The default value "
                "is -1 which means using all the cores in the sockets")
        elif num_cores > system_num_cores:
            raise ValueError("Number of cores exceeds system core number: {}".
                             format(system_num_cores))

        if args.output_results and ((args.model_name != "resnet50" and
                                    args.model_name != "resnet50v1_5") or args.precision != "fp32"):
            raise ValueError("--output-results is currently only supported for resnet50 FP32 inference.")
        elif args.output_results and (args.mode != "inference" or not args.data_location):
            raise ValueError("--output-results can only be used when running inference with a dataset.")

    def initialize_model(self, args, unknown_args):
        """Create model initializer for the specified model"""
        model_initializer = None
        model_init_file = None
        if args.model_name:  # not empty
            current_path = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))

            # find the path to the model_init.py file
            filename = "{}.py".format(self.MODEL_INITIALIZER)
            model_init_file = os.path.join(current_path, args.use_case,
                                           args.framework, args.model_name,
                                           args.mode, args.precision,
                                           filename)
            package = ".".join([args.use_case, args.framework,
                                args.model_name, args.mode, args.precision])
            model_init_module = __import__(
                package + "." + self.MODEL_INITIALIZER, fromlist=["*"])
            model_initializer = model_init_module.ModelInitializer(
                args, unknown_args, self._platform_util)

        if model_initializer is None:
            raise ImportError("Unable to locate {}.".format(model_init_file))

        return model_initializer
