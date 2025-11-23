"""
Drone Client for uploading images to the image server
Supports single and batch uploads with metadata (GPS, altitude, etc.)
"""

import requests
import os
import mimetypes
from typing import Optional, List, Dict
from datetime import datetime
import json


class DroneImageClient:
    """Client for uploading drone images with metadata"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8000"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
    
    def upload_image(
        self,
        image_path: str,
        flight_id: Optional[str] = None,
        gps_latitude: Optional[float] = None,
        gps_longitude: Optional[float] = None,
        altitude: Optional[float] = None,
        camera_settings: Optional[Dict] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Upload a single image with metadata
        
        Args:
            image_path: Path to the image file
            flight_id: Optional flight session ID
            gps_latitude: GPS latitude coordinate
            gps_longitude: GPS longitude coordinate
            altitude: Altitude in meters
            camera_settings: Dictionary of camera settings (ISO, shutter, etc.)
            notes: Optional notes about the image
        
        Returns:
            Dictionary with upload result or None if failed
        """
        if not os.path.exists(image_path):
            print(f"Error: File not found: {image_path}")
            return None
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"
        
        url = f"{self.server_url}/upload/"
        
        # Prepare form data
        data = {}
        if flight_id:
            data["flight_id"] = flight_id
        if gps_latitude is not None:
            data["gps_latitude"] = str(gps_latitude)
        if gps_longitude is not None:
            data["gps_longitude"] = str(gps_longitude)
        if altitude is not None:
            data["altitude"] = str(altitude)
        if camera_settings:
            data["camera_settings"] = json.dumps(camera_settings)
        if notes:
            data["notes"] = notes
        
        # Upload file
        try:
            with open(image_path, "rb") as image_file:
                filename = os.path.basename(image_path)
                files = {"file": (filename, image_file, mime_type)}
                response = self.session.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Uploaded: {filename} (Flight: {flight_id or 'N/A'})")
                return result
            else:
                print(f"✗ Upload failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Error uploading {image_path}: {str(e)}")
            return None
    
    def upload_batch(
        self,
        image_paths: List[str],
        flight_id: Optional[str] = None,
        gps_latitude: Optional[float] = None,
        gps_longitude: Optional[float] = None,
        altitude: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Upload multiple images in a single request
        
        Args:
            image_paths: List of paths to image files
            flight_id: Optional flight session ID
            gps_latitude: GPS latitude coordinate
            gps_longitude: GPS longitude coordinate
            altitude: Altitude in meters
        
        Returns:
            Dictionary with batch upload results
        """
        url = f"{self.server_url}/upload/batch"
        
        # Prepare form data
        data = {}
        if flight_id:
            data["flight_id"] = flight_id
        if gps_latitude is not None:
            data["gps_latitude"] = str(gps_latitude)
        if gps_longitude is not None:
            data["gps_longitude"] = str(gps_longitude)
        if altitude is not None:
            data["altitude"] = str(altitude)
        
        # Prepare files - use try-except to handle file opening errors
        files = []
        opened_files = []  # Track opened files for cleanup
        
        try:
            for image_path in image_paths:
                if not os.path.exists(image_path):
                    print(f"Warning: File not found, skipping: {image_path}")
                    continue
                
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = "image/jpeg"
                
                filename = os.path.basename(image_path)
                try:
                    file_handle = open(image_path, "rb")
                    opened_files.append(file_handle)
                    files.append(("files", (filename, file_handle, mime_type)))
                except (OSError, PermissionError, IOError) as e:
                    print(f"Warning: Could not open {image_path}: {str(e)}")
                    # Close any files already opened before re-raising
                    for f in opened_files:
                        try:
                            f.close()
                        except:
                            pass
                    raise
        
            if not files:
                print("Error: No valid files to upload")
                return None
            
            # Perform the upload
            response = self.session.post(url, files=files, data=data, timeout=60)
            
            # Close file handles after successful POST
            for file_handle in opened_files:
                try:
                    file_handle.close()
                except:
                    pass
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Batch upload: {result['successful']}/{result['total']} successful")
                return result
            else:
                print(f"✗ Batch upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            # Ensure all opened files are closed on any error
            for file_handle in opened_files:
                try:
                    file_handle.close()
                except:
                    pass
            print(f"✗ Error in batch upload: {str(e)}")
            return None
    
    def list_images(self, flight_id: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """List all images, optionally filtered by flight_id or date"""
        url = f"{self.server_url}/images/"
        params = {}
        if flight_id:
            params["flight_id"] = flight_id
        if date:
            params["date"] = date
        
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                return response.json().get("images", [])
            else:
                print(f"Failed to list images: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error listing images: {str(e)}")
            return []
    
    def get_flights(self) -> List[Dict]:
        """Get list of all flight sessions"""
        url = f"{self.server_url}/flights/"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get("flights", [])
            else:
                print(f"Failed to get flights: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting flights: {str(e)}")
            return []
    
    def get_stats(self) -> Optional[Dict]:
        """Get server statistics"""
        url = f"{self.server_url}/stats/"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get stats: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """Check if server is healthy"""
        url = f"{self.server_url}/health"
        try:
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = DroneImageClient("http://127.0.0.1:8000")
    
    # Check server health
    if not client.health_check():
        print("Error: Server is not responding. Is it running?")
        exit(1)
    
    print("Server is healthy!")
    
    # Example: Upload a single image with metadata
    # client.upload_image(
    #     image_path="path/to/image.jpg",
    #     flight_id="FLIGHT_001",
    #     gps_latitude=37.7749,
    #     gps_longitude=-122.4194,
    #     altitude=100.5,
    #     camera_settings={"iso": 400, "shutter": "1/500", "aperture": "f/2.8"},
    #     notes="Test image from drone"
    # )
    
    # Example: Upload multiple images
    # image_files = ["image1.jpg", "image2.jpg", "image3.jpg"]
    # client.upload_batch(
    #     image_paths=image_files,
    #     flight_id="FLIGHT_001",
    #     gps_latitude=37.7749,
    #     gps_longitude=-122.4194,
    #     altitude=100.5
    # )
    
    # Get statistics
    stats = client.get_stats()
    if stats:
        print(f"\nServer Stats:")
        print(f"  Total Images: {stats['total_images']}")
        print(f"  Total Size: {stats['total_size_gb']} GB")
        print(f"  Total Flights: {stats['total_flights']}")

