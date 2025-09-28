document.addEventListener('DOMContentLoaded', async () => {
    const statusDiv = document.getElementById('status');
    const todayCountSpan = document.getElementById('todayCount');
    const totalCountSpan = document.getElementById('totalCount');
    const currentSiteSpan = document.getElementById('currentSite');
    
    // Check ESM connection
    try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
            statusDiv.textContent = '✅ ESM Connected';
            statusDiv.className = 'status active';
        } else {
            throw new Error('ESM not responding');
        }
    } catch (error) {
        statusDiv.textContent = '❌ ESM Disconnected';
        statusDiv.className = 'status inactive';
    }
    
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const hostname = new URL(tab.url).hostname;
    
    let siteName = 'Unknown';
    if (hostname.includes('claude.ai')) siteName = 'Claude';
    else if (hostname.includes('chat.openai.com')) siteName = 'ChatGPT';
    else if (hostname.includes('bard.google.com')) siteName = 'Bard';
    else if (hostname.includes('character.ai')) siteName = 'Character.AI';
    else if (hostname.includes('poe.com')) siteName = 'Poe';
    else if (hostname.includes('perplexity.ai')) siteName = 'Perplexity';
    
    currentSiteSpan.textContent = siteName;
    
    // Get capture stats
    try {
        const response = await fetch('http://localhost:8000/capture/stats/total');
        const stats = await response.json();
        todayCountSpan.textContent = stats.today_count || 0;
        totalCountSpan.textContent = stats.total_count || 0;
    } catch (error) {
        todayCountSpan.textContent = 'Error';
        totalCountSpan.textContent = 'Error';
    }
    
    // Button handlers
    document.getElementById('toggleCapture').addEventListener('click', () => {
        chrome.tabs.sendMessage(tab.id, { action: 'toggleCapture' });
    });
    
    document.getElementById('openESM').addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:3000' });
    });
    
    document.getElementById('testConnection').addEventListener('click', async () => {
        try {
            const response = await fetch('http://localhost:8000/health');
            if (response.ok) {
                alert('✅ Connection successful!');
            } else {
                alert('❌ Connection failed!');
            }
        } catch (error) {
            alert('❌ Connection error: ' + error.message);
        }
    });
});