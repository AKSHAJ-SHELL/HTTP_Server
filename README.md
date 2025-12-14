# Drone Image Server

A FastAPI-based image server designed for drone operations, automatically organizing and storing captured images with metadata (GPS, altitude, timestamps, etc.). The server starts automatically on boot and is optimized for real-time image capture and storage.

## Quick Start

1. Make sure Docker and Docker Compose are installed
2. Run: `docker-compose up -d`
3. Server will be available at `http://localhost:8000`
4. Server auto-starts on boot (configured with `restart: always`)

## Features

- **Automatic Organization**: Images organized by date and flight session
- **Metadata Storage**: GPS coordinates, altitude, camera settings, timestamps
- **Batch Upload**: Upload multiple images in a single request
- **Flight Tracking**: Group images by flight sessions
- **Health Monitoring**: Health check endpoint for system monitoring
- **Auto-Start**: Service automatically starts when drone/system boots
- **Comprehensive Logging**: All uploads logged with timestamps

## API Endpoints

### Image Management
- `POST /upload/` - Upload a single image with metadata
- `POST /upload/batch` - Upload multiple images at once
- `GET /images/` - List all images (optional filters: `flight_id`, `date`)
- `GET /images/{date}/{flight_folder}/{filename}` - Get specific image
- `GET /metadata/{date}/{flight_folder}/{filename}` - Get image metadata

### Flight Management
- `GET /flights/` - List all flight sessions
- `GET /stats/` - Get server statistics (total images, size, flights)

### System
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## Testing

### Running Tests

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run all tests:
   ```bash
   pytest
   ```

3. Run tests with coverage report:
   ```bash
   pytest --cov
   ```

4. Generate HTML coverage report:
   ```bash
   pytest --cov --cov-report=html
   ```
   Then open `htmlcov/index.html` in your browser

5. Run specific test file:
   ```bash
   pytest tests/test_server.py
   ```

6. Run specific test:
   ```bash
   pytest tests/test_server.py::TestUploadEndpoint::test_upload_image_success
   ```

### Test Coverage

The test suite covers:
- ✅ Image upload (success, failure, edge cases)
- ✅ Image listing (empty, with images)
- ✅ Image retrieval (success, 404 errors)
- ✅ Integration workflows
- ✅ Multiple file formats
- ✅ Client functions

## Drone Integration

### Using the Drone Client

The `drone_client.py` provides a Python client for uploading images from your drone:

```python
from drone_client import DroneImageClient

# Initialize client
client = DroneImageClient("http://127.0.0.1:8000")

# Upload single image with metadata
client.upload_image(
    image_path="captured_image.jpg",
    flight_id="FLIGHT_001",
    gps_latitude=37.7749,
    gps_longitude=-122.4194,
    altitude=100.5,
    camera_settings={"iso": 400, "shutter": "1/500", "aperture": "f/2.8"},
    notes="Survey area A"
)

# Upload multiple images (batch)
image_files = ["img1.jpg", "img2.jpg", "img3.jpg"]
client.upload_batch(
    image_paths=image_files,
    flight_id="FLIGHT_001",
    gps_latitude=37.7749,
    gps_longitude=-122.4194,
    altitude=100.5
)
```

### Image Organization

Images are automatically organized in the following structure:
```
images/
  └── 2025-11-08/          # Date folder
      └── flight_20251108_143022/  # Flight session folder
          ├── 20251108_143025_123.jpg
          ├── 20251108_143026_456.jpg
          └── ...
metadata/
  └── 2025-11-08/
      └── flight_20251108_143022/
          ├── 20251108_143025_123.json
          ├── 20251108_143026_456.json
          └── ...
```

### Metadata Format

Each image has associated metadata stored as JSON:
```json
{
  "original_filename": "IMG_001.jpg",
  "stored_filename": "20251108_143025_123.jpg",
  "upload_timestamp": "2025-11-08T14:30:25.123",
  "flight_id": "FLIGHT_001",
  "gps": {
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "altitude": 100.5,
  "camera_settings": {
    "iso": 400,
    "shutter": "1/500",
    "aperture": "f/2.8"
  },
  "notes": "Survey area A",
  "file_size": 2048576,
  "content_type": "image/jpeg"
}
```

### Continuous Upload from Drone

For continuous real-time uploads, integrate the client into your drone's image capture loop:

```python
import time
from drone_client import DroneImageClient

client = DroneImageClient("http://192.168.1.100:8000")  # Drone's server IP
flight_id = f"FLIGHT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

while capturing:
    image_path = capture_image()  # Your capture function
    gps = get_gps_coordinates()   # Your GPS function
    altitude = get_altitude()     # Your altitude function
    
    client.upload_image(
        image_path=image_path,
        flight_id=flight_id,
        gps_latitude=gps['lat'],
        gps_longitude=gps['lon'],
        altitude=altitude
    )
    
    time.sleep(0.1)  # Adjust based on capture rate
```

## Sharing with Others

Just share the `docker-compose.yml` file along with:
- `Dockerfile`
- `requirements.txt`
- `server.py`
- `drone_client.py`
- `tests/` directory (for testing)

They can run it with: `docker-compose up -d`

## Stopping the Server

Run: `docker-compose down`

## Auto-Start on Boot

The server can be configured to automatically start when your system boots. This ensures the service is always available.

### Prerequisites

1. **Enable Docker Desktop Auto-Start:**
   - Open Docker Desktop
   - Go to Settings (gear icon)
   - Navigate to "General"
   - Check "Start Docker Desktop when you log in"
   - Click "Apply & Restart"

### Method 1: Using Docker Restart Policy (Recommended)

The `docker-compose.yml` is configured with `restart: always`, which means:
- Containers will automatically start when Docker Desktop starts
- Containers will restart if they crash
- Containers will start after system reboot (if Docker Desktop auto-starts)

**To enable:**
1. Ensure Docker Desktop is set to start on login (see Prerequisites)
2. Start the containers once: `docker-compose up -d`
3. The containers will now automatically start on every boot

### Method 2: Using Startup Scripts

For additional reliability, you can use the provided startup scripts:

#### Option A: PowerShell Script

1. **Add to Windows Startup Folder:**
   - Press `Win + R`, type `shell:startup`, press Enter
   - Create a shortcut to `start-server.ps1`
   - Right-click the shortcut → Properties
   - In "Target", add: `powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\start-server.ps1"`

2. **Or use Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Trigger: "When the computer starts"
   - Action: "Start a program"
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\start-server.ps1"`

#### Option B: Batch File

1. **Add to Windows Startup Folder:**
   - Press `Win + R`, type `shell:startup`, press Enter
   - Copy `start-server.bat` to this folder
   - Or create a shortcut to `start-server.bat`

2. **Or use Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Trigger: "When the computer starts"
   - Action: "Start a program"
   - Program: `C:\path\to\start-server.bat`

### Verifying Auto-Start

After configuring auto-start:

1. **Restart your computer**
2. **Wait for Docker Desktop to start** (check system tray)
3. **Verify containers are running:**
   ```powershell
   docker-compose ps
   ```
4. **Test the server:**
   - Open browser: `http://localhost:8000/docs`
   - Or check status: `docker ps`

### Troubleshooting

**Containers don't start on boot:**
- Verify Docker Desktop is set to start on login
- Check if Docker Desktop is running (system tray icon)
- Manually run: `docker-compose up -d`
- Check Docker Desktop logs for errors

**Startup script doesn't work:**
- Ensure the script path is correct
- For PowerShell: Check execution policy with `Get-ExecutionPolicy`
- Run the script manually to see error messages
- Check Windows Event Viewer for script errors

**Port 8000 already in use:**
- Another service may be using port 8000
- Stop the conflicting service or change the port in `docker-compose.yml`

**Docker Desktop doesn't start automatically:**
- Re-check Docker Desktop settings
- Ensure you're logged in to Windows (not just locked)
- Check Windows Startup programs list

