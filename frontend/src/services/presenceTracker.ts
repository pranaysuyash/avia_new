export interface UserPresence {
  userId: string;
  userName: string;
  isActive: boolean;
  lastActivity: Date;
  currentSection?: string;
  cursorPosition?: number;
  selectedText?: string;
  status: 'online' | 'away' | 'busy' | 'offline';
}

export interface PresenceEvent {
  type: 'activity' | 'status_change' | 'cursor_move' | 'section_change';
  userId: string;
  timestamp: Date;
  data: any;
}

export class PresenceTracker {
  private presences: Map<string, UserPresence> = new Map();
  private callbacks: Map<string, Function[]> = new Map();
  private activityTimeout: number = 30000; // 30 seconds
  
  constructor(documentId?: string, currentUser?: any) {
    // Constructor can accept parameters for compatibility
  }

  updatePresence(userId: string, updates: Partial<UserPresence>): void {
    const current = this.presences.get(userId) || {
      userId,
      userName: `User ${userId}`,
      isActive: true,
      lastActivity: new Date(),
      status: 'online'
    };

    const updated = {
      ...current,
      ...updates,
      lastActivity: new Date()
    };

    this.presences.set(userId, updated);
    this.emit('presence_updated', updated);
  }

  setUserActivity(userId: string, isActive: boolean): void {
    this.updatePresence(userId, { 
      isActive, 
      lastActivity: new Date(),
      status: isActive ? 'online' : 'away'
    });
  }

  setUserStatus(userId: string, status: UserPresence['status']): void {
    this.updatePresence(userId, { status });
  }

  setCursorPosition(userId: string, position: number): void {
    this.updatePresence(userId, { cursorPosition: position });
    this.emit('cursor_moved', { userId, position });
  }

  setSelectedText(userId: string, text: string): void {
    this.updatePresence(userId, { selectedText: text });
    this.emit('text_selected', { userId, text });
  }

  setCurrentSection(userId: string, section: string): void {
    this.updatePresence(userId, { currentSection: section });
    this.emit('section_changed', { userId, section });
  }

  getUserPresence(userId: string): UserPresence | undefined {
    return this.presences.get(userId);
  }

  getAllPresences(): UserPresence[] {
    return Array.from(this.presences.values());
  }

  getActiveUsers(): UserPresence[] {
    const now = new Date();
    return Array.from(this.presences.values()).filter(presence => {
      const timeSinceLastActivity = now.getTime() - presence.lastActivity.getTime();
      return timeSinceLastActivity < this.activityTimeout && presence.status !== 'offline';
    });
  }

  removeUser(userId: string): void {
    const presence = this.presences.get(userId);
    if (presence) {
      this.presences.delete(userId);
      this.emit('user_left', presence);
    }
  }

  startActivityTracking(): void {
    setInterval(() => {
      const now = new Date();
      this.presences.forEach((presence, userId) => {
        const timeSinceLastActivity = now.getTime() - presence.lastActivity.getTime();
        if (timeSinceLastActivity > this.activityTimeout && presence.isActive) {
          this.updatePresence(userId, { 
            isActive: false, 
            status: 'away' 
          });
        }
      });
    }, 10000); // Check every 10 seconds
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
    this.startActivityTracking();
  }

  cleanup(): void {
    // Cleanup method for compatibility
  }

  onUserJoin(callback: (user: any) => void): void {
    this.on('user_joined', callback);
  }

  onUserLeave(callback: (userId: string) => void): void {
    this.on('user_left', callback);
  }

  onUserActivity(callback: (userId: string, activity: any) => void): void {
    this.on('presence_updated', (presence: UserPresence) => {
      callback(presence.userId, {
        isTyping: presence.isActive,
        cursor: { line: 0, column: presence.cursorPosition || 0 }
      });
    });
  }

  updateCursorPosition(position: number): void {
    // Method for updating cursor position
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.callbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }
}

export default new PresenceTracker();