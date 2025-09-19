

# Advanced Bloatware Remover

This tool, developed using Python and Tkinter, is a desktop application that allows you to easily manage unwanted applications (bloatware) on Android devices. By using ADB (Android Debug Bridge) commands through a graphical user interface, it enables even users with limited technical knowledge to safely clean their devices.

## ✨ Features

  * **Automatic Bloatware Detection:** Automatically lists potentially unwanted software by comparing installed applications on the device with a known bloatware database (`uad_lists.json`).
  * **Detailed Information Display:** Provides detailed information for each listed application, including package name, description, and safety level (`Recommended`, `Advanced`, `Expert`, `Unsafe`).
  * **Color-Coded Safety Levels:** Visually alerts the user by color-coding applications based on their risk level (Green, Orange, Red).
  * **Safe Uninstallation and Restoration:**
      * Disables applications for the current user (`uninstall --user 0`) instead of completely removing them from the system. This allows applications to be restored upon a factory reset.
      * Provides the ability to easily restore accidentally uninstalled applications from the "Restore" tab.
  * **Session History (Logging):** Every uninstall operation is automatically saved with a timestamp to a separate file in the `uninstall_logs` folder.
  * **Restore from History:** The "Uninstall History" feature allows viewing past uninstall sessions and selecting applications from these logs to add to the restore list.
  * **User-Friendly Interface:**
      * Real-time search/filter bar.
      * "Auto-Select" menu to bulk-select applications based on their safety level.
      * Column sorting by clicking on headers.
      * Informational tooltips for long descriptions on mouse hover.
  * **Device Management Tools:** An integrated "Reboot" menu to restart the device in Normal, Recovery, Bootloader, or Download modes.
  * **Tiered Safety Confirmations:** Minimizes user error by displaying different warning messages based on the risk level of the applications being uninstalled.
  * **Single File `.exe`:** Can be packaged as a single executable file, including all dependencies (`platform-tools`, database).

## 🚀 How to Use

### Requirements

  * A Windows PC.
  * An Android device (Android 5.0+).
  * A USB cable suitable for the device.

### Step 1: Prepare Your Phone

1.  **Enable Developer Options:** On your phone, go to **Settings \> About Phone** and tap on the **"Build Number"** 7-8 times consecutively.
2.  **Enable USB Debugging:** Return to the main Settings menu, go to **Developer Options**, and enable the **"USB Debugging"** option.

### Step 2: Run the Application

1.  Connect your phone to your computer with the USB cable. If a prompt like "Allow this computer?" appears on your screen, check "Always allow" and confirm.
2.  Double-click the `remover.exe` file to run the program.
3.  The program will display a disclaimer on the first launch. After you agree, the main interface will open.
4.  Click the "Scan for Bloatware" button to list the unwanted applications on your device and start managing them.

## 🛠️ For Developers: Building from Source (`.exe` Creation)

If you wish to compile this project yourself:

1.  Ensure you have Python 3 installed on your computer.
2.  Install the required package, `pyinstaller`:
    ```bash
    pip install pyinstaller
    ```
3.  Make sure the project files are structured as follows:
    ```
    /BW_REMOVE
    ├── platform-tools/
    ├── remover.py
    └── uad_lists.json
    ```
4.  Open a Command Prompt (CMD) in the project's root directory (`BW_REMOVE`) and run the following command:
    ```bash
    pyinstaller --noconsole --onefile --add-data "platform-tools;platform-tools" --add-data "uad_lists.json;." remover.py
    ```
5.  Once the process is complete, the executable `remover.exe` will be ready in the `dist` folder.

## ⚠️ Disclaimer

This tool is provided "as is" for educational and personal use. The developer assumes NO responsibility for any damage to your device, including but not limited to, bricking, bootloops, or loss of data. Incorrectly uninstalling system applications can lead to severe system instability. You are using this tool at YOUR OWN RISK.

## 🙏 Acknowledgements

The bloatware list in this project is sourced from the `uad_lists.json` file of the [**Universal Android Debloater**](https://github.com/0x192/universal-android-debloater) project. We thank them for creating this valuable database.

## 📄 License

This project is licensed under the [License Name, e.g., MIT License]. See the `LICENSE` file for more details.
