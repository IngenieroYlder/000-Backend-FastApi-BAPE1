const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const app = express();
app.use(bodyParser.json());

const PORT = process.env.PORT || 3001;
const SESSION_DIR = path.join(__dirname, 'sessions');

// Store active socket connections
const sessions = new Map();

// Helper to delete folder recursively
const deleteFolderRecursive = (directoryPath) => {
    if (fs.existsSync(directoryPath)) {
        fs.readdirSync(directoryPath).forEach((file, index) => {
            const curPath = path.join(directoryPath, file);
            if (fs.lstatSync(curPath).isDirectory()) {
                deleteFolderRecursive(curPath);
            } else {
                fs.unlinkSync(curPath);
            }
        });
        fs.rmdirSync(directoryPath);
    }
};

async function startSession(sessionName, webhookUrl) {
    const sessionPath = path.join(SESSION_DIR, sessionName);
    
    // Create session dir if not exists (handled by useMultiFileAuthState but good to know)
    if (!fs.existsSync(sessionPath)) {
        fs.mkdirSync(sessionPath, { recursive: true });
    }

    const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
    const { version, isLatest } = await fetchLatestBaileysVersion();
    
    console.log(`Starting session ${sessionName} with version ${version.join('.')}`);

    const sock = makeWASocket({
        version,
        logger: require('pino')({ level: 'error' }),
        printQRInTerminal: false, // We will send QR to webhook or return in response
        auth: state,
        browser: ['BAPE', 'Chrome', '1.0.0']
    });

    // Save creds
    sock.ev.on('creds.update', saveCreds);

    // Connection updates
    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log(`QR Generated for ${sessionName}`);
            // Send QR to webhook
            if (webhookUrl) {
                try {
                    await axios.post(webhookUrl, { event: 'qr', session_name: sessionName, qr });
                } catch (err) {
                    console.error('Error sending QR webhook:', err.message);
                }
            }
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log(`Connection closed for ${sessionName}. Reconnecting: ${shouldReconnect}`);
            
            if (shouldReconnect) {
                startSession(sessionName, webhookUrl);
            } else {
                console.log(`Session ${sessionName} logged out.`);
                sessions.delete(sessionName);
                deleteFolderRecursive(sessionPath);
            }
        } else if (connection === 'open') {
            console.log(`Session ${sessionName} opened.`);
             if (webhookUrl) {
                try {
                    await axios.post(webhookUrl, { event: 'ready', session_name: sessionName });
                } catch (err) {
                   console.error('Error sending ready webhook:', err.message);
                }
            }
        }
    });

    // Messages
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        console.log(`[BAILEYS DEBUG] Received message upsert of type: ${type}. Message count: ${messages.length}`);
        if (messages.length > 0) {
            console.log(`[BAILEYS DEBUG] First msg fromMe: ${messages[0].key.fromMe}, remoteJid: ${messages[0].key.remoteJid}`);
        }
        if (type === 'notify') {
            for (const msg of messages) {
                if (!msg.key.fromMe && webhookUrl) {
                    try {
                        const messageType = msg.message ? Object.keys(msg.message)[0] : 'unknown';

                        let mediaPath = null;
                        // Check for Audio or Image
                        if (messageType === 'audioMessage' || messageType === 'imageMessage') {
                            const { downloadMediaMessage } = require('@whiskeysockets/baileys');
                            const buffer = await downloadMediaMessage(
                                msg,
                                'buffer',
                                {},
                                {
                                    logger: console,
                                    reuploadRequest: sock.updateMediaMessage
                                }
                            );

                            const folder = path.join(__dirname, 'media');
                            if (!fs.existsSync(folder)) {
                                fs.mkdirSync(folder, { recursive: true });
                            }

                            const ext = messageType === 'audioMessage' ? 'ogg' : 'jpg';
                            const fileName = `${msg.key.id}.${ext}`;
                            mediaPath = path.join(folder, fileName);
                            
                            fs.writeFileSync(mediaPath, buffer);
                            console.log(`Media saved to: ${mediaPath}`);
                        }

                        // Send Webhook with media_path
                        const payload = { 
                            event: 'message', 
                            session_name: sessionName, 
                            message: msg,
                            media_path: mediaPath 
                        };

                        await axios.post(webhookUrl, payload);
                    } catch (err) {
                        console.error('Error handling message/media:', err.message);
                    }
                }
            }
        }
    });

    sessions.set(sessionName, { sock, webhookUrl });
    return sock;
}

// Routes
app.post('/session/reset', async (req, res) => {
    const { session_name, webhook_url } = req.body;
    if (!session_name) return res.status(400).json({ error: 'session_name is required' });

    const session = sessions.get(session_name);
    const sessionPath = path.join(SESSION_DIR, session_name);

    // 1. Close socket if active
    if (session && session.sock) {
        try {
            session.sock.end();
            session.sock.logout(); // Attempt logout to clear session on servers?
        } catch (e) { console.error('Error closing socket:', e.message); }
    }
    
    sessions.delete(session_name);

    // 2. Delete Folder
    setTimeout(() => {
        try {
            deleteFolderRecursive(sessionPath);
            console.log(`Cleared path for ${sessionName}`);
        } catch (e) { console.error('Error deleting folder:', e.message); }

        // 3. Re-init if requested
        if (webhook_url) {
            startSession(session_name, webhook_url);
        }
    }, 1000);

    res.json({ message: 'Session reset started' });
});

app.post('/session/repair', async (req, res) => {
    const { session_name, webhook_url } = req.body;
    if (!session_name) return res.status(400).json({ error: 'session_name is required' });

    const session = sessions.get(session_name);
    const sessionPath = path.join(SESSION_DIR, session_name);

    // 1. Close socket if active
    if (session && session.sock) {
        try {
            session.sock.end();
            // We don't logout() here because we want to preserve the session on the server
        } catch (e) { console.error('Error closing socket:', e.message); }
    }
    
    sessions.delete(session_name);

    // 2. Delete all files EXCEPT creds.json
    setTimeout(() => {
        try {
            if (fs.existsSync(sessionPath)) {
                fs.readdirSync(sessionPath).forEach((file) => {
                    if (file !== 'creds.json') {
                        const curPath = path.join(sessionPath, file);
                        if (fs.lstatSync(curPath).isDirectory()) {
                            deleteFolderRecursive(curPath);
                        } else {
                            fs.unlinkSync(curPath);
                        }
                    }
                });
                console.log(`Repaired (soft reset) path for ${session_name}`);
            }
        } catch (e) { console.error('Error repairing folder:', e.message); }

        // 3. Re-init if requested
        if (webhook_url) {
            startSession(session_name, webhook_url);
        }
    }, 1000);

    res.json({ message: 'Session repair started' });
});

app.post('/session/init', async (req, res) => {
    const { session_name, webhook_url } = req.body;
    if (!session_name) return res.status(400).json({ error: 'session_name is required' });

    if (sessions.has(session_name)) {
        return res.json({ message: 'Session already active', status: 'active' });
    }

    try {
        await startSession(session_name, webhook_url);
        res.json({ message: 'Session initialization started', status: 'initializing' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to start session' });
    }
});

app.post('/message/send', async (req, res) => {
    const { session_name, jid, message } = req.body;
    const session = sessions.get(session_name);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        await session.sock.sendMessage(jid, message);
        res.json({ status: 'sent' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to send message' });
    }
});

app.post('/message/read', async (req, res) => {
    const { session_name, jid, message_key } = req.body;
    const session = sessions.get(session_name);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        // Mark as read
        await session.sock.readMessages([message_key]);
        res.json({ status: 'read' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to mark as read' });
    }
});

app.post('/session/presence', async (req, res) => {
    const { session_name, jid, presence } = req.body; // presence: 'composing' | 'paused' | 'available'
    const session = sessions.get(session_name);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        await session.sock.sendPresenceUpdate(presence, jid);
        res.json({ status: 'updated' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to update presence' });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok', active_sessions: sessions.size });
});

// Start server
app.listen(PORT, () => {
    console.log(`Baileys Engine running on port ${PORT}`);
});
