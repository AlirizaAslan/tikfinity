class GlobalTTSClient {
    constructor() {
        this.socket = null;
        this.username = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    connect(username) {
        if (this.socket && this.username === username && this.isConnected) {
            console.log('Already connected to', username);
            return;
        }

        this.username = username;
        setStoredUsername(username); // Store username for persistence
        this.disconnect();

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/live/${username}/`;
        
        console.log('Connecting to TikTok Live:', wsUrl);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('✅ Connected to TikTok Live:', username);
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.showStatus('WebSocket connected to @' + username, 'success');
            
            // Dispatch custom event for other parts of the page
            window.dispatchEvent(new CustomEvent('ttsConnectionChanged', {
                detail: { connected: true, username: username }
            }));
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            this.handleMessage(data);
        };

        this.socket.onclose = () => {
            console.log('❌ Disconnected from TikTok Live');
            this.isConnected = false;
            
            // Dispatch custom event for other parts of the page
            window.dispatchEvent(new CustomEvent('ttsConnectionChanged', {
                detail: { connected: false, username: this.username }
            }));
            
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showStatus('Connection error', 'error');
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.isConnected = false;
    }

    handleMessage(data) {
        console.log('Received message:', data);

        switch (data.type) {
            case 'connection':
                if (data.status === 'tiktok_connected') {
                    this.showStatus('Connected to TikTok @' + data.username, 'success');
                } else {
                    this.showStatus(data.message, 'info');
                }
                break;
            case 'comment':
                this.handleComment(data);
                break;
            case 'tts':
                console.log('TTS message received:', data);
                this.playTTS(data);
                break;
            case 'error':
                this.showStatus(data.message, 'error');
                break;
        }
    }

    handleComment(data) {
        console.log('💬 Comment:', data.username, '-', data.message);
        // Comment will be processed for TTS automatically by the server
    }

    playTTS(data) {
        console.log('🔊 Playing TTS:', data.text, 'URL:', data.audio_url);
        if (data.audio_url) {
            const audio = new Audio(data.audio_url);
            audio.volume = this.getTTSVolume();
            
            audio.onloadstart = () => console.log('TTS audio loading started');
            audio.oncanplay = () => console.log('TTS audio can play');
            audio.onplay = () => console.log('TTS audio started playing');
            audio.onended = () => console.log('TTS audio finished playing');
            audio.onerror = (e) => console.error('TTS audio error:', e);
            
            audio.play().then(() => {
                console.log('TTS audio playback started successfully');
            }).catch(e => {
                console.error('TTS playback failed:', e);
                console.log('Try clicking on the page to enable audio autoplay');
            });
        }
    }

    getTTSVolume() {
        // Try to get volume from TTS settings page if available
        const volumeSlider = document.getElementById('volume');
        if (volumeSlider) {
            return volumeSlider.value / 100;
        }
        return 1.0; // Default volume
    }

    showStatus(message, type) {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Show status in UI if status element exists
        const statusEl = document.getElementById('tts-status');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = `status ${type}`;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts && this.username) {
            this.reconnectAttempts++;
            console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.connect(this.username);
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }
}

// Global instance
window.globalTTS = new GlobalTTSClient();

// Auto-connect if username is available
document.addEventListener('DOMContentLoaded', function() {
    // Try to get username from various sources
    const username = getStoredUsername();
    if (username) {
        console.log('Auto-connecting to stored username:', username);
        window.globalTTS.connect(username);
    } else {
        console.log('No stored username found for auto-connect');
    }
});

function getStoredUsername() {
    // Try localStorage first
    let username = localStorage.getItem('tiktok_username');
    if (username) return username;
    
    // Try sessionStorage
    username = sessionStorage.getItem('tiktok_username');
    if (username) return username;
    
    // Try to extract from current page
    const urlMatch = window.location.pathname.match(/live\/([^\/]+)/);
    if (urlMatch) return urlMatch[1];
    
    return null;
}

// Store username when connecting
function setStoredUsername(username) {
    localStorage.setItem('tiktok_username', username);
    sessionStorage.setItem('tiktok_username', username);
}