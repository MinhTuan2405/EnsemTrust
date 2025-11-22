# GPU Training Setup Guide

## Prerequisites

### 1. NVIDIA GPU with CUDA Support
- Check GPU compatibility: https://developer.nvidia.com/cuda-gpus
- Minimum: CUDA Compute Capability 3.5+
- Recommended: RTX 20xx/30xx/40xx series or higher

### 2. Install NVIDIA Drivers
```powershell
# Download from: https://www.nvidia.com/Download/index.aspx
# Verify installation:
nvidia-smi
```

### 3. Install NVIDIA Container Toolkit (Windows WSL2)

#### Enable WSL2
```powershell
wsl --install
wsl --set-default-version 2
```

#### Inside WSL2, install NVIDIA Container Toolkit
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### Verify GPU access in Docker
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## Usage

### 1. Build GPU-enabled Dagster Image
```powershell
docker compose -f docker-compose.gpu.yml build dagster-gpu
```

### 2. Start Services with GPU Support
```powershell
# Stop CPU version first
docker compose down

# Start GPU version
docker compose -f docker-compose.gpu.yml up -d
```

### 3. Verify GPU Detection
```powershell
# Check GPU in container
docker exec dagster-gpu nvidia-smi

# Check Python GPU detection
docker exec dagster-gpu python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

## What Gets Accelerated

### ✅ GPU-Accelerated Components
1. **LightGBM Training** - Automatically uses GPU via `device='gpu'`
2. **SentenceTransformer Embeddings** - PyTorch CUDA acceleration
3. **Feature Engineering** - Embedding computation on GPU

### ❌ CPU-Only Components
- Logistic Regression (sklearn)
- SVM (sklearn)
- TF-IDF & SVD (sklearn)
- Spark transformations

## Performance Comparison

### Typical Speedup (depends on dataset size and GPU):
- **LightGBM Training**: 5-10x faster
- **SentenceTransformer**: 3-5x faster
- **Overall Pipeline**: 2-3x faster (limited by CPU-only components)

## Troubleshooting

### GPU not detected
```bash
# Verify NVIDIA runtime
docker info | grep -i runtime

# Check GPU allocation
docker run --rm --gpus all ubuntu nvidia-smi
```

### Out of Memory
```yaml
# Reduce batch size in docker-compose.gpu.yml
environment:
  - CUDA_VISIBLE_DEVICES=0  # Use only first GPU
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### LightGBM GPU build fails
```dockerfile
# Alternative installation in Dockerfile.dagster.gpu:
RUN pip install lightgbm --config-settings=cmake.define.USE_GPU=ON
```

## Switching Back to CPU

```powershell
# Stop GPU version
docker compose -f docker-compose.gpu.yml down

# Start CPU version
docker compose up -d
```

## Cost Considerations

- **Development**: Use CPU version (docker-compose.yml)
- **Training**: Use GPU version (docker-compose.gpu.yml)
- **Production Inference**: CPU version is usually sufficient

## Notes

- GPU Docker support requires Docker Desktop with WSL2 backend on Windows
- Linux users can skip WSL2 and install nvidia-docker directly
- MacOS does not support NVIDIA GPUs in Docker
- First GPU build takes ~10-15 minutes due to CUDA libraries
