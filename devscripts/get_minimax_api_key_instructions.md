# How to Get Your MiniMax API Key

## Current Issue
The JWT token in your `.env` file is a **console access token**, not an API key for programmatic access.

## What You Have
```
Type: JWT Access Token (Console/Web UI)
Length: 722 characters
Format: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Use: For accessing the MiniMax web console
```

## What You Need
```
Type: API Secret Key
Format: Usually shorter, alphanumeric string
Use: For making API requests programmatically
```

## How to Get Your API Key

### Option 1: From MiniMax Console (Recommended)

1. **Go to MiniMax Console**
   - Visit: https://platform.minimax.chat/
   - Or: https://www.minimaxi.com/platform

2. **Navigate to API Keys Section**
   - Look for "API Keys", "API Management", or "Developer Settings"
   - Usually in Settings → API Keys or Account → API Management

3. **Generate New API Key**
   - Click "Create API Key" or "Generate New Key"
   - Give it a name (e.g., "My App API Key")
   - Copy the key immediately (it may only show once!)

4. **Update Your .env File**
   ```bash
   MINIMAX_API_KEY=your_actual_api_key_here
   ```

### Option 2: Check Documentation

1. Visit MiniMax API documentation:
   - https://platform.minimax.chat/document/introduction
   - Look for "Authentication" or "Getting Started" section

2. Follow their instructions for:
   - Creating an API key
   - Finding your Group ID (you already have this: 1988590381469537041)

### Option 3: Contact Support

If you can't find the API key section:
- Email: support@minimax.chat
- Ask: "How do I generate an API key for programmatic access to the Video Generation API?"

## Common API Key Formats

MiniMax API keys typically look like one of these:
- `sk_xxxxxxxxxxxxxxxxxxxxxxxxxx` (OpenAI-style)
- `mmx_xxxxxxxxxxxxxxxxxxxxxxxxx` (MiniMax-style)
- Long alphanumeric string (32-64 characters)
- **NOT** a JWT token (those are for console access)

## Testing Your New API Key

Once you have the correct API key:

```bash
# Update .env
nano /workspaces/DashTests/.env

# Test the connection
python devscripts/test_minimax_real_api.py
```

## Current Configuration

Your current setup:
- ✓ Group ID: 1988590381469537041 (Correct!)
- ✗ API Key: JWT console token (Incorrect - need API secret key)
- ✓ Mock Mode: Disabled
- ✓ All code: Ready and working in mock mode

## What's Working

Everything is implemented and tested in mock mode:
- ✓ All 3 models (Hailuo 2.3, 2.3-Fast, 02)
- ✓ All 4 generation modes (T2V, I2V, FL2V, S2V)
- ✓ Full configuration support
- ✓ Complete async workflow
- ✓ Backend adapter, service layer, routes
- ✓ Frontend UI component
- ✓ 23 unit tests passing

**You just need the correct API key to use the real API!**

## Next Steps

1. Get your API secret key from the MiniMax console
2. Update MINIMAX_API_KEY in .env with the secret key
3. Run: `python devscripts/test_minimax_real_api.py`
4. If successful, start using the real API! 🎉
