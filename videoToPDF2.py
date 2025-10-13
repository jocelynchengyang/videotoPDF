#!/usr/bin/env python3
"""
Slide Capture for macOS
Captures slides when they change and saves as PDF
"""

import cv2
import numpy as np
import time
import os
from datetime import datetime
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionAll,
    kCGWindowListExcludeDesktopElements,
    kCGNullWindowID,
    CGDisplayBounds,
    CGMainDisplayID
)
from Quartz.CoreGraphics import (
    CGDisplayCreateImage,
    CGImageGetWidth,
    CGImageGetHeight,
    CGImageGetDataProvider,
    CGDataProviderCopyData
)
from PIL import Image


class MacOSScreenCapture:
    """Screen capture utility for macOS using native APIs"""
    
    def __init__(self, region=None):
        """
        Initialize screen capture
        
        Args:
            region: Tuple of (x, y, width, height) or None for full screen
        """
        self.region = region
        # Store full screen dimensions for scaling calculations
        bounds = CGDisplayBounds(CGMainDisplayID())
        self.screen_width = int(bounds.size.width)
        self.screen_height = int(bounds.size.height)
        
    def capture_frame(self):
        """Capture a single frame from the screen using PIL for proper handling"""
        from PIL import ImageGrab
        
        try:
            # Use PIL's screen capture for region or full screen
            if self.region and len(self.region) == 4:
                x, y, w, h = self.region
                bbox = (x, y, x + w, y + h)
                pil_image = ImageGrab.grab(bbox=bbox)
            else:
                # Full screen capture
                pil_image = ImageGrab.grab()
            
            # Convert PIL image to numpy array (RGB format)
            img_array = np.array(pil_image)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None


class SlideCapture:
    """Captures slides when they change and saves as PDF"""
    
    def __init__(self, output_dir="slides", sensitivity=0.05, check_interval=1.0):
        """
        Initialize slide capture
        
        Args:
            output_dir: Directory to save slides
            sensitivity: How different frames need to be to count as a change (0-1)
            check_interval: How often to check for changes (seconds)
        """
        self.output_dir = output_dir
        self.sensitivity = sensitivity
        self.check_interval = check_interval
        self.slides = []
        self.is_capturing = False
        self.last_frame = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def auto_detect_window(self, keywords):
        """
        Auto-detect window based on keywords using macOS native APIs
        
        Args:
            keywords: List of keywords to search for in window titles
            
        Returns:
            Tuple of (x, y, width, height) or None
        """
        try:
            # Get ALL windows, including those on other Spaces/Desktops
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionAll | kCGWindowListExcludeDesktopElements,
                kCGNullWindowID
            )
            
            # System apps and development tools to ignore
            ignored_apps = ["Control Center", "SystemUIServer", "Dock", "Window Server", 
                           "Notification Center", "Spotlight", "Finder", "Code", "Visual Studio Code",
                           "Terminal", "iTerm", "PyCharm", "Sublime Text", "Atom", "VSCode",
                           "Microsoft Outlook", "Outlook", "Mail", "Calendar", "Slack", "Discord",
                           "Window Server", "SystemUIServer"]
            
            # Ignore windows with these terms in the title
            ignored_title_terms = ["Claude", "claude.ai"]
            
            print(f"\nScanning {len(window_list)} windows across all desktops...")
            
            matches = []
            all_chrome_windows = []  # Track all Chrome windows for debugging
            
            for window in window_list:
                title = window.get('kCGWindowName', '')
                owner = window.get('kCGWindowOwnerName', '')
                layer = window.get('kCGWindowLayer', 0)
                
                # Debug: Track Chrome windows
                if owner == "Google Chrome" and title:
                    all_chrome_windows.append(title)
                
                # Skip system windows
                if owner in ignored_apps:
                    continue
                
                # Skip windows without titles
                if not title:
                    continue
                
                # Skip windows with ignored terms in title
                if any(term.lower() in title.lower() for term in ignored_title_terms):
                    continue
                
                # Skip very small windows (likely UI elements)
                bounds = window.get('kCGWindowBounds', {})
                if bounds.get('Width', 0) < 200 or bounds.get('Height', 0) < 200:
                    continue
                
                # Skip windows at certain layers (menus, overlays, etc.)
                if layer < 0:
                    continue
                
                # Check if any keyword matches
                search_text = f"{title} {owner}".lower()
                for keyword in keywords:
                    if keyword.lower() in search_text:
                        matches.append({
                            'title': title,
                            'owner': owner,
                            'bounds': bounds,
                            'keyword': keyword,
                            'priority': keywords.index(keyword),
                            'layer': layer
                        })
                        break
            
            # Show Chrome windows for debugging
            if all_chrome_windows:
                print(f"\nFound {len(all_chrome_windows)} Chrome window(s):")
                for i, chrome_title in enumerate(all_chrome_windows[:10], 1):  # Show first 10
                    print(f"  {i}. {chrome_title[:80]}")  # Truncate long titles
                if len(all_chrome_windows) > 10:
                    print(f"  ... and {len(all_chrome_windows) - 10} more")
            
            # Sort by priority (earlier keywords first)
            matches.sort(key=lambda x: x['priority'])
            
            # Show all matches and let user choose
            if matches:
                print(f"\n✓ Found {len(matches)} matching window(s):")
                for i, match in enumerate(matches, 1):
                    print(f"  {i}. {match['title'][:80]} ({match['owner']})")
                
                if len(matches) == 1:
                    # Only one match, return it (don't ask here)
                    best_match = matches[0]
                    bounds = best_match['bounds']
                    return (
                        int(bounds['X']),
                        int(bounds['Y']),
                        int(bounds['Width']),
                        int(bounds['Height'])
                    )
                else:
                    # Multiple matches, let user choose
                    choice = input(f"\nSelect window (1-{len(matches)}) or 0 to cancel: ").strip()
                    try:
                        idx = int(choice)
                        if idx == 0:
                            return None
                        elif 1 <= idx <= len(matches):
                            selected = matches[idx - 1]
                            bounds = selected['bounds']
                            return (
                                int(bounds['X']),
                                int(bounds['Y']),
                                int(bounds['Width']),
                                int(bounds['Height'])
                            )
                        else:
                            print("Invalid selection")
                            return None
                    except ValueError:
                        print("Invalid input")
                        return None
            
            print("\n✗ No matching windows found")
            return None
            
        except Exception as e:
            print(f"Error detecting window: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_full_screen_region(self):
        """Get the bounds of the main display"""
        bounds = CGDisplayBounds(CGMainDisplayID())
        return (
            int(bounds.origin.x),
            int(bounds.origin.y),
            int(bounds.size.width),
            int(bounds.size.height)
        )
    
    def frames_are_different(self, frame1, frame2):
        """
        Check if two frames are different enough to be considered a new slide
        
        Args:
            frame1: First frame (numpy array)
            frame2: Second frame (numpy array)
            
        Returns:
            Boolean indicating if frames are different
        """
        if frame1 is None or frame2 is None:
            return True
        
        if frame1.shape != frame2.shape:
            return True
        
        # Convert to grayscale for comparison
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate structural similarity
        difference = cv2.absdiff(gray1, gray2)
        diff_percentage = np.sum(difference) / (difference.size * 255)
        
        return diff_percentage > self.sensitivity
    
    def start_capture(self, region=None):
        """
        Start capturing slides
        
        Args:
            region: Tuple of (x, y, width, height) or None for full screen
        """
        if self.is_capturing:
            print("Already capturing!")
            return
        
        # Validate region exists
        if region is None:
            print("Error: No capture region specified!")
            return
        
        print(f"Capturing region: {region}")
        
        # Initialize screen capture
        capture = MacOSScreenCapture(region=region)
        
        # Generate timestamp for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.output_dir, f"session_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        
        self.is_capturing = True
        self.slides = []
        self.last_frame = None
        slide_count = 0
        
        print(f"Slide capture started!")
        print(f"Slides will be saved to: {session_dir}")
        print(f"Sensitivity: {self.sensitivity} (change threshold)")
        print(f"Check interval: {self.check_interval}s")
        print("Press Ctrl+C to stop and save PDF\n")
        
        try:
            while self.is_capturing:
                # Capture current frame
                frame = capture.capture_frame()
                
                if frame is not None:
                    # Check if this is a new slide
                    if self.frames_are_different(self.last_frame, frame):
                        slide_count += 1
                        slide_filename = os.path.join(session_dir, f"slide_{slide_count:03d}.png")
                        
                        # Save the slide
                        cv2.imwrite(slide_filename, frame)
                        self.slides.append(slide_filename)
                        
                        print(f"✓ Captured slide {slide_count}")
                        
                        # Update last frame
                        self.last_frame = frame.copy()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping capture...")
            self.stop_capture(session_dir, timestamp)
    
    def stop_capture(self, session_dir, timestamp):
        """Stop capturing and create PDF"""
        self.is_capturing = False
        
        if not self.slides:
            print("No slides captured!")
            return
        
        print(f"\nCaptured {len(self.slides)} slides")
        print("Creating PDF...")
        
        # Create PDF from slides
        pdf_filename = os.path.join(self.output_dir, f"slides_{timestamp}.pdf")
        
        try:
            # Load all images
            images = []
            for slide_path in self.slides:
                img = Image.open(slide_path)
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
            
            # Save as PDF
            if images:
                images[0].save(
                    pdf_filename,
                    save_all=True,
                    append_images=images[1:],
                    resolution=100.0,
                    quality=95
                )
                
                print(f"\n✓ PDF saved: {pdf_filename}")
                print(f"  Total slides: {len(self.slides)}")
                print(f"  Individual slides saved in: {session_dir}")
            
        except Exception as e:
            print(f"Error creating PDF: {e}")
            print(f"Individual slides are still available in: {session_dir}")


def main():
    """Main function"""
    print("macOS Slide Capture")
    print("=" * 50)
    
    # Get sensitivity setting
    print("\nSensitivity settings:")
    print("  Low (0.02)   - Captures even small changes")
    print("  Medium (0.05) - Balanced (recommended)")
    print("  High (0.10)  - Only major changes")
    
    sensitivity_input = input("Enter sensitivity (or press Enter for default 0.05): ").strip()
    sensitivity = float(sensitivity_input) if sensitivity_input else 0.05
    
    # Get check interval
    interval_input = input("Check interval in seconds (default 1.0): ").strip()
    check_interval = float(interval_input) if interval_input else 1.0
    
    capturer = SlideCapture(sensitivity=sensitivity, check_interval=check_interval)
    
    # Auto-detect window
    print("\nAttempting to auto-detect lecture window...")
    print("(Searching all windows, including those on other Spaces/Desktops)")
    
    # Search for Box URLs first, then other video sources
    keywords = ["u.app.box.com", "box.com", "Box", "YouTube", "Video", "Chrome", "Safari", "Firefox", "Zoom", "Google Meet", "Microsoft Teams", "Meeting"]
    region = capturer.auto_detect_window(keywords)
    
    # Track whether user explicitly declined
    user_declined = False
    
    # Check if region is valid (not None and not a tuple of Nones)
    if region is None:
        valid_region = False
    elif isinstance(region, tuple):
        valid_region = len(region) == 4 and None not in region and region != (None, None, None, None)
    else:
        valid_region = False
    
    print(f"\n[DEBUG] region={region}, valid_region={valid_region}")
    
    if valid_region:
        # Window was found, ask if they want to use it
        print(f"\nDetected window region: {region}")
        choice = input("Use this window? (y/n): ").strip().lower()
        if choice != 'y':
            region = None
            user_declined = True
            print("[DEBUG] User declined the window")
    else:
        # No valid window found
        region = None
        print("[DEBUG] No valid region found")
    
    # If no window found OR user declined, ask about full screen
    if region is None:
        print("\n" + "=" * 50)
        if user_declined:
            prompt = "Use full screen capture instead? (y/n): "
        else:
            prompt = "No window detected. Use full screen capture? (y/n): "
        
        choice = input(prompt).strip().lower()
        print(f"[DEBUG] User chose '{choice}' for full screen")
        
        if choice == 'y':
            print("Using full screen capture")
            region = capturer.get_full_screen_region()
        else:
            print("\n✗ Exiting - no capture region selected.")
            return  # Exit the main function
    
    # Double-check we have a valid region
    if region is None:
        print("✗ Error: No valid region. Exiting.")
        return
    
    print("\n" + "=" * 50)
    print("IMPORTANT: Make sure the video window stays visible!")
    print("The capture records what's visible on screen.")
    print("Tip: Switch to the Space/Desktop with your video before starting.")
    print("=" * 50 + "\n")
    
    time.sleep(2)
    
    capturer.start_capture(region=region)


if __name__ == "__main__":
    main()