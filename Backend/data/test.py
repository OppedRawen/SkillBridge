import cupy as cp
print("CUDA Devices Available:", cp.cuda.runtime.getDeviceCount())
print("Current Device ID:", cp.cuda.runtime.getDevice())