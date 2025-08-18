export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: Map<string, Function[]> = new Map();

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          this.emit('connected');
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        };
        
        this.ws.onclose = () => {
          this.emit('disconnected');
        };
        
        this.ws.onerror = (error) => {
          this.emit('error', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(type: string, payload: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  on(event: string, callback: Function): void {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, []);
    }
    this.callbacks.get(event)!.push(callback);
  }

  off(event: string, callback: Function): void {
    const callbacks = this.callbacks.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.callbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  // Add methods expected by RealtimeCollaborationEditor
  onConnectionChange(callback: (status: 'connecting' | 'connected' | 'disconnected') => void): void {
    this.on('connected', () => callback('connected'));
    this.on('disconnected', () => callback('disconnected'));
    this.on('error', () => callback('disconnected'));
  }
}

export default new WebSocketManager(import.meta.env.VITE_WS_URL || 'ws://localhost:8001');