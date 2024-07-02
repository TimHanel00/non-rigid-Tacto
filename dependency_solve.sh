#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <PathToYourAnacondaEnvDir>"
    exit 1
fi
PathToYourAnacondaEnvDir="$1"
git submodule update --init --recursive
cd tacto
pip install -r requirements/examples.txt
pip install -e .
pip install -r requirements/dev.txt




sed -i 's/fractions/math/g' $PathToYourAnacondaEnvDir/lib/python3.9/site-packages/networkx/algorithms/dag.py

sed -i 's/np.int,/int,/g' $PathToYourAnacondaEnvDir/lib/python3.9/site-packages/networkx/readwrite/graphml.py

sed -i 's/np.float,/float,/g' $PathToYourAnacondaEnvDir/lib/python3.9/site-packages/urdfpy/urdf.py


sed -i 's/np.float)/float)/g' $PathToYourAnacondaEnvDir/lib/python3.9/site-packages/urdfpy/urdf.py
sed -i 's/np.float)/float)/g' ./tacto/renderer.py

cd examples
python demo_pybullet_digit.py
