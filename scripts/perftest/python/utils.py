#!/usr/bin/env python3
#-------------------------------------------------------------
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#-------------------------------------------------------------

from os.path import join
import os
import json
import subprocess
import shlex
import re
import logging

# This file contains all the utility functions required for performance test module


def get_family(current_algo, ml_algo):
    """
    Return: Algorithm family given input algorithm

    """

    for family, algos in ml_algo.items():
        if current_algo in algos:
            current_family = family
    return current_family


def split_rowcol(matrix_dim):
    """
    Return: matrix row, column on input string (e.g. 10k_1k)

    """

    k = str(0) * 3
    M = str(0) * 6
    replace_M = matrix_dim.replace('M', str(M))
    replace_k = replace_M.replace('k', str(k))
    row, col = replace_k.split('_')
    return row, col


def config_writer(write_path, config_dict):
    """
    Writes the dictionary as an configuration json file to the give path

    """

    with open(write_path, 'w') as input_file:
        json.dump(config_dict, input_file, indent=4)


def config_reader(read_path):
    """
    Return: configuration dictionary on reading the json file

    """

    with open(read_path, 'r') as input_file:
        conf_file = json.load(input_file)

    return conf_file


def create_dir(directory):
    """
    Create directory given path if the directory does not exist already

    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def get_existence(path):
    """
    Return: Boolean check if the file _SUCCESS exists

    """

    full_path = join(path, '_SUCCESS')
    exist = os.path.isfile(full_path)
    return exist


def exec_func(exec_type, file_name, args, path):
    """
    This function is responsible of execution of input arguments
    Return: Total execution time

    """

    check_exist = get_existence(path)
    if check_exist:
        total_time = 'file_exists'
    else:
        algorithm = file_name + '.dml'
        if exec_type == 'singlenode':
            exec_script = join(os.environ.get('SYSTEMML_HOME'), 'bin', 'systemml-standalone.py')

            args = ''.join(['{} {}'.format(k, v) for k, v in args.items()])
            cmd = [exec_script, algorithm, args]
            cmd_string = ' '.join(cmd)

        if exec_type == 'hybrid_spark':
            exec_script = join(os.environ.get('SYSTEMML_HOME'), 'bin', 'systemml-spark-submit.py')
            cmd = [exec_script, '-f', algorithm, '-nvargs', args]
            cmd_string = ' '.join(cmd)


        # Subrocess to execute input arguments
        # proc1_log contains the shell output which is used for time parsing
        proc1 = subprocess.Popen(shlex.split(cmd_string), stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        proc1_log = []
        while proc1.poll() is None:
            raw_std_out = proc1.stdout.readline()
            decode_raw = raw_std_out.decode('ascii').strip()
            proc1_log.append(decode_raw)
            logging.log(10, decode_raw)

        _, err1 = proc1.communicate()

        if "Error" in str(err1):
            print('Error Found in {}'.format(file_name))
            total_time = 'failure'
        else:
            total_time = get_time(proc1_log)
            full_path = join(path, '_SUCCESS')
            open(full_path, 'w').close()

    return total_time


def get_time(raw_logs):
    """
    Return: Time based on rawlogs received

    """

    for line in raw_logs:
        if line.startswith('Total execution time'):
            raw_time = line
            extract_time = re.findall(r'\d+', raw_time)
            total_time = '.'.join(extract_time)
            return total_time

    return 'not_found'


def get_config(file_path):
    """
    Return: matrix type and matrix dim based

    """

    folder_name = file_path.split('/')[-1]
    algo_prop = folder_name.split('.')
    mat_type = algo_prop[1]
    mat_dim = algo_prop[2]

    try:
        intercept = algo_prop[3]
    except IndexError:
        intercept = 'none'

    return mat_type, mat_dim, intercept
