import os
import json
import subprocess
import pytest
from unittest import mock
from pathlib import Path

from backend.utils.ffmpeg import (
    check_ffmpeg_installed,
    get_video_info,
    add_padding_to_video,
    normalize_video,
    get_temp_file,
    process_and_upload_video
)
from backend.exceptions import PostFxError
from backend.schemas.common import PresignKind


class TestFFmpegUtilsAdvanced:
    """Advanced tests for FFmpeg utility functions"""
    
    @pytest.fixture
    def mock_ffmpeg_check(self):
        """Mock FFmpeg check to always return True"""
        with mock.patch('backend.utils.ffmpeg.check_ffmpeg_installed', return_value=True):
            yield
            
    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess for ffmpeg commands"""
        with mock.patch('backend.utils.ffmpeg.subprocess.run') as mock_run:
            # Configure the mock to return a success result
            mock_run.return_value = mock.MagicMock(
                returncode=0,
                stdout='{"dummy": "output"}',
                stderr=''
            )
            yield mock_run
    
    def test_check_ffmpeg_installed_success(self):
        """Test check_ffmpeg_installed when FFmpeg is available"""
        with mock.patch('backend.utils.ffmpeg.subprocess.run') as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            result = check_ffmpeg_installed()
            assert result is True
            mock_run.assert_called_once()
    
    def test_check_ffmpeg_installed_failure(self):
        """Test check_ffmpeg_installed when FFmpeg is not available"""
        with mock.patch('backend.utils.ffmpeg.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = check_ffmpeg_installed()
            assert result is False
            mock_run.assert_called_once()
    
    def test_get_video_info_success(self, tmp_path):
        """Test get_video_info success case"""
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Sample ffprobe output
        sample_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1280,
                    "height": 720,
                    "r_frame_rate": "24/1"
                },
                {
                    "codec_type": "audio",
                    "sample_rate": "44100"
                }
            ],
            "format": {
                "duration": "60.042",
                "size": "24000000"
            }
        }
        
        with mock.patch('backend.utils.ffmpeg.subprocess.run') as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=0,
                stdout=json.dumps(sample_output),
                stderr=""
            )
            
            result = get_video_info(video_path)
            
            assert result == sample_output
            mock_run.assert_called_once()
            cmd_args = mock_run.call_args[0][0]
            assert "ffprobe" in cmd_args
            assert video_path in cmd_args
    
    def test_get_video_info_failure(self, tmp_path):
        """Test get_video_info failure case"""
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        with mock.patch('backend.utils.ffmpeg.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("Command failed")
            
            with pytest.raises(RuntimeError) as excinfo:
                get_video_info(video_path)
            
            assert "Failed to get video info" in str(excinfo.value)
    
    def test_process_and_upload_video_error_handling(self, mock_ffmpeg_check, tmp_path):
        """Test error handling during video processing"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Mock the storage service
        with mock.patch('backend.services.storage.StorageService') as mock_service_class:
            mock_service = mock.MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock normalize_video to raise an exception
            with mock.patch('backend.utils.ffmpeg.normalize_video') as mock_normalize:
                mock_normalize.side_effect = RuntimeError("Normalization failed")
                
                # Mock get_temp_file
                with mock.patch('backend.utils.ffmpeg.get_temp_file', return_value=(str(tmp_path / "temp.mp4"), str(tmp_path))):
                    # Mock log_postfx_operation
                    with mock.patch('backend.utils.logging.log_postfx_operation'):
                        # Call should raise PostFxError
                        with pytest.raises(PostFxError) as excinfo:
                            process_and_upload_video(
                                video_path=video_path,
                                add_padding=False,
                                normalize=True
                            )
                        
                        assert "Failed to process video" in str(excinfo.value)
                        assert "Normalization failed" in str(excinfo.value)
    
    def test_process_and_upload_video_upload_failure(self, mock_ffmpeg_check, tmp_path):
        """Test handling upload failure during processing"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Mock the storage service to fail on upload
        with mock.patch('backend.services.storage.StorageService') as mock_service_class:
            mock_service = mock.MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.upload_file.side_effect = Exception("Upload failed")
            
            # Mock get_temp_file
            with mock.patch('backend.utils.ffmpeg.get_temp_file', return_value=(str(tmp_path / "temp.mp4"), str(tmp_path))):
                # Mock log_postfx_operation
                with mock.patch('backend.utils.logging.log_postfx_operation'):
                    # Call should raise PostFxError
                    with pytest.raises(PostFxError) as excinfo:
                        process_and_upload_video(
                            video_path=video_path,
                            add_padding=False,
                            normalize=False
                        )
                        
                    assert "Failed to process video" in str(excinfo.value)
                    assert "Upload failed" in str(excinfo.value)
    
    def test_process_and_upload_video_with_job_id(self, mock_ffmpeg_check, mock_subprocess, tmp_path):
        """Test processing video with a job ID for logging"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        job_id = "test-job-123"
        
        # Mock storage service
        with mock.patch('backend.services.storage.StorageService') as mock_service_class:
            mock_service = mock.MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.upload_file.return_value = ("video/test-123456.mp4", "https://storage.example.com/video/test-123456.mp4")
            
            # Mock logging function
            with mock.patch('backend.utils.logging.log_postfx_operation') as mock_log:
                # Call the function
                key, url = process_and_upload_video(
                    video_path=video_path,
                    add_padding=False,
                    normalize=False,
                    job_id=job_id
                )
                
                # Check logs were called with job_id
                for call in mock_log.call_args_list:
                    _, kwargs = call
                    assert kwargs.get("job_id") == job_id
                
                # Check final log contains success=True
                final_call = mock_log.call_args_list[-1]
                _, kwargs = final_call
                assert kwargs.get("success") is True
                assert kwargs.get("operation") == "process_video"