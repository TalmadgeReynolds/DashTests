# Storage Presign Policy

Accept:
- image: image/jpeg,image/png (≤ 10MB)
- audio: audio/mpeg,audio/wav (≤ 20MB)
Key format: {kind}/{sha256}-{ts}.{ext}
Response: { uploadUrl, fileUrl } (PUT presign; public GET fileUrl)
