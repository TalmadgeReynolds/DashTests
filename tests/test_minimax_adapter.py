"""
Tests for MiniMax Hailuo adapter

Tests all generation modes, task polling, and error handling
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from backend.adapters.minimax_adapter import (
    MinimaxAdapter,
    MinimaxModel,
    TaskStatus,
    GenerationMode
)
from backend.exceptions import ProviderError, ProviderTimeoutError


@pytest.fixture
def minimax_adapter():
    """Create MiniMax adapter in mock mode"""
    return MinimaxAdapter(mock_mode=True)


@pytest.fixture
def minimax_adapter_real():
    """Create MiniMax adapter with mock API (not mock mode)"""
    return MinimaxAdapter(
        api_key="test-api-key",
        group_id="test-group",
        mock_mode=False
    )


class TestMinimaxAdapterMockMode:
    """Test MiniMax adapter in mock mode"""
    
    @pytest.mark.asyncio
    async def test_text_to_video_mock(self, minimax_adapter):
        """Test T2V generation in mock mode"""
        task_id = await minimax_adapter.text_to_video(
            prompt="A dog running in a field",
            model=MinimaxModel.HAILUO_2_3
        )
        
        assert task_id.startswith("mock-minimax-t2v-")
        assert len(task_id) > 10
    
    @pytest.mark.asyncio
    async def test_image_to_video_mock(self, minimax_adapter):
        """Test I2V generation in mock mode"""
        task_id = await minimax_adapter.image_to_video(
            prompt="The person smiles and waves",
            first_frame_image=b"fake_image_data",
            model=MinimaxModel.HAILUO_2_3_FAST
        )
        
        assert task_id.startswith("mock-minimax-i2v-")
    
    @pytest.mark.asyncio
    async def test_first_last_frame_mock(self, minimax_adapter):
        """Test FL2V generation in mock mode"""
        task_id = await minimax_adapter.first_last_frame_to_video(
            prompt="Smooth transition between frames",
            first_frame_image=b"first_frame",
            last_frame_image=b"last_frame"
        )
        
        assert task_id.startswith("mock-minimax-fl2v-")
    
    @pytest.mark.asyncio
    async def test_subject_reference_mock(self, minimax_adapter):
        """Test S2V generation in mock mode"""
        task_id = await minimax_adapter.subject_reference_to_video(
            prompt="Character walks forward",
            reference_image=b"reference",
            reference_type="character"
        )
        
        assert task_id.startswith("mock-minimax-s2v-")
    
    @pytest.mark.asyncio
    async def test_query_status_mock(self, minimax_adapter):
        """Test status query in mock mode"""
        task_id = "mock-minimax-t2v-1234"
        
        status = await minimax_adapter.query_task_status(task_id)
        
        assert status["task_id"] == task_id
        assert status["status"] == TaskStatus.SUCCESS.value
        assert "file_id" in status
    
    @pytest.mark.asyncio
    async def test_download_video_mock(self, minimax_adapter):
        """Test video download in mock mode"""
        file_id = "mock-file-1234"
        
        video_bytes = await minimax_adapter.download_video(file_id)
        
        assert isinstance(video_bytes, bytes)
        assert len(video_bytes) > 0


class TestMinimaxAdapterParameters:
    """Test parameter validation and configuration"""
    
    @pytest.mark.asyncio
    async def test_all_models_supported(self, minimax_adapter):
        """Test all model types"""
        models = [
            MinimaxModel.HAILUO_2_3,
            MinimaxModel.HAILUO_2_3_FAST,
            MinimaxModel.HAILUO_02
        ]
        
        for model in models:
            task_id = await minimax_adapter.text_to_video(
                prompt="Test video",
                model=model
            )
            assert task_id is not None
    
    @pytest.mark.asyncio
    async def test_aspect_ratios(self, minimax_adapter):
        """Test different aspect ratios"""
        aspect_ratios = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"]
        
        for ratio in aspect_ratios:
            task_id = await minimax_adapter.text_to_video(
                prompt="Test video",
                aspect_ratio=ratio
            )
            assert task_id is not None
    
    @pytest.mark.asyncio
    async def test_duration_range(self, minimax_adapter):
        """Test different video durations"""
        for duration in [2, 4, 6, 8, 10]:
            task_id = await minimax_adapter.text_to_video(
                prompt="Test video",
                duration_seconds=duration,
                model=MinimaxModel.HAILUO_02  # Supports up to 10s
            )
            assert task_id is not None
    
    @pytest.mark.asyncio
    async def test_seed_parameter(self, minimax_adapter):
        """Test seed for reproducibility"""
        task_id = await minimax_adapter.text_to_video(
            prompt="Test video",
            seed=42
        )
        assert task_id is not None
    
    @pytest.mark.asyncio
    async def test_prompt_optimizer(self, minimax_adapter):
        """Test prompt optimizer setting"""
        # Test with optimizer enabled
        task_id1 = await minimax_adapter.text_to_video(
            prompt="Test video",
            prompt_optimizer=True
        )
        assert task_id1 is not None
        
        # Test with optimizer disabled
        task_id2 = await minimax_adapter.text_to_video(
            prompt="Test video",
            prompt_optimizer=False
        )
        assert task_id2 is not None


class TestMinimaxAdapterPolling:
    """Test polling functionality"""
    
    @pytest.mark.asyncio
    async def test_poll_until_complete_success(self, minimax_adapter):
        """Test successful polling until completion"""
        task_id = await minimax_adapter.text_to_video(
            prompt="Test video"
        )
        
        result = await minimax_adapter.poll_until_complete(
            task_id=task_id,
            max_wait_seconds=10,
            poll_interval=1
        )
        
        assert result["status"] == TaskStatus.SUCCESS.value
        assert "file_id" in result
    
    @pytest.mark.asyncio
    async def test_poll_timeout(self, minimax_adapter_real):
        """Test polling timeout"""
        # Mock the query_task_status to always return processing
        with patch.object(
            minimax_adapter_real,
            'query_task_status',
            return_value={"status": TaskStatus.PROCESSING.value, "progress": 50}
        ):
            with pytest.raises(ProviderTimeoutError):
                await minimax_adapter_real.poll_until_complete(
                    task_id="test-task",
                    max_wait_seconds=2,
                    poll_interval=1
                )


class TestMinimaxAdapterImageEncoding:
    """Test image encoding functionality"""
    
    def test_encode_bytes(self, minimax_adapter):
        """Test encoding bytes to base64"""
        image_bytes = b"fake_image_data"
        encoded = minimax_adapter._encode_image(image_bytes)
        
        assert isinstance(encoded, str)
        assert len(encoded) > 0
    
    def test_encode_string(self, minimax_adapter):
        """Test handling of string input"""
        # Already base64
        base64_str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        encoded = minimax_adapter._encode_image(base64_str)
        
        assert encoded == base64_str


class TestMinimaxAdapterErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_prompt(self, minimax_adapter):
        """Test handling of empty prompt"""
        # Should still work in mock mode
        task_id = await minimax_adapter.text_to_video(
            prompt=""
        )
        assert task_id is not None
    
    @pytest.mark.asyncio
    async def test_invalid_file_id(self, minimax_adapter):
        """Test download with invalid file ID"""
        # In mock mode, should still return data
        video_bytes = await minimax_adapter.download_video("invalid-file-id")
        assert isinstance(video_bytes, bytes)
    
    @pytest.mark.asyncio
    async def test_headers_generation(self, minimax_adapter_real):
        """Test request headers generation"""
        headers = minimax_adapter_real._build_headers()
        
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]
        assert "GroupId" in headers


class TestMinimaxAdapterIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_t2v_workflow(self, minimax_adapter):
        """Test complete T2V workflow: create -> poll -> download"""
        # Create task
        task_id = await minimax_adapter.text_to_video(
            prompt="A beautiful sunset over mountains",
            model=MinimaxModel.HAILUO_2_3,
            aspect_ratio="16:9",
            duration_seconds=6
        )
        assert task_id is not None
        
        # Query status
        status = await minimax_adapter.query_task_status(task_id)
        assert status["status"] == TaskStatus.SUCCESS.value
        
        # Download video
        file_id = status["file_id"]
        video_bytes = await minimax_adapter.download_video(file_id)
        assert len(video_bytes) > 0
    
    @pytest.mark.asyncio
    async def test_complete_i2v_workflow(self, minimax_adapter):
        """Test complete I2V workflow"""
        # Create task
        task_id = await minimax_adapter.image_to_video(
            prompt="The person smiles",
            first_frame_image=b"fake_image",
            model=MinimaxModel.HAILUO_2_3_FAST
        )
        assert task_id is not None
        
        # Poll until complete
        result = await minimax_adapter.poll_until_complete(task_id, max_wait_seconds=10)
        assert result["status"] == TaskStatus.SUCCESS.value
        
        # Download
        video_bytes = await minimax_adapter.download_video(result["file_id"])
        assert len(video_bytes) > 0


class TestMinimaxModels:
    """Test model enum and capabilities"""
    
    def test_model_values(self):
        """Test model enum values"""
        assert MinimaxModel.HAILUO_2_3.value == "MiniMax-Hailuo-2.3"
        assert MinimaxModel.HAILUO_2_3_FAST.value == "MiniMax-Hailuo-2.3-Fast"
        assert MinimaxModel.HAILUO_02.value == "MiniMax-Hailuo-02"
    
    def test_task_status_values(self):
        """Test task status enum values"""
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
    
    def test_generation_mode_values(self):
        """Test generation mode enum values"""
        assert GenerationMode.TEXT_TO_VIDEO.value == "t2v"
        assert GenerationMode.IMAGE_TO_VIDEO.value == "i2v"
        assert GenerationMode.FIRST_LAST_TO_VIDEO.value == "fl2v"
        assert GenerationMode.SUBJECT_REFERENCE.value == "s2v"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
