
# Installation Instructions for a Nvidia Jetson AGX Orin running Ubuntu 22

These steps help set up an environment compatible with NVIDIA Jetson and YOLOv10.

---

## 💡 Check JetPack Version

```bash
apt-cache show nvidia-jetpack  # Example output: 5.1.3-b29
```

---

## 🔧 System Dependencies

```bash
sudo apt update
sudo apt install python3.10 python3.10-dev python3.10-venv ccache apt-utils
```

---

## 🐍 Python Environment Setup

```bash
alias python=python3.10
python -m venv yolov10-env
source yolov10-env/bin/activate
```

---

## 🔥 PyTorch & TorchVision (Jetson-Compatible)

1. **Install Torch 2.1.0a0+41361538.nv23.06**  
   ```bash
   wget https://developer.download.nvidia.cn/compute/redist/jp/v512/pytorch/torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl
   pip install torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl
   ```

2. **Install dependencies if compiling Torch**  
   ```bash
   export CMAKE_CUDA_COMPILER=/usr/local/cuda-11.4/bin/nvcc
   rm -rf /root/pytorch/build/
   sudo apt-get install libopenblas-base libopenmpi-dev libomp-dev
   ```

3. **Install TorchVision v0.16.1**
   ```bash
   git clone --branch v0.16.1 https://github.com/pytorch/vision torchvision
   cd torchvision
   python setup.py install
   ```

---

## 🔍 YOLOv10 Installation

```bash
pip install -q git+https://github.com/THU-MIG/yolov10.git
git clone https://github.com/THU-MIG/yolov10
```

*More info: [Roboflow blog on YOLOv10](https://blog.roboflow.com/yolov10-how-to-train/)*

---

## 📢 Additional Libraries

```bash
sudo apt install espeak libnfc-bin libnfc-examples libnfc-dev
```

---

## 🧲 GPIO Setup

Reference: https://github.com/NVIDIA/jetson-gpio

```bash
python -m pip install Jetson.GPIO
sudo groupadd -f -r gpio
sudo usermod -a -G gpio your_user_name
sudo cp /root/yolov5-env/lib/python3.8/site-packages/Jetson/GPIO/99-gpio.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## 📦 Python Packages

```bash
pip install pandas opencv-python paramiko mysql-connector-python geocoder huggingface_hub \
pyttsx3 pyzbar nfcpy pyudev evdev adafruit-circuitpython-servokit pyyaml typing_extensions \
numpy==1.26.1
```

## 📺 Touchscreen & Brightness

Touchscreen setup:  
https://www.waveshare.com/wiki/8DP-CAPLCD  
Brightness control using `ddcutil`:

```bash
sudo apt-get install ddcutil -y
sudo ddcutil detect
sudo ddcutil setvcp 10 <value>  # Replace <value> with brightness level
```

---

## 🧪 Alternate Torch/Torchvision Builds

```bash
pip install torchvision-0.20.0a0+6344041-cp310-cp310-linux_aarch64.whl
pip install torch-2.4.0a0+f70bd71a48.nv24.06.15634931-cp310-cp310-linux_aarch64.whl
```

---

## 🗣️ Text-to-Speech

```bash
pip install piper-tts
```

---

## 📝 Notes

- Compare PyTorch/TorchVision builds: https://pypi.org/project/torchvision/
- NVIDIA's Jetson PyTorch builds: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048

---

Feel free to modify according to your system paths and Jetson variant.
