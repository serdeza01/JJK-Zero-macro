# Jujutsu Zero Macro (Windows & Mac)

A powerful, customizable automation tool for Jujutsu Zero. This tool features a **Macro Recorder** to record your own specific movements and a **Legacy Auto-Mode** for automated image detection.

It works on **Windows** (via standalone Executable) and **macOS** (via Python/Terminal).

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20MacOS-lightgrey.svg)

## 📥 Download

### Windows Users
You do **not** need to install Python.
1. Go to the **[Releases](https://github.com/serdeza01/Macro-JJK-V2/releases)** page on this repository.
2. Download the latest `Jujutsu_Manager.exe`.
3. Place it in a folder on your Desktop.

### Mac Users
You will run the script directly from the source code. See the [Mac Installation Guide](#-mac-installation-guide) below.

---

## 🖥️ Windows Guide

### Method 1: The Executable (Recommended)
1. Run `Jujutsu_Manager.exe`.
2. A folder named `saved_macros` will be created automatically.
3. **Manager Mode (Recorder):**
   - Click "Record" (or press **P**).
   - Perform your fight sequence.
   - Press **P** again to stop.
   - Name your macro and click **Save**.
   - Select it from the list and press **M** to loop it.
4. **Legacy Mode (Image Detection):**
   - If you want to use the automatic "Legacy Mode" (which looks for images on screen), you must take a screenshot of the "Retry" button or the specific game element you want to click.
   - Name the image exactly `image{WIDTH}x{HEIGHT}.png` matching your screen resolution.
     - *Example:* If your screen is 1920x1080, name the file `image1920x1080.png`.
   - Place this image in the **same folder** as the `.exe`.

---

## 🍎 Mac Installation Guide

Due to macOS security restrictions, you must run this tool via VS Code or Terminal to grant it proper accessibility permissions.

### Prerequisites
1. **Install Python 3**: [Download Here](https://www.python.org/downloads/)
2. **Install VS Code** (Recommended): [Download Here](https://code.visualstudio.com/)

### Step 1: Install Dependencies
Open your Terminal (or VS Code Terminal) and run:
```bash
pip3 install pyautogui pynput