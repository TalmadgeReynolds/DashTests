# cURL Examples

POST /lipsync/prompt
curl -sS -X POST http://localhost:8000/api/v1/lipsync/prompt -H 'Content-Type: application/json' -d '{"script":"We shipped it!","post":{"interpolate":true,"upscale":false}}'

POST /lipsync/audio
curl -sS -X POST http://localhost:8000/api/v1/lipsync/audio -H 'Content-Type: application/json' -d '{"image_url":"https://.../face.jpg","tts":{"provider":"elevenlabs","text":"Hello world"}}'

POST /uploads/presign
curl -sS -X POST http://localhost:8000/api/v1/uploads/presign -H 'Content-Type: application/json' -d '{"filename":"face.jpg","mime":"image/jpeg","kind":"IMAGE"}'
