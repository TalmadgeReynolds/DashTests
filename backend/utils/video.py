"""Video utilities for handling video file operations."""
import subprocess
import json
from typing import Dict, Any
import asyncio

async def get_video_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get video file metadata using FFmpeg.
    Returns size, duration, frame count, and other essential metadata.
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'format=duration,size,format_name:stream=width,height,r_frame_rate,nb_frames',
        '-show_streams',
        '-of', 'json',
        file_path
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise ValueError(f"FFprobe error: {stderr.decode()}")

        data = json.loads(stdout.decode())
        
        # Get main metadata fields
        stream = data['streams'][0]
        format_data = data['format']
        
        # Detect container format
        format_name = format_data.get('format_name', '').lower()
        container = 'mov' if 'mov' in format_name or 'quicktime' in format_name else 'mp4'
        
        # Calculate frame rate from rational string
        num, den = map(int, stream['r_frame_rate'].split('/'))
        frame_rate = num / den

        # Get or calculate frame count
        nb_frames = stream.get('nb_frames')
        if nb_frames is None or nb_frames == 'N/A':
            # If frame count not available, calculate from duration and frame rate
            duration = float(format_data['duration'])
            nb_frames = int(duration * frame_rate)

        return {
            "size": int(format_data['size']),
            "duration": float(format_data['duration']),
            "width": int(stream['width']),
            "height": int(stream['height']),
            "frameRate": frame_rate,
            "frameCount": nb_frames,
            "container": container
        }
    except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Error getting video metadata: {str(e)}")