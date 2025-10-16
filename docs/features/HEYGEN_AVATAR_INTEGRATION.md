# Heygen Photo Avatar Integration

This enhancement adds support for Heygen's Photo Avatar functionality to the Option 2 workflow in the application.

## Features Added

- **Video Mode Toggle**: Users can now choose between "Talking Photo" (original) and "Photo Avatar" (new) modes
- **Avatar Management**: Create and select avatars for video generation
- **Avatar-Based Video Creation**: Generate more dynamic videos using facial animation technology
- **Action Prompt Support**: Add movement instructions to avatars for enhanced videos

## Implementation Details

### Backend Changes

- **HeygenAdapter**: Enhanced with avatar-specific methods (create_avatar, list_avatars, generate_avatar_video)
- **Avatar API Routes**: New routes for avatar management (create, list, get)
- **Job Schema**: Updated to support avatar configuration
- **Orchestrator**: Modified to handle avatar-based video generation

### Frontend Changes

- **AvatarSelector Component**: New component for browsing and creating avatars
- **Option2Form**: Updated to support both talking photo and avatar modes
- **Avatar API Client**: New frontend client for interacting with avatar endpoints
- **Job Types**: Updated to include avatar configuration

## Usage

1. Navigate to the Option 2 workflow in the Composer
2. Toggle between "Talking Photo" and "Photo Avatar" modes
3. When in Avatar mode:
   - Select an existing avatar or create a new one
   - Provide face images when creating a new avatar
   - Add an action prompt for enhanced movement
4. Complete the form with audio settings (upload or TTS)
5. Submit to create a new avatar-based video job

## Testing

- Use the `/test-avatar-api` route to verify avatar API connectivity
- Check avatar creation, listing, and selection functionality
- Verify job creation with avatar configuration
- Monitor job processing for avatar-based video generation

## Technical Notes

- Avatar creation requires clear face images for best results
- Action prompts enhance the avatar's movements and expressions
- Avatar videos support the same post-processing options as talking photos