import os
import pytest
from unittest import mock
from pathlib import Path

from backend.exceptions import PostFxError
from backend.utils.ffmpeg import (
    check_ffmpeg_installed,
    get_video_info,
    add_padding_to_video,
    normalize_video,
    get_temp_file,
    process_and_upload_video
)


@pytest.fixture
def mock_ffmpeg_check():
    """Mock FFmpeg check to always return True"""
    with mock.patch('backend.utils.ffmpeg.check_ffmpeg_installed', return_value=True):
        yield


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for ffmpeg commands"""
    with mock.patch('backend.utils.ffmpeg.subprocess.run') as mock_run:
        # Configure the mock to return a success result
        mock_run.return_value = mock.MagicMock(
            returncode=0,
            stdout='{"dummy": "output"}',
            stderr=''
        )
        yield mock_run


@pytest.fixture
def mock_storage_service():
    """Mock StorageService for testing upload"""
    with mock.patch('backend.services.storage.StorageService') as mock_service_class:
        mock_service = mock.MagicMock()
        mock_service_class.return_value = mock_service
        
        # Configure upload_file to return a predictable result
        mock_service.upload_file.return_value = ("video/test-123456.mp4", "https://storage.example.com/video/test-123456.mp4")
        
        yield mock_service


class TestFFmpegUtils:
    """Test suite for FFmpeg utility functions"""
    
    def test_process_and_upload_video_no_processing(self, mock_ffmpeg_check, mock_subprocess, mock_storage_service, tmp_path):
        """Test processing and uploading video without any processing steps"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Call the function with processing disabled
        key, url = process_and_upload_video(
            video_path=video_path,
            add_padding=False,
            normalize=False
        )
        
        # Check that ffmpeg commands were not called
        mock_subprocess.assert_not_called()
        
        # Check that file was uploaded directly
        mock_storage_service.upload_file.assert_called_once()
        args, kwargs = mock_storage_service.upload_file.call_args
        assert kwargs["file_path"] == video_path
        
        # Check returned values
        assert key == "video/test-123456.mp4"
        assert url == "https://storage.example.com/video/test-123456.mp4"
    
    def test_process_and_upload_video_with_padding(self, mock_ffmpeg_check, mock_subprocess, mock_storage_service, tmp_path):
        """Test processing and uploading video with padding"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Mock get_temp_file to return predictable paths
        temp_paths = [str(tmp_path / "temp1.mp4"), str(tmp_path / "temp2.mp4")]
        
        with mock.patch('backend.utils.ffmpeg.get_temp_file', side_effect=[(p, os.path.dirname(p)) for p in temp_paths]):
            # Call the function with only padding
            key, url = process_and_upload_video(
                video_path=video_path,
                add_padding=True,
                normalize=False
            )
            
            # Check that padding command was called
            mock_subprocess.assert_called_once()
            cmd_args = mock_subprocess.call_args[0][0]
            assert "tpad=stop_duration=" in " ".join(cmd_args)
            
            # Check that file was uploaded
            mock_storage_service.upload_file.assert_called_once()
            
            # Check returned values
            assert key == "video/test-123456.mp4"
            assert url == "https://storage.example.com/video/test-123456.mp4"
    
    def test_process_and_upload_video_with_normalization(self, mock_ffmpeg_check, mock_subprocess, mock_storage_service, tmp_path):
        """Test processing and uploading video with normalization"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Mock get_temp_file to return predictable paths
        with mock.patch('backend.utils.ffmpeg.get_temp_file', return_value=(str(tmp_path / "temp.mp4"), str(tmp_path))):
            # Call the function with only normalization
            key, url = process_and_upload_video(
                video_path=video_path,
                add_padding=False,
                normalize=True
            )
            
            # Check that normalization command was called
            mock_subprocess.assert_called_once()
            cmd_args = mock_subprocess.call_args[0][0]
            assert "libx264" in cmd_args
            
            # Check that file was uploaded
            mock_storage_service.upload_file.assert_called_once()
            
            # Check returned values
            assert key == "video/test-123456.mp4"
            assert url == "https://storage.example.com/video/test-123456.mp4"
    
    def test_process_and_upload_video_with_both(self, mock_ffmpeg_check, mock_subprocess, mock_storage_service, tmp_path):
        """Test processing and uploading video with both padding and normalization"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Mock get_temp_file to return predictable paths
        temp_paths = [str(tmp_path / "temp1.mp4"), str(tmp_path / "temp2.mp4")]
        
        with mock.patch('backend.utils.ffmpeg.get_temp_file', side_effect=[(p, os.path.dirname(p)) for p in temp_paths]):
            # Call the function with both processing steps
            key, url = process_and_upload_video(
                video_path=video_path,
                add_padding=True,
                normalize=True
            )
            
            # Check that both commands were called
            assert mock_subprocess.call_count == 2
            
            # First call should be padding
            first_cmd_args = mock_subprocess.call_args_list[0][0][0]
            assert "tpad=stop_duration=" in " ".join(first_cmd_args)
            
            # Second call should be normalization
            second_cmd_args = mock_subprocess.call_args_list[1][0][0]
            assert "libx264" in second_cmd_args
            
            # Check that file was uploaded
            mock_storage_service.upload_file.assert_called_once()
            
            # Check returned values
            assert key == "video/test-123456.mp4"
            assert url == "https://storage.example.com/video/test-123456.mp4"
    
    def test_process_and_upload_video_ffmpeg_not_available(self, tmp_path):
        """Test handling when FFmpeg is not available"""
        # Create a test video file
        test_video = tmp_path / "input.mp4"
        test_video.write_bytes(b"test video content")
        video_path = str(test_video)
        
        # Mock FFmpeg check to return False
        with mock.patch('backend.utils.ffmpeg.check_ffmpeg_installed', return_value=False):
            # Call should raise PostFxError
            with pytest.raises(PostFxError) as excinfo:
                process_and_upload_video(video_path)
                
            assert "FFmpeg is not available" in str(excinfo.value)