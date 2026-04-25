> **! Note**: Manual installation is only available for _Linux_ operating systems inlcluding WSL2 linux
### Get the code
First, download and checkout the latest release as per usual
```shell script
# from a directory of your choice
git clone https://github.com/weberlab-hhu/Helixer.git
cd Helixer
```

### System dependencies

#### Python 3.10
It is old but we have to use old libraries - we will use a venv one here 
We need to use the deadsnakes repo for older libraries  



#### Python development libraries
Ubuntu (& co.)
```shell script
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10-venv
sudo apt install -y libze1 libze-intel-gpu1
sudo apt install intel-opencl-icd
```

### Virtualenv (optional)
We **strongly** recommend installing all the python packages in a
virtual environment: https://docs.python-guide.org/dev/virtualenvs/


For example, create and activate an environment called 'intelenv': and install the intel requirements  
```shell script
python3.10 -m venv intelenv
source intelenv/bin/activate
pip install requests
pip install -r requirements.3.10.intelXPU.txt

```
This installs requirements including some intel libraries currently including:  
intel dpcpp-cpp-rt==2024.2.1 which has been tested  
dpcpp-cpp-rt==2025.0.1 might work as well it is offically supported on the last intel TF maintainance release 

The steps below assume you are working in the same environment.

### Post processor

https://github.com/TonyBolger/HelixerPost

Setup according to included instructions and
further add the compiled `helixer_post_bin` to 
your system PATH or drop it into a exe directory like /usr/local/bin


### Helixer itself

```shell script
# from the Helixer directory
pip install .  # or `pip install -e .`, if you will be changing the code
```

#### Test Helixer
Helixer comes with test data and unit tests.
```bash
# switch to the Helixer code subdirectory
cd Helixer/helixer
# run the unit tests
pytest --verbose tests/test_helixer.py
```

### XPU requirements 
We use intel tensorflow extensions these should register as XPU 
When does it pay off? 
 (your CPU ends in HX the GPU is crippled for use with NVIDA so use that)  UHD Graphics 710  - no much slower ca 2024 processur Like Core i3/5/7
 ARC 
 | Intel Generation / Series | Representative Processor | iGPU Architecture (Cores/EUs) | FP32 TFLOPS AI  (Peak) | Tested / DL Inference Comments |
| :--- | :--- | :--- | :--- | :--- |
| **Core 14th Gen (HX)** | i9-14900HX | UHD 770 (32 EU) | **0.8 - 0.9** | **HX** normally coupled with NVIDIA use that one. **Tested** and starts helixer bur crippling slow  |
| **Core 14th Gen (H)** | i7-14700H | Iris Xe (96 EU) | **2.2 - 2.5** |  Uses older Vector Engines. **untested**|
| **Core Ultra Series 1 (H)** | Ultra 7 155H | Arc Xe-LPG (8 Xe) | **4.5 - 4.7** | **New** Good driver support via Intel Extension for TensorFlow (ITEX). **untested**|
| **Core Ultra Series 2 (V)** | Ultra 7 258V | Arc Xe2-LPG (8 Xe2) | **4.0 - 4.2** | **untested** |
| **Core Ultra Series 2 (H)** | Ultra 9 285H | Arc Xe-LPG+ (8 Xe) | **4.6 - 4.9** | **likely intel supported.** and fastish. **untested**|
| **Core Ultra Series 2 (HX)**| Ultra 9 285HX | Arc Xe-LPG+ (4 Xe) | **2.1 - 2.4** | avoid HX iGPU core count is halved compared to "H" chips. **untested**|
| **Core Ultra Series 3 (H)** | Ultra X9 388H | Arc Xe3-LPG (12 Xe3)| **6.5 - 7.5** | **Might not be suppoerted anymore by intel**. **untested**|


```bash
# Verify the installation:
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('XPU'))"

# sometimes the following error will pop up: Unable to register cuDNN factory... (and other factories)
# sometimes the following warning will pop up: tensorflow/compiler/tf2tensorrt/utils/py_utils.cc:38] TF-TRT Warning: Could not find TensorRT
# usually those can be ignored and will not impair Helixer's performance
```
### Known Issues
when you run helixer and encounter some gibberish like "F tensorflow/core/framework/tensor.cc:847] Check failed: IsAligned() ptr "  
``` export ITEX_ENABLE_NEXTPLUGGABLE_DEVICE=0 ```  
it occurs on an Intel UHD which should not be used  
