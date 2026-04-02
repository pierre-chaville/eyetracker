# GazeSpeaker Bridge

A C# application that streams Tobii Eye Tracker data over WebSocket for integration with web applications (Vue.js, React) and Python backends (FastAPI, Flask).

## Features

- **Real-time eye tracking data** streaming at ~30 FPS
- **WebSocket server** on `ws://127.0.0.1:8765`
- **Accurate screen coordinates** using actual display resolution (not DPI-scaled)
- **JSON data format** for easy integration
- Supports **Tobii Eye Tracker 5** and compatible devices

## Requirements

- **.NET 8.0 SDK** (64-bit)
- **Tobii Eye Tracker** (Eye Tracker 5 or compatible)
- **Tobii Stream Engine** installed
- Windows OS

## Installation

1. Clone this repository
2. Ensure Tobii software is installed and eye tracker is connected
3. Build the project:
   ```bash
   dotnet build
   ```

## Usage

Run the application:
```bash
dotnet run
```

The WebSocket server will start on `ws://127.0.0.1:8765` and begin broadcasting gaze data.

### Data Format

The server broadcasts JSON data at approximately 30 FPS:

```json
{
  "timestamp": 1704672000000,
  "x": 0.5,
  "y": 0.3,
  "pixelX": 1280,
  "pixelY": 432,
  "screenWidth": 2560,
  "screenHeight": 1440,
  "valid": true
}
```

**Fields:**
- `timestamp`: Unix timestamp in milliseconds
- `x`, `y`: Normalized gaze coordinates (0.0 to 1.0)
- `pixelX`, `pixelY`: Screen coordinates in pixels
- `screenWidth`, `screenHeight`: Actual screen resolution
- `valid`: Always true (only sent when gaze data is valid)

## Client Examples

### JavaScript/Vue.js
```javascript
const ws = new WebSocket('ws://127.0.0.1:8765');

ws.onopen = () => console.log('Connected to GazeSpeaker bridge');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Gaze: ${data.pixelX}, ${data.pixelY}`);
};

ws.onerror = (error) => console.error('WebSocket error:', error);
```

### Python
```python
import asyncio
import websockets
import json

async def receive_gaze():
    async with websockets.connect('ws://127.0.0.1:8765') as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Gaze: {data['pixelX']}, {data['pixelY']}")

asyncio.run(receive_gaze())
```

## Configuration

- **Update frequency**: Modify `Thread.Sleep(33)` in [Program.cs](Program.cs#L210) (33ms = ~30 FPS)
- **WebSocket port**: Change `ws://127.0.0.1:8765` in [Program.cs](Program.cs#L33)
- **Screen resolution**: Automatically detected, but can be modified in [Program.cs](Program.cs#L162-L172)

## Project Structure

```
c#bridge/
├── Program.cs              # Main application logic
├── GazeSpeakerInterop.cs  # P/Invoke declarations for Tobii API
├── tobii_stream_engine.dll # Tobii native library (64-bit)
├── GazeSpeakerBridge.csproj
└── README.md
```

## Troubleshooting

### "No Tobii device found"
- Ensure Tobii Eye Tracker is connected and recognized by Windows
- Check Tobii Experience/Control Panel is running
- Restart the application

### "Failed to create API context"
- Verify `tobii_stream_engine.dll` is 64-bit and in project directory
- Ensure .NET 8.0 64-bit runtime is installed

### Access Violation Errors
- Make sure you're using the correct version of `tobii_stream_engine.dll` (64-bit from `C:\Program Files\Tobii\Tobii EyeX\`)
- Ensure project is compiled for x64 platform

## Technical Details

- **Platform Target**: x64
- **.NET Version**: 8.0
- **WebSocket Library**: Fleck 1.2.0
- **Tobii API**: Stream Engine (native C API via P/Invoke)

## License

Private repository - All rights reserved

## Notes

- Eye position tracking (individual eye coordinates) is not supported on consumer Tobii devices like Eye Tracker 5
- The application uses `EnumDisplaySettings` to get actual screen resolution, bypassing Windows DPI scaling
- Data is only broadcast when clients are connected to reduce CPU usage
