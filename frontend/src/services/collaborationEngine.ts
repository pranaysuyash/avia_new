export interface CollaborationUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  isOnline: boolean;
  lastSeen: Date;
}

export interface CollaborationEvent {
  type: 'text_change' | 'cursor_move' | 'selection' | 'comment' | 'annotation';
  userId: string;
  timestamp: Date;
  data: any;
}

export class CollaborationEngine {
  private users: Map<string, CollaborationUser> = new Map();
  private events: CollaborationEvent[] = [];
  private callbacks: Map<string, Function[]> = new Map();
  
  constructor(documentId?: string, currentUser?: any) {
    // Constructor can accept parameters for compatibility
  }

  addUser(user: CollaborationUser): void {
    this.users.set(user.id, user);
    this.emit('user_joined', user);
  }

  removeUser(userId: string): void {
    const user = this.users.get(userId);
    if (user) {
      this.users.delete(userId);
      this.emit('user_left', user);
    }
  }

  updateUser(userId: string, updates: Partial<CollaborationUser>): void {
    const user = this.users.get(userId);
    if (user) {
      Object.assign(user, updates);
      this.emit('user_updated', user);
    }
  }

  getUsers(): CollaborationUser[] {
    return Array.from(this.users.values());
  }

  addEvent(event: CollaborationEvent): void {
    this.events.push(event);
    this.emit('event', event);
  }

  getEvents(): CollaborationEvent[] {
    return [...this.events];
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

  // Add methods expected by RealtimeCollaborationEditor
  async initialize(wsManager?: any): Promise<void> {
    // Initialize method for compatibility
  }

  cleanup(): void {
    // Cleanup method for compatibility
  }

  onContentChange(callback: (content: string) => void): void {
    this.on('content_changed', callback);
  }

  onLockChanged(callback: (locked: boolean, holderId?: string) => void): void {
    this.on('lock_changed', (data: { locked: boolean; holderId?: string }) => {
      callback(data.locked, data.holderId);
    });
  }

  applyChange(content: string): void {
    this.emit('content_changed', content);
  }

  acquireLock(): void {
    this.emit('lock_changed', { locked: true, holderId: 'current_user' });
  }

  releaseLock(): void {
    this.emit('lock_changed', { locked: false, holderId: null });
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.callbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }
}

export default new CollaborationEngine();