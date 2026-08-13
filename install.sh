#!/bin/bash
# This script automates the creation and installation
# of the conda environmnet. It's useful for working
# in the docker file and on travis, but it's not
# necessary for individual users to use it.
# Developers are encouraged to only run scripts
# that they fully understand, and may prefer to
# run aspects of this script manually to set-up
# openwpm.
# This script will remove an existing openwpm
# conda environment if it exists.
# Arguments:
# --skip-create: Doesn't change the openwpm conda environment
set -e
# Make conda available to shell script
eval "$(conda shell.bash hook)"
if [ "$1" != "--skip-create" ]; then
  echo 'Creating / Overwriting openwpm conda environment.'
  # `PYTHONNOUSERSITE` set so python ignores local user site libraries when building the env
  # See: https://github.com/openwpm/OpenWPM/pull/682#issuecomment-645648939
  #
  # `CONDA_REPODATA_USE_SHARDS=false` works around a bug in newer conda /
  # conda-libmamba-solver versions where the sharded-repodata SQLite cache
  # (repodata_shards.db) can raise "sqlite3.OperationalError: database is
  # locked" when a network-fetch thread and a cache-read thread hit it at
  # the same time. See: https://github.com/conda/conda-libmamba-solver/issues/925
  # Retrying is a belt-and-suspenders fallback for the same race condition.
  export CONDA_REPODATA_USE_SHARDS=false

  n=0
  until [ "$n" -ge 3 ]
  do
    PYTHONNOUSERSITE=True conda env create -q -f environment.yaml && break
    n=$((n+1))
    echo "conda env create failed (attempt $n/3), retrying in 5s..."
    sleep 5
  done
  if [ "$n" -ge 3 ]; then
    echo "conda env create failed after 3 attempts." >&2
    exit 1
  fi
fi
echo 'Activating environment.'
conda activate openwpm
echo 'Building extension.'
./scripts/build-extension.sh
echo 'Installation complete, activate your new environment by running:'
echo 'conda activate openwpm'
