# ESM Browser Extension Installation

## Chrome/Edge Installation:
1. Open Chrome/Edge and go to: chrome://extensions/ or edge://extensions/
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `browser-extension` folder
5. The extension will appear in your toolbar

## Firefox Installation:
1. Open Firefox and go to: about:debugging
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select any file in the `browser-extension` folder
5. The extension will appear in your toolbar

## Usage:
- The extension automatically captures conversations on supported sites
- Click the extension icon to see status and stats
- All conversations are automatically saved to your ESM system

## Supported Sites:
- ✅ Claude.ai
- ✅ ChatGPT web interface
- ✅ Google Bard
- ✅ Character.ai
- ✅ Poe.com
- ✅ Perplexity.ai

## Troubleshooting:
1. **Extension not working?**
   - Check if ESM system is running (http://localhost:8000/health)
   - Refresh the AI chat page
   - Check browser console for errors

2. **No conversations being captured?**
   - Ensure ESM system is accessible at localhost:8000
   - Check if the AI chat site is supported
   - Look for the extension icon showing green status

3. **Permission errors?**
   - The extension needs permissions for the AI chat sites
   - Click "Allow" when browser asks for permissions
   - Reload the extension if needed