# non-rigid-Tacto
Group Project for Robot Learning at TU Dresden -- aim is to extend the tacto tactile Simulator https://github.com/facebookresearch/tacto to work with non-rigid bodies

## Tacto usage:
ubuntu 22.04

	cd $REPO
	chmod +x dependency_solve.sh
	conda create -n "new_environment"
	conda activate "new_environment"
	./dependency_solve.sh $PathToYourAnaconda3/envs/"new_environment"

mayby comment out pip install -r requirements/dev.txt if necessary
### Test Tacto
	cd $REPO
	cd tacto/examples
	python3 demo_pybullet_digit.py
## Non-rigid-Data Pipeline 
This pipeline is used to create the soft tissue characteristics of organs the are usable in the sofa environment https://gitlab.com/nct_tso_public/nonrigid-data-generation-pipeline
#### install packages
	cd $REPO
	cd nonrigid
	pip install -r requirements.txt
	conda install libboost


### build VascuSynth

	cd vascu_synth
	sudo apt-get install libinsighttoolkit5-dev
	mkdir build
	cd build
	cmake ../sources
	cmake --build .
#### Export Path
	export VASCUSYNTH_PATH=$REPO/vascu_synth/build/VascuSynth

### Setup Blender (v3.4.1):
#### Install packages
	$yourBlenderlocation/blender-3.4.1-linux-x64//3.4/python/bin/python3.10 -m ensurepip
	$yourBlenderlocation/blender-3.4.1-linux-x64/3.4/python/bin/python3.10 -m pip install PyYAML numpy natsort
#### Export Path
	export PATH="$yourBlenderlocation/blender-3.4.1-linux-x64:$PATH"

### Setup Sofa:
download zip from here:
https://github.com/sofa-framework/sofa/releases/tag/v22.12.00
depackage in $sofaLocation (replace with your own location)
#### Export Paths
	export SOFA_ROOT="$sofaLocation/SOFA_v22.12.00_Linux"
	export PYTHONPATH=$SOFA_ROOT/plugins/SofaPython3/lib/python3/site-packages:$PYTHONPATH
### Test nonrigid:
	cd $REPO
	cd nonrigid
	python3 src/run_nonrigid_displacement.py --data_path data/sample_data --launch_sofa_gui --show_full_errors --num_samples 1
If successfull the sofa environment should open automatically, if the Pipeline only had partial success delete the nonridig/data folder
### Setup STLIB:
Stlib is a plugin for Sofa that has to be manually installed from https://github.com/SofaDefrost/STLIB it can be done automatically
#### via Skript:
	cd $REPO
	./stlibInstall.sh
#### Export Path
	export PYTHONPATH=$REPO/stlib/build/lib/python3/site-packages:$PYTHONPATH
### Test Stlib:
	cd $REPO
	python3 sofa_example/src/sofa_example.py
This should also open up a sofa environment with a cube and a sphere added via STLIB

## Recommendations
It is highly recommended to put all of the path exports in your ~/.bashrc (obviously replace the variables except $SOFA_ROOT with your own directories):
#### Paths
	export VASCUSYNTH_PATH=$REPO/vascu_synth/build/VascuSynth
	export PATH=$yourBlenderlocation/blender-3.4.1-linux-x64:$PATH
	export SOFA_ROOT="$sofaLocation/SOFA_v22.12.00_Linux"
	export PYTHONPATH=$SOFA_ROOT/plugins/SofaPython3/lib/python3/site-packages:$PYTHONPATH
	export PYTHONPATH=$REPO/stlib/build/lib/python3/site-packages:$PYTHONPATH
	export PYTHONPATH=$REPO/robot_learning/nonrigid/src:$PYTHONPATH
## Trivia
	https://sofapython3.readthedocs.io/en/latest/content/modules/Sofa/generated/Sofa.Core/classes/Sofa.Core.DataContainer.html
	Sofa can also be installed directly in anaconda via https://github.com/sofa-framework/conda-ci
	conda install libboost=1.84.0 --channel conda-forge
	conda install python=3.12.3
	conda install sofa-app sofa-python3 --channel sofa-framework
	but there is only version 23.12+ available which is incompatible with the https://gitlab.com/nct_tso_public/nonrigid-data-generation-pipeline used in "nonrigid"



    

Important Paper: https://arxiv.org/pdf/2402.01181
