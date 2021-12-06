#!/bin/bash
__conda_setup="$('/home/airflow/miniconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
eval "$__conda_script"

conda activate tpaws
airflow "$@"
conda deactivate
