// Background script for ESM browser extension

chrome.runtime.onInstalled.addListener(() => {
    console.log('ESM Auto-Capture extension installed');
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'captureConversation') {
        // Forward to ESM API
        fetch('http://localhost:8000/capture/browser', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request.data)
        })
        .then(response => response.json())
        .then(data => {
            sendResponse({ success: true, data: data });
        })
        .catch(error => {
            sendResponse({ success: false, error: error.message });
        });
        
        return true; // Keep message channel open
    }
});