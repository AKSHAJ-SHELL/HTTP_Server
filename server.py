from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
import os
import json
from datetime import datetime
from pathlib import Path
import uuid

app = FastAPI(
    title="Drone Image Server",
    description="Server for storing and managing drone-captured images with metadata",
    version="1.0.0"
)

# Directories
IMAGE_DIR = "images"
METADATA_DIR = "metadata"
LOGS_DIR = "logs"

# Ensure directories exist
for directory in [IMAGE_DIR, METADATA_DIR, LOGS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_timestamped_path(flight_id: Optional[str] = None) -> tuple:
    """Generate timestamped directory structure"""
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    
    if flight_id:
        flight_folder = f"flight_{flight_id}"
    else:
        flight_folder = f"flight_{now.strftime('%Y%m%d_%H%M%S')}"
    
    full_path = os.path.join(IMAGE_DIR, date_folder, flight_folder)
    os.makedirs(full_path, exist_ok=True)
    
    return full_path, date_folder, flight_folder


def generate_filename(original_filename: str) -> str:
    """Generate timestamped filename"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds precision
    ext = os.path.splitext(original_filename)[1]
    return f"{timestamp}{ext}"


def save_metadata(image_path: str, metadata: dict, flight_id: Optional[str] = None):
    """Save image metadata to JSON file"""
    metadata_file = image_path.replace(IMAGE_DIR, METADATA_DIR).replace(
        os.path.splitext(image_path)[1], ".json"
    )
    
    # Create metadata directory structure
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    
    # Add server-side metadata
    metadata["server_timestamp"] = datetime.now().isoformat()
    metadata["image_path"] = image_path
    metadata["metadata_file"] = metadata_file
    
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_file


def log_upload(filename: str, flight_id: Optional[str] = None):
    """Log upload activity"""
    log_file = os.path.join(LOGS_DIR, f"uploads_{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | Flight: {flight_id or 'N/A'} | Image: {filename}\n")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "drone-image-server",
        "version": "1.0.0"
    }


@app.post("/upload/")
async def upload_image(
    file: UploadFile = File(...),
    flight_id: Optional[str] = Form(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    altitude: Optional[float] = Form(None),
    camera_settings: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    """Upload a single image with optional metadata"""
    try:
        # Generate timestamped path
        full_path, date_folder, flight_folder = get_timestamped_path(flight_id)
        
        # Generate filename
        filename = generate_filename(file.filename)
        image_path = os.path.join(full_path, filename)
        
        # Save image
        content = await file.read()
        with open(image_path, "wb") as image_file:
            image_file.write(content)
        
        # Prepare metadata
        metadata = {
            "original_filename": file.filename,
            "stored_filename": filename,
            "upload_timestamp": datetime.now().isoformat(),
            "flight_id": flight_id,
            "gps": {
                "latitude": gps_latitude,
                "longitude": gps_longitude
            },
            "altitude": altitude,
            "camera_settings": json.loads(camera_settings) if camera_settings else None,
            "notes": notes,
            "file_size": len(content),
            "content_type": file.content_type
        }
        
        # Save metadata
        metadata_file = save_metadata(image_path, metadata, flight_id)
        
        # Log upload
        log_upload(filename, flight_id)
        
        return {
            "filename": filename,  # First for backward compatibility
            "status": "success",
            "path": image_path,
            "metadata_file": metadata_file,
            "flight_id": flight_id or flight_folder,
            "uploaded_at": metadata["upload_timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/upload/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    flight_id: Optional[str] = Form(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    altitude: Optional[float] = Form(None)
):
    """Upload multiple images in a single request"""
    results = []
    
    for file in files:
        try:
            # Generate timestamped path
            full_path, date_folder, flight_folder = get_timestamped_path(flight_id)
            
            # Generate filename
            filename = generate_filename(file.filename)
            image_path = os.path.join(full_path, filename)
            
            # Save image
            content = await file.read()
            with open(image_path, "wb") as image_file:
                image_file.write(content)
            
            # Prepare metadata
            metadata = {
                "original_filename": file.filename,
                "stored_filename": filename,
                "upload_timestamp": datetime.now().isoformat(),
                "flight_id": flight_id,
                "gps": {
                    "latitude": gps_latitude,
                    "longitude": gps_longitude
                },
                "altitude": altitude,
                "file_size": len(content),
                "content_type": file.content_type
            }
            
            # Save metadata
            metadata_file = save_metadata(image_path, metadata, flight_id)
            
            # Log upload
            log_upload(filename, flight_id)
            
            results.append({
                "status": "success",
                "filename": filename,
                "path": image_path
            })
        except Exception as e:
            results.append({
                "status": "error",
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }


@app.get("/images/")
async def list_images(flight_id: Optional[str] = None, date: Optional[str] = None, simple: bool = False):
    """List all images, optionally filtered by flight_id or date
    
    Args:
        flight_id: Optional flight ID filter
        date: Optional date filter (YYYY-MM-DD)
        simple: If True, returns simple list of filenames for backward compatibility
    """
    images_list = []
    
    if date:
        # List images for specific date
        date_path = os.path.join(IMAGE_DIR, date)
        if not os.path.exists(date_path):
            raise HTTPException(status_code=404, detail=f"No images found for date: {date}")
        
        for flight_folder in os.listdir(date_path):
            if flight_id and f"flight_{flight_id}" != flight_folder:
                continue
            flight_path = os.path.join(date_path, flight_folder)
            if os.path.isdir(flight_path):
                for filename in os.listdir(flight_path):
                    if os.path.isfile(os.path.join(flight_path, filename)):
                        images_list.append({
                            "filename": filename,
                            "path": f"{date}/{flight_folder}/{filename}",
                            "flight_id": flight_folder.replace("flight_", "")
                        })
    else:
        # List all images
        for root, dirs, files in os.walk(IMAGE_DIR):
            for filename in files:
                rel_path = os.path.relpath(os.path.join(root, filename), IMAGE_DIR)
                flight_folder = os.path.basename(os.path.dirname(rel_path))
                images_list.append({
                    "filename": filename,
                    "path": rel_path.replace("\\", "/"),
                    "flight_id": flight_folder.replace("flight_", "") if "flight_" in flight_folder else None
                })
    
    if not images_list:
        raise HTTPException(status_code=404, detail="No images found")
    
    # Backward compatibility: return simple list if requested
    if simple:
        return {"images": [img["filename"] for img in images_list]}
    
    return {
        "total": len(images_list),
        "images": images_list
    }


@app.get("/images/{date}/{flight_folder}/{filename}")
async def get_image(date: str, flight_folder: str, filename: str):
    """Get a specific image by date/flight/filename"""
    image_path = os.path.join(IMAGE_DIR, date, flight_folder, filename)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    ext = os.path.splitext(filename)[1].lower()
    content_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tiff": "image/tiff",
        ".tif": "image/tiff"
    }
    media_type = content_type_map.get(ext, "image/jpeg")
    
    return FileResponse(image_path, media_type=media_type)


@app.get("/images/{filename}")
async def get_image_by_filename(filename: str):
    """Get an image by filename (backward compatible - searches all directories)
    
    This endpoint searches for images by filename across all directories.
    For better performance, use /images/{date}/{flight_folder}/{filename} if you know the path.
    """
    # Search for the image across all directories
    for root, dirs, files in os.walk(IMAGE_DIR):
        if filename in files:
            image_path = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            content_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".tiff": "image/tiff",
                ".tif": "image/tiff"
            }
            media_type = content_type_map.get(ext, "image/jpeg")
            return FileResponse(image_path, media_type=media_type)
    
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/metadata/{date}/{flight_folder}/{filename}")
async def get_metadata(date: str, flight_folder: str, filename: str):
    """Get metadata for a specific image"""
    image_path = os.path.join(IMAGE_DIR, date, flight_folder, filename)
    metadata_file = image_path.replace(IMAGE_DIR, METADATA_DIR).replace(
        os.path.splitext(image_path)[1], ".json"
    )
    
    if not os.path.exists(metadata_file):
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    return metadata


@app.get("/flights/")
async def list_flights():
    """List all flight sessions"""
    flights = []
    
    for date_folder in os.listdir(IMAGE_DIR):
        date_path = os.path.join(IMAGE_DIR, date_folder)
        if os.path.isdir(date_path):
            for flight_folder in os.listdir(date_path):
                flight_path = os.path.join(date_path, flight_folder)
                if os.path.isdir(flight_path) and "flight_" in flight_folder:
                    image_count = len([f for f in os.listdir(flight_path) if os.path.isfile(os.path.join(flight_path, f))])
                    flights.append({
                        "date": date_folder,
                        "flight_id": flight_folder.replace("flight_", ""),
                        "path": f"{date_folder}/{flight_folder}",
                        "image_count": image_count
                    })
    
    if not flights:
        raise HTTPException(status_code=404, detail="No flights found")
    
    return {
        "total": len(flights),
        "flights": flights
    }


@app.get("/stats/")
async def get_stats():
    """Get server statistics"""
    total_images = 0
    total_size = 0
    flights = {}
    
    for root, dirs, files in os.walk(IMAGE_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            total_images += 1
            total_size += os.path.getsize(file_path)
            
            # Count by flight
            flight_folder = os.path.basename(os.path.dirname(file_path))
            if "flight_" in flight_folder:
                flight_id = flight_folder.replace("flight_", "")
                if flight_id not in flights:
                    flights[flight_id] = 0
                flights[flight_id] += 1
    
    return {
        "total_images": total_images,
        "total_size_gb": round(total_size / (1024**3), 2),
        "total_flights": len(flights),
        "images_per_flight": flights,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
