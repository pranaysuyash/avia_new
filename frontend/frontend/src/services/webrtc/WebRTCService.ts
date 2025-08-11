/**
 * WebRTC Service for Real-time Collaboration
 * Handles peer-to-peer connections for collaborative editing
 */

import { EventEmitter } from 'events';

interface WebRTCConfig {
  iceServers: RTCIceServer[];
  signalingServerUrl: string;
}

interface PeerData {
  peerId: string;
  connection: RTCPeerConnection;
  dataChannel?: RTCDataChannel;
  metadata: {
    userId: string;
    userName: string;
    cursorColor: string;
  };
}

interface CollaborationMessage {
  type: 'cursor' | 'selection' | 'edit' | 'presence' | 'sync';
  userId: string;
  data: any;
  timestamp: number;
}

export class WebRTCService extends EventEmitter {
  private config: WebRTCConfig;
  private ws: WebSocket | null = null;
  private peers: Map<string, PeerData> = new Map();
  private localStream: MediaStream | null = null;
  private roomId: string | null = null;
  private userId: string;
  private userName: string;

  constructor(config: WebRTCConfig, userId: string, userName: string) {
    super();
    this.config = config;
    this.userId = userId;
    this.userName = userName;
  }

  /**
   * Connect to signaling server and join room
   */
  async joinRoom(roomId: string): Promise<void> {
    this.roomId = roomId;
    
    // Connect to signaling server
    this.ws = new WebSocket(this.config.signalingServerUrl);
    
    this.ws.onopen = () => {
      this.sendSignal({
        type: 'join',
        roomId,
        userId: this.userId,
        userName: this.userName,
      });
      this.emit('connected');
    };

    this.ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      await this.handleSignalingMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };

    this.ws.onclose = () => {
      this.emit('disconnected');
      this.cleanup();
    };
  }

  /**
   * Leave the current room
   */
  leaveRoom(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendSignal({
        type: 'leave',
        roomId: this.roomId,
        userId: this.userId,
      });
    }
    this.cleanup();
  }

  /**
   * Send collaboration message to all peers
   */
  broadcast(message: CollaborationMessage): void {
    const data = JSON.stringify(message);
    
    this.peers.forEach((peer) => {
      if (peer.dataChannel && peer.dataChannel.readyState === 'open') {
        peer.dataChannel.send(data);
      }
    });
  }

  /**
   * Send collaboration message to specific peer
   */
  sendToPeer(peerId: string, message: CollaborationMessage): void {
    const peer = this.peers.get(peerId);
    
    if (peer?.dataChannel && peer.dataChannel.readyState === 'open') {
      peer.dataChannel.send(JSON.stringify(message));
    }
  }

  /**
   * Handle signaling messages
   */
  private async handleSignalingMessage(message: any): Promise<void> {
    switch (message.type) {
      case 'user-joined':
        await this.handleUserJoined(message);
        break;
      
      case 'user-left':
        this.handleUserLeft(message);
        break;
      
      case 'offer':
        await this.handleOffer(message);
        break;
      
      case 'answer':
        await this.handleAnswer(message);
        break;
      
      case 'ice-candidate':
        await this.handleIceCandidate(message);
        break;
      
      case 'room-users':
        await this.handleRoomUsers(message);
        break;
    }
  }

  /**
   * Handle new user joining
   */
  private async handleUserJoined(message: any): Promise<void> {
    const { userId, userName } = message;
    
    if (userId === this.userId) return; // Skip self
    
    // Create offer for new peer
    const peer = await this.createPeerConnection(userId, userName);
    const offer = await peer.connection.createOffer();
    await peer.connection.setLocalDescription(offer);
    
    this.sendSignal({
      type: 'offer',
      to: userId,
      from: this.userId,
      offer: offer.sdp,
    });
  }

  /**
   * Handle user leaving
   */
  private handleUserLeft(message: any): void {
    const { userId } = message;
    const peer = this.peers.get(userId);
    
    if (peer) {
      peer.connection.close();
      this.peers.delete(userId);
      this.emit('peer-left', { userId });
    }
  }

  /**
   * Handle WebRTC offer
   */
  private async handleOffer(message: any): Promise<void> {
    const { from, offer } = message;
    
    const peer = await this.createPeerConnection(from, message.userName);
    
    await peer.connection.setRemoteDescription(
      new RTCSessionDescription({ type: 'offer', sdp: offer })
    );
    
    const answer = await peer.connection.createAnswer();
    await peer.connection.setLocalDescription(answer);
    
    this.sendSignal({
      type: 'answer',
      to: from,
      from: this.userId,
      answer: answer.sdp,
    });
  }

  /**
   * Handle WebRTC answer
   */
  private async handleAnswer(message: any): Promise<void> {
    const { from, answer } = message;
    const peer = this.peers.get(from);
    
    if (peer) {
      await peer.connection.setRemoteDescription(
        new RTCSessionDescription({ type: 'answer', sdp: answer })
      );
    }
  }

  /**
   * Handle ICE candidate
   */
  private async handleIceCandidate(message: any): Promise<void> {
    const { from, candidate } = message;
    const peer = this.peers.get(from);
    
    if (peer && candidate) {
      await peer.connection.addIceCandidate(new RTCIceCandidate(candidate));
    }
  }

  /**
   * Handle room users list
   */
  private async handleRoomUsers(message: any): Promise<void> {
    const { users } = message;
    
    // Create connections with all existing users
    for (const user of users) {
      if (user.userId !== this.userId && !this.peers.has(user.userId)) {
        await this.createPeerConnection(user.userId, user.userName);
      }
    }
  }

  /**
   * Create peer connection
   */
  private async createPeerConnection(peerId: string, userName: string): Promise<PeerData> {
    const connection = new RTCPeerConnection(this.config);
    
    // Create data channel
    const dataChannel = connection.createDataChannel('collaboration', {
      ordered: true,
    });
    
    const peerData: PeerData = {
      peerId,
      connection,
      dataChannel,
      metadata: {
        userId: peerId,
        userName,
        cursorColor: this.generateCursorColor(peerId),
      },
    };
    
    // Set up event handlers
    connection.onicecandidate = (event) => {
      if (event.candidate) {
        this.sendSignal({
          type: 'ice-candidate',
          to: peerId,
          from: this.userId,
          candidate: event.candidate,
        });
      }
    };
    
    connection.onconnectionstatechange = () => {
      if (connection.connectionState === 'connected') {
        this.emit('peer-connected', peerData.metadata);
      } else if (connection.connectionState === 'failed') {
        this.handleUserLeft({ userId: peerId });
      }
    };
    
    dataChannel.onopen = () => {
      this.emit('channel-open', { userId: peerId });
    };
    
    dataChannel.onmessage = (event) => {
      const message = JSON.parse(event.data) as CollaborationMessage;
      this.emit('message', message);
    };
    
    dataChannel.onerror = (error) => {
      console.error('Data channel error:', error);
    };
    
    // Handle incoming data channel
    connection.ondatachannel = (event) => {
      const channel = event.channel;
      peerData.dataChannel = channel;
      
      channel.onopen = () => {
        this.emit('channel-open', { userId: peerId });
      };
      
      channel.onmessage = (event) => {
        const message = JSON.parse(event.data) as CollaborationMessage;
        this.emit('message', message);
      };
    };
    
    this.peers.set(peerId, peerData);
    return peerData;
  }

  /**
   * Send signal through WebSocket
   */
  private sendSignal(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Generate unique cursor color for peer
   */
  private generateCursorColor(peerId: string): string {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
      '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
    ];
    
    const hash = peerId.split('').reduce((acc, char) => {
      return char.charCodeAt(0) + acc;
    }, 0);
    
    return colors[hash % colors.length];
  }

  /**
   * Cleanup connections
   */
  private cleanup(): void {
    this.peers.forEach((peer) => {
      peer.connection.close();
    });
    this.peers.clear();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
    
    this.roomId = null;
  }

  /**
   * Get connected peers
   */
  getConnectedPeers(): PeerData[] {
    return Array.from(this.peers.values()).filter(
      peer => peer.connection.connectionState === 'connected'
    );
  }

  /**
   * Get peer by ID
   */
  getPeer(peerId: string): PeerData | undefined {
    return this.peers.get(peerId);
  }
}