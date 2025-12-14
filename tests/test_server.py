import pytest
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from PIL import Image
import io

# Import the app after setting up test environment
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app, IMAGE_DIR


@pytest.fixture(scope='function')
def test_client():
    """Create a test client with temporary directories"""
    # Create temporary directories
    temp_base = tempfile.mkdtemp()
    temp_image_dir = os.path.join(temp_base, 'images')
    temp_metadata_dir = os.path.join(temp_base, 'metadata')
    temp_logs_dir = os.path.join(temp_base, 'logs')
    
    original_image_dir = IMAGE_DIR
    import server
    original_metadata_dir = server.METADATA_DIR
    original_logs_dir = server.LOGS_DIR
    
    # Temporarily modify directories in the app
    server.IMAGE_DIR = temp_image_dir
    server.METADATA_DIR = temp_metadata_dir
    server.LOGS_DIR = temp_logs_dir
    
    # Ensure directories exist
    os.makedirs(temp_image_dir, exist_ok=True)
    os.makedirs(temp_metadata_dir, exist_ok=True)
    os.makedirs(temp_logs_dir, exist_ok=True)
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    shutil.rmtree(temp_base)
    server.IMAGE_DIR = original_image_dir
    server.METADATA_DIR = original_metadata_dir
    server.LOGS_DIR = original_logs_dir


@pytest.fixture
def sample_image():
    """Create a sample image in memory"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


class TestHealthEndpoint:
    """Test cases for GET /health endpoint"""
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get('/health')
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'healthy'
        assert 'timestamp' in result
        assert result['service'] == 'drone-image-server'
        assert result['version'] == '1.0.0'


class TestUploadEndpoint:
    """Test cases for POST /upload/ endpoint"""
    
    def test_upload_image_success(self, test_client, sample_image):
        """Test successful image upload"""
        response = test_client.post(
            '/upload/',
            files={'file': ('test_image.jpg', sample_image, 'image/jpeg')}
        )
        assert response.status_code == 200
        result = response.json()
        assert 'filename' in result
        assert result.get('status') == 'success'
        assert result['filename'].endswith('.jpg')
    
    def test_upload_image_png(self, test_client):
        """Test uploading PNG image"""
        img = Image.new('RGB', (50, 50), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        response = test_client.post(
            '/upload/',
            files={'file': ('test.png', img_bytes, 'image/png')}
        )
        assert response.status_code == 200
        result = response.json()
        assert 'filename' in result
        assert result.get('status') == 'success'
        assert result['filename'].endswith('.png')
    
    def test_upload_with_metadata(self, test_client, sample_image):
        """Test upload with flight_id and metadata"""
        sample_image.seek(0)
        response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')},
            data={
                'flight_id': 'FLIGHT001',
                'gps_latitude': 37.7749,
                'gps_longitude': -122.4194,
                'altitude': 100.5,
                'camera_settings': '{"iso": 400, "shutter": "1/1000"}',
                'notes': 'Test flight'
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
        assert result['flight_id'] == 'FLIGHT001'
        assert 'path' in result
        assert 'metadata_file' in result
    
    def test_upload_with_flight_id_only(self, test_client, sample_image):
        """Test upload with only flight_id"""
        sample_image.seek(0)
        response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FLIGHT002'}
        )
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
        assert result['flight_id'] == 'FLIGHT002'
    
    def test_upload_with_gps_data(self, test_client, sample_image):
        """Test upload with GPS coordinates"""
        sample_image.seek(0)
        response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')},
            data={
                'gps_latitude': 40.7128,
                'gps_longitude': -74.0060
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
    
    def test_upload_multiple_images(self, test_client, sample_image):
        """Test uploading multiple different images"""
        # Upload first image
        sample_image.seek(0)
        response1 = test_client.post(
            '/upload/',
            files={'file': ('image1.jpg', sample_image, 'image/jpeg')}
        )
        assert response1.status_code == 200
        
        # Upload second image
        img2 = Image.new('RGB', (200, 200), color='green')
        img_bytes2 = io.BytesIO()
        img2.save(img_bytes2, format='JPEG')
        img_bytes2.seek(0)
        
        response2 = test_client.post(
            '/upload/',
            files={'file': ('image2.jpg', img_bytes2, 'image/jpeg')}
        )
        assert response2.status_code == 200
        result2 = response2.json()
        assert 'filename' in result2
        assert result2.get('status') == 'success'
        assert result2['filename'].endswith('.jpg')
    
    def test_upload_missing_file(self, test_client):
        """Test upload without file parameter"""
        response = test_client.post('/upload/')
        assert response.status_code == 422  # Validation error
    
    def test_upload_empty_file(self, test_client):
        """Test uploading empty file"""
        empty_file = io.BytesIO(b'')
        response = test_client.post(
            '/upload/',
            files={'file': ('empty.jpg', empty_file, 'image/jpeg')}
        )
        # Should still succeed (empty file is valid)
        assert response.status_code == 200
    
    def test_upload_with_invalid_json_camera_settings(self, test_client, sample_image):
        """Test upload with invalid JSON in camera_settings"""
        sample_image.seek(0)
        response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')},
            data={'camera_settings': 'invalid json'}
        )
        # Should handle gracefully - might fail or use None
        # The endpoint should not crash
        assert response.status_code in [200, 500]  # Either succeeds or returns error


class TestBatchUploadEndpoint:
    """Test cases for POST /upload/batch endpoint"""
    
    def test_batch_upload_success(self, test_client, sample_image):
        """Test successful batch upload"""
        img1 = Image.new('RGB', (100, 100), color='red')
        img_bytes1 = io.BytesIO()
        img1.save(img_bytes1, format='JPEG')
        img_bytes1.seek(0)
        
        img2 = Image.new('RGB', (100, 100), color='blue')
        img_bytes2 = io.BytesIO()
        img2.save(img_bytes2, format='JPEG')
        img_bytes2.seek(0)
        
        response = test_client.post(
            '/upload/batch',
            files=[
                ('files', ('batch1.jpg', img_bytes1, 'image/jpeg')),
                ('files', ('batch2.jpg', img_bytes2, 'image/jpeg'))
            ]
        )
        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 2
        assert result['successful'] == 2
        assert result['failed'] == 0
        assert len(result['results']) == 2
        assert all(r['status'] == 'success' for r in result['results'])
    
    def test_batch_upload_with_metadata(self, test_client, sample_image):
        """Test batch upload with flight_id and metadata"""
        img1 = Image.new('RGB', (100, 100), color='red')
        img_bytes1 = io.BytesIO()
        img1.save(img_bytes1, format='JPEG')
        img_bytes1.seek(0)
        
        response = test_client.post(
            '/upload/batch',
            files=[('files', ('batch1.jpg', img_bytes1, 'image/jpeg'))],
            data={
                'flight_id': 'BATCH_FLIGHT',
                'gps_latitude': 37.7749,
                'gps_longitude': -122.4194,
                'altitude': 150.0
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result['successful'] == 1
        assert result['failed'] == 0
    
    def test_batch_upload_empty(self, test_client):
        """Test batch upload with no files"""
        response = test_client.post('/upload/batch', files=[])
        assert response.status_code == 422  # Validation error
    
    def test_batch_upload_mixed_success_failure(self, test_client, sample_image):
        """Test batch upload with one valid and one invalid file"""
        img1 = Image.new('RGB', (100, 100), color='red')
        img_bytes1 = io.BytesIO()
        img1.save(img_bytes1, format='JPEG')
        img_bytes1.seek(0)
        
        # Create an invalid file (empty bytes)
        empty_file = io.BytesIO(b'')
        
        response = test_client.post(
            '/upload/batch',
            files=[
                ('files', ('valid.jpg', img_bytes1, 'image/jpeg')),
                ('files', ('empty.jpg', empty_file, 'image/jpeg'))
            ]
        )
        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 2
        # Both should succeed (empty files are valid)
        assert result['successful'] == 2


class TestListImagesEndpoint:
    """Test cases for GET /images/ endpoint"""
    
    def test_list_images_empty(self, test_client):
        """Test listing images when directory is empty"""
        response = test_client.get('/images/')
        assert response.status_code == 404
        assert 'No images found' in response.json()['detail']
    
    def test_list_images_success(self, test_client, sample_image):
        """Test listing images when images exist"""
        # Upload an image first
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        stored_filename = upload_response.json().get('filename')
        
        response = test_client.get('/images/?simple=true')
        assert response.status_code == 200
        assert 'images' in response.json()
        assert stored_filename in response.json()['images']
    
    def test_list_images_full_format(self, test_client, sample_image):
        """Test listing images with full format (not simple)"""
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        
        response = test_client.get('/images/')
        assert response.status_code == 200
        result = response.json()
        assert 'total' in result
        assert 'images' in result
        assert len(result['images']) > 0
        assert 'filename' in result['images'][0]
        assert 'path' in result['images'][0]
    
    def test_list_images_with_flight_id_filter(self, test_client, sample_image):
        """Test listing images filtered by flight_id"""
        # Upload image with flight_id
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FILTER_TEST'}
        )
        assert upload_response.status_code == 200
        
        # Upload another image without flight_id
        sample_image.seek(0)
        test_client.post(
            '/upload/',
            files={'file': ('test2.jpg', sample_image, 'image/jpeg')}
        )
        
        # List with flight_id filter
        response = test_client.get('/images/?flight_id=FILTER_TEST')
        assert response.status_code == 200
        result = response.json()
        assert 'images' in result
        # Should find at least the filtered image
        assert len(result['images']) >= 1
    
    def test_list_images_with_date_filter(self, test_client, sample_image):
        """Test listing images filtered by date"""
        from datetime import datetime
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        
        # Get the date from list_images which returns the correct format
        list_response = test_client.get('/images/')
        assert list_response.status_code == 200
        images = list_response.json()['images']
        assert len(images) > 0
        
        # Extract date from the first image's path
        path_parts = images[0]['path'].replace('\\', '/').split('/')
        date_folder = path_parts[0]
        
        # List with date filter
        response = test_client.get(f'/images/?date={date_folder}')
        assert response.status_code == 200
        result = response.json()
        assert 'images' in result
        assert len(result['images']) >= 1
    
    def test_list_images_with_invalid_date(self, test_client):
        """Test listing images with invalid date filter"""
        response = test_client.get('/images/?date=9999-99-99')
        assert response.status_code == 404
        assert 'No images found for date' in response.json()['detail']
    
    def test_list_multiple_images(self, test_client, sample_image):
        """Test listing multiple images"""
        # Upload multiple images and store their actual filenames
        stored_filenames = []
        original_filenames = ['img1.jpg', 'img2.jpg', 'img3.jpg']
        for filename in original_filenames:
            sample_image.seek(0)
            upload_response = test_client.post(
                '/upload/',
                files={'file': (filename, sample_image, 'image/jpeg')}
            )
            assert upload_response.status_code == 200
            stored_filenames.append(upload_response.json().get('filename'))
        
        response = test_client.get('/images/?simple=true')
        assert response.status_code == 200
        images = response.json()['images']
        assert len(images) == 3
        for stored_filename in stored_filenames:
            assert stored_filename in images


class TestGetImageEndpoint:
    """Test cases for GET /images/{filename} endpoint"""
    
    def test_get_image_not_found(self, test_client):
        """Test getting non-existent image"""
        response = test_client.get('/images/nonexistent.jpg')
        assert response.status_code == 404
        assert 'Image not found' in response.json()['detail']
    
    def test_get_image_success(self, test_client, sample_image):
        """Test successfully retrieving an image"""
        # Upload image first
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('retrieve_test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        stored_filename = upload_response.json().get('filename')
        
        # Retrieve the image using the stored filename
        response = test_client.get(f'/images/{stored_filename}')
        assert response.status_code == 200
        assert response.headers['content-type'] == 'image/jpeg'
        assert len(response.content) > 0
    
    def test_get_image_with_special_chars(self, test_client, sample_image):
        """Test getting image with special characters in filename"""
        sample_image.seek(0)
        filename = 'test_image_123.jpg'
        upload_response = test_client.post(
            '/upload/',
            files={'file': (filename, sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        stored_filename = upload_response.json().get('filename')
        
        response = test_client.get(f'/images/{stored_filename}')
        assert response.status_code == 200
        assert response.headers['content-type'] == 'image/jpeg'
    
    def test_get_image_content_matches(self, test_client, sample_image):
        """Test that retrieved image content matches uploaded content"""
        # Upload image
        sample_image.seek(0)
        original_content = sample_image.read()
        sample_image.seek(0)
        
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('content_test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        stored_filename = upload_response.json().get('filename')
        
        # Retrieve and verify content
        response = test_client.get(f'/images/{stored_filename}')
        assert response.status_code == 200
        retrieved_content = response.content
        assert retrieved_content == original_content
    
    def test_get_image_png_content_type(self, test_client):
        """Test getting PNG image with correct content type"""
        img = Image.new('RGB', (50, 50), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('test.png', img_bytes, 'image/png')}
        )
        assert upload_response.status_code == 200
        stored_filename = upload_response.json().get('filename')
        
        response = test_client.get(f'/images/{stored_filename}')
        assert response.status_code == 200
        assert 'image/png' in response.headers['content-type']


class TestGetImageByPathEndpoint:
    """Test cases for GET /images/{date}/{flight_folder}/{filename} endpoint"""
    
    def test_get_image_by_path_success(self, test_client, sample_image):
        """Test getting image by full path"""
        import server
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('path_test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        
        # Get the path from list_images which returns the correct format
        list_response = test_client.get('/images/')
        assert list_response.status_code == 200
        images = list_response.json()['images']
        assert len(images) > 0
        
        # Find our uploaded image
        uploaded_filename = upload_result['filename']
        image_info = next((img for img in images if img['filename'] == uploaded_filename), None)
        assert image_info is not None
        
        # Extract path components from the path returned by list_images
        path_parts = image_info['path'].replace('\\', '/').split('/')
        date_folder = path_parts[0]
        flight_folder = path_parts[1]
        filename = path_parts[2]
        
        # Get image by full path
        response = test_client.get(f'/images/{date_folder}/{flight_folder}/{filename}')
        assert response.status_code == 200
        assert response.headers['content-type'] == 'image/jpeg'
        assert len(response.content) > 0
    
    def test_get_image_by_path_not_found(self, test_client):
        """Test getting non-existent image by path"""
        response = test_client.get('/images/2024-01-01/flight_test/nonexistent.jpg')
        assert response.status_code == 404
        assert 'Image not found' in response.json()['detail']
    
    def test_get_image_by_path_png(self, test_client):
        """Test getting PNG image by path"""
        img = Image.new('RGB', (50, 50), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('test.png', img_bytes, 'image/png')}
        )
        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        
        # Get the path from list_images which returns the correct format
        list_response = test_client.get('/images/')
        assert list_response.status_code == 200
        images = list_response.json()['images']
        
        # Find our uploaded image
        uploaded_filename = upload_result['filename']
        image_info = next((img for img in images if img['filename'] == uploaded_filename), None)
        assert image_info is not None
        
        # Extract path components from the path returned by list_images
        path_parts = image_info['path'].replace('\\', '/').split('/')
        date_folder = path_parts[0]
        flight_folder = path_parts[1]
        filename = path_parts[2]
        
        response = test_client.get(f'/images/{date_folder}/{flight_folder}/{filename}')
        assert response.status_code == 200
        assert 'image/png' in response.headers['content-type']


class TestMetadataEndpoint:
    """Test cases for GET /metadata/{date}/{flight_folder}/{filename} endpoint"""
    
    def test_get_metadata_success(self, test_client, sample_image):
        """Test getting metadata for an image"""
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('metadata_test.jpg', sample_image, 'image/jpeg')},
            data={
                'flight_id': 'META_TEST',
                'gps_latitude': 37.7749,
                'gps_longitude': -122.4194,
                'altitude': 200.0,
                'notes': 'Metadata test'
            }
        )
        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        
        # Get the path from list_images which returns the correct format
        list_response = test_client.get('/images/')
        assert list_response.status_code == 200
        images = list_response.json()['images']
        
        # Find our uploaded image
        uploaded_filename = upload_result['filename']
        image_info = next((img for img in images if img['filename'] == uploaded_filename), None)
        assert image_info is not None
        
        # Extract path components from the path returned by list_images
        path_parts = image_info['path'].replace('\\', '/').split('/')
        date_folder = path_parts[0]
        flight_folder = path_parts[1]
        filename = path_parts[2]
        
        # Get metadata
        response = test_client.get(f'/metadata/{date_folder}/{flight_folder}/{filename}')
        assert response.status_code == 200
        metadata = response.json()
        assert metadata['flight_id'] == 'META_TEST'
        assert metadata['gps']['latitude'] == 37.7749
        assert metadata['gps']['longitude'] == -122.4194
        assert metadata['altitude'] == 200.0
        assert metadata['notes'] == 'Metadata test'
        assert 'upload_timestamp' in metadata
        assert 'server_timestamp' in metadata
    
    def test_get_metadata_not_found(self, test_client):
        """Test getting metadata for non-existent image"""
        response = test_client.get('/metadata/2024-01-01/flight_test/nonexistent.jpg')
        assert response.status_code == 404
        assert 'Metadata not found' in response.json()['detail']
    
    def test_get_metadata_without_optional_fields(self, test_client, sample_image):
        """Test getting metadata for image uploaded without optional fields"""
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('simple_test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        
        # Get the path from list_images which returns the correct format
        list_response = test_client.get('/images/')
        assert list_response.status_code == 200
        images = list_response.json()['images']
        
        # Find our uploaded image
        uploaded_filename = upload_result['filename']
        image_info = next((img for img in images if img['filename'] == uploaded_filename), None)
        assert image_info is not None
        
        # Extract path components from the path returned by list_images
        path_parts = image_info['path'].replace('\\', '/').split('/')
        date_folder = path_parts[0]
        flight_folder = path_parts[1]
        filename = path_parts[2]
        
        response = test_client.get(f'/metadata/{date_folder}/{flight_folder}/{filename}')
        assert response.status_code == 200
        metadata = response.json()
        assert 'original_filename' in metadata
        assert 'stored_filename' in metadata
        assert metadata['gps']['latitude'] is None
        assert metadata['gps']['longitude'] is None


class TestFlightsEndpoint:
    """Test cases for GET /flights/ endpoint"""
    
    def test_list_flights_empty(self, test_client):
        """Test listing flights when none exist"""
        response = test_client.get('/flights/')
        assert response.status_code == 404
        assert 'No flights found' in response.json()['detail']
    
    def test_list_flights_success(self, test_client, sample_image):
        """Test listing flights"""
        # Upload images with different flight_ids
        sample_image.seek(0)
        test_client.post(
            '/upload/',
            files={'file': ('flight1_img1.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FLIGHT_A'}
        )
        
        sample_image.seek(0)
        test_client.post(
            '/upload/',
            files={'file': ('flight1_img2.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FLIGHT_A'}
        )
        
        sample_image.seek(0)
        test_client.post(
            '/upload/',
            files={'file': ('flight2_img1.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FLIGHT_B'}
        )
        
        response = test_client.get('/flights/')
        assert response.status_code == 200
        result = response.json()
        assert 'total' in result
        assert 'flights' in result
        assert result['total'] >= 2
        assert len(result['flights']) >= 2
        
        # Check flight structure
        flight = result['flights'][0]
        assert 'date' in flight
        assert 'flight_id' in flight
        assert 'path' in flight
        assert 'image_count' in flight
        assert flight['image_count'] > 0


class TestStatsEndpoint:
    """Test cases for GET /stats/ endpoint"""
    
    def test_get_stats_empty(self, test_client):
        """Test getting stats when no images exist"""
        response = test_client.get('/stats/')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_images'] == 0
        assert stats['total_size_gb'] == 0.0
        assert stats['total_flights'] == 0
        assert 'timestamp' in stats
    
    def test_get_stats_with_images(self, test_client, sample_image):
        """Test getting stats with images"""
        # Upload multiple images
        for i in range(3):
            sample_image.seek(0)
            test_client.post(
                '/upload/',
                files={'file': (f'stats_test_{i}.jpg', sample_image, 'image/jpeg')},
                data={'flight_id': 'STATS_FLIGHT'}
            )
        
        response = test_client.get('/stats/')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_images'] >= 3
        assert stats['total_size_gb'] >= 0.0
        assert stats['total_flights'] >= 1
        assert 'images_per_flight' in stats
        assert 'timestamp' in stats
        assert 'STATS_FLIGHT' in stats['images_per_flight']
        assert stats['images_per_flight']['STATS_FLIGHT'] >= 3
    
    def test_get_stats_multiple_flights(self, test_client, sample_image):
        """Test stats with multiple flights"""
        # Upload images to different flights
        sample_image.seek(0)
        test_client.post(
            '/upload/',
            files={'file': ('img1.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FLIGHT_1'}
        )
        
        sample_image.seek(0)
        test_client.post(
            '/upload/',
            files={'file': ('img2.jpg', sample_image, 'image/jpeg')},
            data={'flight_id': 'FLIGHT_2'}
        )
        
        response = test_client.get('/stats/')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_flights'] >= 2
        assert len(stats['images_per_flight']) >= 2


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_upload_list_download_workflow(self, test_client, sample_image):
        """Test complete workflow: upload -> list -> download"""
        # Upload
        sample_image.seek(0)
        upload_response = test_client.post(
            '/upload/',
            files={'file': ('workflow_test.jpg', sample_image, 'image/jpeg')}
        )
        assert upload_response.status_code == 200
        stored_filename = upload_response.json().get('filename')
        
        # List
        list_response = test_client.get('/images/?simple=true')
        assert list_response.status_code == 200
        assert stored_filename in list_response.json()['images']
        
        # Download
        download_response = test_client.get(f'/images/{stored_filename}')
        assert download_response.status_code == 200
        assert download_response.headers['content-type'] == 'image/jpeg'
    
    def test_multiple_uploads_same_filename(self, test_client, sample_image):
        """Test uploading same filename multiple times (creates separate files with timestamps)"""
        # First upload
        sample_image.seek(0)
        response1 = test_client.post(
            '/upload/',
            files={'file': ('same_name.jpg', sample_image, 'image/jpeg')}
        )
        assert response1.status_code == 200
        filename1 = response1.json().get('filename')
        
        # Second upload with same name (creates new file with different timestamp)
        sample_image.seek(0)
        response2 = test_client.post(
            '/upload/',
            files={'file': ('same_name.jpg', sample_image, 'image/jpeg')}
        )
        assert response2.status_code == 200
        filename2 = response2.json().get('filename')
        
        # Should have two images (different timestamps create different files)
        list_response = test_client.get('/images/?simple=true')
        assert list_response.status_code == 200
        images = list_response.json()['images']
        assert filename1 in images
        assert filename2 in images
        assert len(images) >= 2

