# Post-FX Pipeline

Order: Interpolate (RIFE) → Upscale (Real-ESRGAN or Topaz)

Inputs: mp4 (h264/aac), target_fps ∈ {24,30}
Outputs: normalized mp4, same AR, padded 300ms tail

CLI guidance:
- rife-ncnn-vulkan -i in.mp4 -o rife.mp4 -f {fps}
- realesrgan-ncnn-vulkan -i rife.mp4 -o up.mp4 -s 4 -n general-x4v3

CPU fallback: use slower PyTorch RIFE; log warning
