# videotoPDF

# macOS Slide Capture

A Python tool that automatically detects and captures slides during presentations or lectures, then compiles them into a PDF document.

## Overview

This tool monitors a window or screen region for changes and automatically captures screenshots when it detects a new slide. Perfect for capturing lecture slides, webinar presentations, or any video content with changing slides.

## Script Versions

This repository contains multiple versions of the capture script:

| Script | Capture Modes | Description |
|--------|---------------|-------------|
| `videoToPDF.py` | First + Last | **Recommended** - Full-featured version with both capture modes |
| `videoToPDF2.py` | First only | Basic version without "Last" mode support |
| `videoToPDF_backup.py` | First + Last | Backup copy of the full-featured version |

**Use `videoToPDF.py`** for the best experience, especially if you need to capture slides with animations.

## Features

- **Automatic slide detection** - Captures frames only when content changes significantly
- **Two capture modes** - "First" mode for immediate capture, "Last" mode for slides with animations
- **Smart window detection** - Automatically finds presentation windows (Box, YouTube, Zoom, etc.)
- **Full screen support** - Can capture the entire screen if needed
- **PDF compilation** - Automatically creates a PDF with all captured slides
- **Configurable sensitivity** - Adjust how different frames need to be to trigger a capture
- **Multi-desktop support** - Detects windows across all macOS Spaces/Desktops
- **Individual slide backup** - Saves each slide as a separate PNG file

## Requirements

### System
- macOS (uses native macOS APIs)
- Python 3.7+

### Python Packages
```bash
pip install opencv-python numpy pillow pyobjc-framework-Quartz
```

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install opencv-python numpy pillow pyobjc-framework-Quartz
```

3. Make the script executable (optional):
```bash
chmod +x videoToPDF.py
```

## Usage

### Basic Usage

Run the script:
```bash
python3 videoToPDF.py
```

### Interactive Setup

The tool will guide you through setup:

1. **Sensitivity Selection**
   - Low (0.02) - Captures even small changes
   - Medium (0.05) - Balanced (recommended)
   - High (0.10) - Only major changes

2. **Check Interval**
   - How often to check for changes (default: 1.0 second)

3. **Capture Mode**
   - **First** (default) - Captures immediately when slide changes
   - **Last** - Waits for content to stabilize before capturing (ideal for slides with incremental animations)

4. **Window Selection**
   - The tool auto-detects windows containing presentations
   - If multiple windows found, you'll choose which one to capture
   - Option to use full screen if no window is detected

5. **Capture**
   - Keep the presentation window visible during capture
   - Press `Ctrl+C` to stop and generate the PDF

### Example Session

```
macOS Slide Capture
==================================================

Sensitivity settings:
  Low (0.02)   - Captures even small changes
  Medium (0.05) - Balanced (recommended)
  High (0.10)  - Only major changes

Enter sensitivity (or press Enter for default 0.05):
Check interval in seconds (default 1.0):

Capture mode:
  first - Capture immediately when slide changes (default)
  last  - Capture final state after incremental changes stop
Enter mode (first/last, default: first):

Attempting to auto-detect lecture window...
✓ Found 1 matching window(s):
  1. Lecture Recording - Box (Google Chrome)

Slide capture started!
Slides will be saved to: slides/session_20241104_143022
Press Ctrl+C to stop and save PDF

✓ Captured slide 1
✓ Captured slide 2
✓ Captured slide 3
...
```

## Output

The tool creates two types of output in the `slides/` directory:

1. **PDF File** - `slides_YYYYMMDD_HHMMSS.pdf`
   - Complete presentation with all slides
   - High quality (95% quality, 100 DPI)

2. **Session Folder** - `session_YYYYMMDD_HHMMSS/`
   - Individual PNG files for each slide
   - Named as `slide_001.png`, `slide_002.png`, etc.
   - Backup in case PDF generation fails

## Configuration

### Sensitivity Settings

Sensitivity determines how different two frames need to be to count as a slide change:

- **0.02 (Low)** - Very sensitive, captures minor changes
  - Best for: Presentations with subtle transitions
  - May capture: Mouse movements, minor text updates

- **0.05 (Medium)** - Recommended default
  - Best for: Most presentations
  - Balances accuracy and avoiding duplicates

- **0.10 (High)** - Less sensitive, only major changes
  - Best for: Presentations with dramatic slide changes
  - May miss: Slides with small incremental updates

### Check Interval

Controls how often the tool checks for changes:

- **0.5 seconds** - Very responsive, higher CPU usage
- **1.0 seconds** - Balanced (recommended)
- **2.0 seconds** - Lower CPU usage, may miss quick slides

### Capture Modes

The tool offers two capture modes to handle different types of presentations:

#### First Mode (Default)
Captures the slide immediately when a change is detected.

- **Best for**: Standard presentations with instant slide transitions
- **Behavior**: Saves a screenshot as soon as content differs from the previous frame
- **Use when**: Slides appear fully rendered in a single transition

#### Last Mode
Waits for the slide content to stabilize before capturing, ensuring you get the final state.

- **Best for**: Presentations with incremental animations or builds
- **Behavior**: Detects a change, then waits for the content to remain stable for ~3 seconds before saving
- **Use when**: Slides have bullet points that appear one-by-one, animated diagrams, or progressive reveals
- **Note**: Captures the complete slide after all animations finish, avoiding partial captures

## Tips

- **Keep window visible** - The tool captures what's on screen, so keep the presentation window visible
- **Use a dedicated Space** - Switch to a desktop Space with just the presentation window
- **Avoid overlapping windows** - Don't cover the presentation window during capture
- **Test sensitivity** - Try a short test run to find the right sensitivity for your content
- **Monitor console** - Watch the console output to see when slides are captured

## Troubleshooting

### "No matching windows found"
- Make sure the presentation is open in a visible window
- Try using full screen capture mode
- Check that the window title contains recognizable keywords (Box, YouTube, Zoom, etc.)

### Too many/few slides captured
- Adjust sensitivity:
  - Too many captures → Increase sensitivity (e.g., 0.08)
  - Too few captures → Decrease sensitivity (e.g., 0.03)

### Window detection issues
- The tool searches for these keywords: Box, YouTube, Chrome, Safari, Firefox, Zoom, Google Meet, Microsoft Teams
- Ensure your presentation window contains one of these in its title or app name

### Permissions
If you get permission errors, you may need to grant:
- **Screen Recording** permission in System Preferences → Security & Privacy → Privacy → Screen Recording

## Technical Details

### How It Works

1. **Window Detection** - Uses macOS Quartz APIs to enumerate all windows
2. **Screen Capture** - Uses PIL's ImageGrab for reliable cross-platform capture
3. **Change Detection** - Converts frames to grayscale and calculates pixel differences
4. **Slide Storage** - Saves captures as PNG files
5. **PDF Generation** - Compiles all slides into a single PDF using PIL

### Ignored Windows

To avoid capturing irrelevant windows, the tool ignores:
- System apps (Dock, Finder, Control Center, etc.)
- Development tools (VS Code, Terminal, etc.)
- Communication apps (Mail, Slack, Outlook, etc.)
- Windows with "Claude" or "claude.ai" in the title

## License

This tool is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues or pull requests for improvements!

## Changelog

### Version 1.1
- Added "Last" capture mode for slides with incremental animations
- Stability detection waits for content to settle before capturing
- Improved handling of animated/progressive slide reveals

### Version 1.0
- Initial release
- Auto-detection of presentation windows
- PDF compilation
- Configurable sensitivity and check interval
- Multi-desktop support for macOS
