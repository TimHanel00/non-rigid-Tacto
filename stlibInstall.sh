#!/bin/bash
if [ -z "$SOFA_ROOT" ]; then
    echo "Error: SOFA_ROOT environment variable is not set."
else
    echo "SOFA_PYTHON is set to $SOFA_ROOT"
fi

if [ -z "$CONDA_PREFIX" ]; then
    echo "Error: CONDA_PREFIX environment variable is not set."
else
    echo "CONDA_PREFIX is set to $CONDA_PREFIX"
fi
if [ ! -z "$SOFA_ROOT" ]; then 
	if [ ! -z "$CONDA_PREFIX" ]; then
			echo "in here"
			cd stlib
			echo $HOME/.bashrc
			rm -r build
			mkdir build
			cd build
			conda install -c conda-forge libstdcxx-ng
			cmake -DCMAKE_PREFIX_PATH:=$SOFA_ROOT -DPLUGIN_SOFAPYTHON=ON -DSOFA_BUILD_METIS=ON ..
			cmake --build .
			export PYTHONPATH=$REPO/stlib/build/lib/python3/site-packages:$PYTHONPATH
		fi
fi
