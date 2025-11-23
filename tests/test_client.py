import pytest
import os
import tempfile
from unittest.mock import patch, Mock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import upload_image, get_image_by_index, list_images, get_image_by_filename


class TestClientFunctions:
    """Test cases for client.py functions"""
    
    @patch('client.requests.post')
    def test_upload_image_success(self, mock_post):
        """Test successful image upload via client"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'filename': 'test.jpg'}
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'fake image data')
            tmp_path = tmp.name
        
        try:
            result = upload_image(tmp_path)
            assert result == 'test.jpg'
            mock_post.assert_called_once()
        finally:
            os.unlink(tmp_path)
    
    @patch('client.requests.post')
    def test_upload_image_failure(self, mock_post):
        """Test failed image upload via client"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'fake image data')
            tmp_path = tmp.name
        
        try:
            result = upload_image(tmp_path)
            assert result is None
        finally:
            os.unlink(tmp_path)
    
    @patch('client.requests.post')
    def test_upload_image_file_not_found(self, mock_post):
        """Test upload with non-existent file"""
        result = upload_image('nonexistent.jpg')
        assert result is None
        mock_post.assert_not_called()
    
    @patch('client.requests.post')
    @patch('client.mimetypes.guess_type')
    def test_upload_image_no_mime_type(self, mock_guess_type, mock_post):
        """Test upload with file that has no MIME type (defaults to image/jpeg)"""
        mock_guess_type.return_value = (None, None)  # No MIME type found
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'filename': 'test.unknown'}
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.unknown') as tmp:
            tmp.write(b'fake image data')
            tmp_path = tmp.name
        
        try:
            result = upload_image(tmp_path)
            assert result == 'test.unknown'
            # Verify that image/jpeg was used as default MIME type
            call_args = mock_post.call_args
            files_arg = call_args[1]['files']
            assert files_arg['file'][2] == 'image/jpeg'
        finally:
            os.unlink(tmp_path)
    
    @patch('client.requests.get')
    def test_list_images_success(self, mock_get):
        """Test successful image listing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'images': ['img1.jpg', 'img2.png']}
        mock_get.return_value = mock_response
        
        result = list_images()
        assert result == ['img1.jpg', 'img2.png']
        mock_get.assert_called_once()
    
    @patch('client.requests.get')
    def test_list_images_empty(self, mock_get):
        """Test listing images when server has none"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = list_images()
        assert result == []
    
    @patch('client.requests.get')
    def test_list_images_full_format(self, mock_get):
        """Test listing images with full format (simple=False)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'images': [
                {'filename': 'img1.jpg', 'path': '2024-01-01/flight_1/img1.jpg'},
                {'filename': 'img2.png', 'path': '2024-01-01/flight_1/img2.png'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = list_images(simple=False)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert 'filename' in result[0]
        # Verify params were passed correctly
        call_args = mock_get.call_args
        assert call_args[1]['params']['simple'] == 'false'
    
    @patch('client.requests.get')
    def test_get_image_by_filename_success(self, mock_get):
        """Test successful image download by filename"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'fake image data'
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            save_path = tmp.name
        
        try:
            result = get_image_by_filename('test.jpg', save_path)
            assert result == save_path
            assert os.path.exists(save_path)
            with open(save_path, 'rb') as f:
                assert f.read() == b'fake image data'
        finally:
            if os.path.exists(save_path):
                os.unlink(save_path)
    
    @patch('client.requests.get')
    def test_get_image_by_filename_no_save_path(self, mock_get):
        """Test image download without specifying save_path (uses default)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'fake image data'
        mock_get.return_value = mock_response
        
        try:
            result = get_image_by_filename('test.jpg')
            assert result == 'downloaded_test.jpg'
            assert os.path.exists('downloaded_test.jpg')
            with open('downloaded_test.jpg', 'rb') as f:
                assert f.read() == b'fake image data'
        finally:
            if os.path.exists('downloaded_test.jpg'):
                os.unlink('downloaded_test.jpg')
    
    @patch('client.requests.get')
    def test_get_image_by_filename_not_found(self, mock_get):
        """Test image download when image is not found (404)"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = get_image_by_filename('nonexistent.jpg')
        assert result is None
    
    @patch('client.get_image_by_filename')
    @patch('client.list_images')
    def test_get_image_by_index_success(self, mock_list, mock_get_file):
        """Test getting image by index"""
        mock_list.return_value = ['img1.jpg', 'img2.png', 'img3.jpg']
        mock_get_file.return_value = 'downloaded_img2.png'
        
        result = get_image_by_index(1)
        assert result == 'downloaded_img2.png'
        mock_list.assert_called_once()
        mock_get_file.assert_called_once_with('img2.png')
    
    @patch('client.get_image_by_filename')
    @patch('client.list_images')
    def test_get_image_by_index_dict_format(self, mock_list, mock_get_file):
        """Test getting image by index when list_images returns dict format"""
        mock_list.return_value = [
            {'filename': 'img1.jpg', 'path': '2024-01-01/flight_1/img1.jpg'},
            {'filename': 'img2.png', 'path': '2024-01-01/flight_1/img2.png'}
        ]
        mock_get_file.return_value = 'downloaded_img2.png'
        
        result = get_image_by_index(1)
        assert result == 'downloaded_img2.png'
        mock_get_file.assert_called_once_with('img2.png')
    
    @patch('client.list_images')
    def test_get_image_by_index_empty_list(self, mock_list):
        """Test getting image by index when no images are available"""
        mock_list.return_value = []
        
        result = get_image_by_index(0)
        assert result is None
    
    @patch('client.list_images')
    def test_get_image_by_index_out_of_range(self, mock_list):
        """Test getting image with invalid index"""
        mock_list.return_value = ['img1.jpg', 'img2.png']
        
        result = get_image_by_index(5)
        assert result is None
        
        result = get_image_by_index(-1)
        assert result is None

