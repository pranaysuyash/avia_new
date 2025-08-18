export interface Annotation {
  id: string;
  type: 'highlight' | 'comment' | 'note' | 'correction' | 'question' | 'medical_term' | 'warning';
  startOffset: number;
  endOffset: number;
  text: string;
  content: string;
  authorId: string;
  authorName: string;
  timestamp: Date;
  replies?: AnnotationReply[];
  metadata?: any;
  isResolved?: boolean;
}

export interface AnnotationReply {
  id: string;
  content: string;
  authorId: string;
  authorName: string;
  timestamp: Date;
}

export interface AnnotationFilter {
  type?: string;
  authorId?: string;
  isResolved?: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export class AnnotationEngine {
  private annotations: Map<string, Annotation> = new Map();
  private callbacks: Map<string, Function[]> = new Map();
  
  constructor(documentId?: string, currentUser?: any) {
    // Constructor can accept parameters for compatibility
  }

  addAnnotation(annotation: Omit<Annotation, 'id' | 'timestamp'>): string {
    const id = this.generateId();
    const newAnnotation: Annotation = {
      ...annotation,
      id,
      timestamp: new Date(),
      replies: []
    };

    this.annotations.set(id, newAnnotation);
    this.emit('annotation_added', newAnnotation);
    return id;
  }

  updateAnnotation(id: string, updates: Partial<Annotation>): boolean {
    const annotation = this.annotations.get(id);
    if (!annotation) {
      return false;
    }

    Object.assign(annotation, updates);
    this.emit('annotation_updated', annotation);
    return true;
  }

  deleteAnnotation(id: string): boolean {
    const annotation = this.annotations.get(id);
    if (!annotation) {
      return false;
    }

    this.annotations.delete(id);
    this.emit('annotation_deleted', annotation);
    return true;
  }

  getAnnotation(id: string): Annotation | undefined {
    return this.annotations.get(id);
  }

  getAnnotations(filter?: AnnotationFilter): Annotation[] {
    let annotations = Array.from(this.annotations.values());

    if (filter) {
      if (filter.type) {
        annotations = annotations.filter(a => a.type === filter.type);
      }
      if (filter.authorId) {
        annotations = annotations.filter(a => a.authorId === filter.authorId);
      }
      if (filter.isResolved !== undefined) {
        annotations = annotations.filter(a => a.isResolved === filter.isResolved);
      }
      if (filter.dateRange) {
        annotations = annotations.filter(a => 
          a.timestamp >= filter.dateRange!.start && 
          a.timestamp <= filter.dateRange!.end
        );
      }
    }

    return annotations.sort((a, b) => a.startOffset - b.startOffset);
  }

  getAnnotationsInRange(startOffset: number, endOffset: number): Annotation[] {
    return Array.from(this.annotations.values()).filter(annotation => {
      return !(annotation.endOffset < startOffset || annotation.startOffset > endOffset);
    });
  }

  addReply(annotationId: string, reply: Omit<AnnotationReply, 'id' | 'timestamp'>): string | null {
    const annotation = this.annotations.get(annotationId);
    if (!annotation) {
      return null;
    }

    const replyId = this.generateId();
    const newReply: AnnotationReply = {
      ...reply,
      id: replyId,
      timestamp: new Date()
    };

    if (!annotation.replies) {
      annotation.replies = [];
    }
    annotation.replies.push(newReply);

    this.emit('reply_added', { annotation, reply: newReply });
    return replyId;
  }

  resolveAnnotation(id: string): boolean {
    return this.updateAnnotation(id, { isResolved: true });
  }

  unresolveAnnotation(id: string): boolean {
    return this.updateAnnotation(id, { isResolved: false });
  }

  exportAnnotations(format: 'json' | 'csv' | 'xml' = 'json'): string {
    const annotations = this.getAnnotations();
    
    switch (format) {
      case 'json':
        return JSON.stringify(annotations, null, 2);
      case 'csv':
        const headers = ['ID', 'Type', 'Start', 'End', 'Text', 'Content', 'Author', 'Timestamp', 'Resolved'];
        const rows = annotations.map(a => [
          a.id,
          a.type,
          a.startOffset,
          a.endOffset,
          a.text.replace(/"/g, '""'),
          a.content.replace(/"/g, '""'),
          a.authorName,
          a.timestamp.toISOString(),
          a.isResolved || false
        ]);
        return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      case 'xml':
        const xmlAnnotations = annotations.map(a => 
          `<annotation id="${a.id}" type="${a.type}" start="${a.startOffset}" end="${a.endOffset}" resolved="${a.isResolved || false}">
            <text>${this.escapeXml(a.text)}</text>
            <content>${this.escapeXml(a.content)}</content>
            <author>${this.escapeXml(a.authorName)}</author>
            <timestamp>${a.timestamp.toISOString()}</timestamp>
          </annotation>`
        ).join('\n');
        return `<?xml version="1.0" encoding="UTF-8"?>\n<annotations>\n${xmlAnnotations}\n</annotations>`;
      default:
        return JSON.stringify(annotations, null, 2);
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

  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  private escapeXml(text: string): string {
    return text.replace(/[<>&'"]/g, (char) => {
      switch (char) {
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '&': return '&amp;';
        case "'": return '&apos;';
        case '"': return '&quot;';
        default: return char;
      }
    });
  }

  // Add methods expected by RealtimeCollaborationEditor
  async initialize(wsManager?: any): Promise<void> {
    // Initialize method for compatibility
  }

  cleanup(): void {
    // Cleanup method for compatibility
  }

  onCommentAdded(callback: (comment: any) => void): void {
    this.on('comment_added', callback);
  }

  onCommentResolved(callback: (commentId: string) => void): void {
    this.on('comment_resolved', callback);
  }

  onAnnotationAdded(callback: (annotation: any) => void): void {
    this.on('annotation_added', callback);
  }

  addComment(comment: any): void {
    const id = this.addAnnotation({
      type: 'comment',
      startOffset: comment.position?.line || 0,
      endOffset: comment.position?.column || 0,
      text: comment.text,
      content: comment.text,
      authorId: comment.userId,
      authorName: 'User',
      isResolved: comment.resolved
    });
    this.emit('comment_added', { ...comment, id });
  }

  resolveComment(commentId: string): void {
    this.updateAnnotation(commentId, { isResolved: true });
    this.emit('comment_resolved', commentId);
  }
}

export default new AnnotationEngine();