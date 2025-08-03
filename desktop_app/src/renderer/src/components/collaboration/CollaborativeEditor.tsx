import React, { useEffect, useRef, useState } from 'react';
import { useCollaboration } from './CollaborationProvider';
import CollaborativeCursors from './CollaborativeCursors';

interface CollaborativeEditorProps {
  initialContent: string;
  onChange?: (content: string) => void;
  readOnly?: boolean;
  className?: string;
}

interface TextSelection {
  start: number;
  end: number;
  text: string;
}

export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  initialContent,
  onChange,
  readOnly = false,
  className = ''
}) => {
  const { selections, activeUsers, updateSelection, sendChange, onReceiveChange } = useCollaboration();
  const [content, setContent] = useState(initialContent);
  const editorRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isComposing = useRef(false);
  const lastSelection = useRef<TextSelection | null>(null);

  // Handle incoming changes
  useEffect(() => {
    const unsubscribe = onReceiveChange((change) => {
      // Apply the change to our content
      if (change.type === 'insert') {
        setContent(prev => 
          prev.slice(0, change.position) + change.text + prev.slice(change.position)
        );
      } else if (change.type === 'delete') {
        setContent(prev => 
          prev.slice(0, change.position) + prev.slice(change.position + change.length)
        );
      } else if (change.type === 'replace') {
        setContent(change.content);
      }
    });

    return unsubscribe;
  }, [onReceiveChange]);

  // Handle selection changes
  useEffect(() => {
    const handleSelectionChange = () => {
      if (!editorRef.current || isComposing.current) return;

      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) return;

      const range = selection.getRangeAt(0);
      const preSelectionRange = range.cloneRange();
      preSelectionRange.selectNodeContents(editorRef.current);
      preSelectionRange.setEnd(range.startContainer, range.startOffset);
      const start = preSelectionRange.toString().length;

      const selectedText = range.toString();
      const end = start + selectedText.length;

      // Only update if selection actually changed
      if (lastSelection.current?.start !== start || lastSelection.current?.end !== end) {
        lastSelection.current = { start, end, text: selectedText };
        updateSelection({ start, end });
      }
    };

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, [updateSelection]);

  // Handle content changes
  const handleInput = (e: React.FormEvent<HTMLDivElement>) => {
    if (readOnly || isComposing.current) return;

    const newContent = e.currentTarget.innerText;
    const selection = window.getSelection();
    let cursorPosition = 0;

    if (selection && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const preSelectionRange = range.cloneRange();
      preSelectionRange.selectNodeContents(e.currentTarget);
      preSelectionRange.setEnd(range.startContainer, range.startOffset);
      cursorPosition = preSelectionRange.toString().length;
    }

    // Detect the type of change
    const oldContent = content;
    let change: any;

    if (newContent.length > oldContent.length) {
      // Text was inserted
      const insertedText = newContent.slice(cursorPosition - (newContent.length - oldContent.length), cursorPosition);
      change = {
        type: 'insert',
        position: cursorPosition - insertedText.length,
        text: insertedText
      };
    } else if (newContent.length < oldContent.length) {
      // Text was deleted
      change = {
        type: 'delete',
        position: cursorPosition,
        length: oldContent.length - newContent.length
      };
    } else {
      // Text was replaced
      change = {
        type: 'replace',
        content: newContent
      };
    }

    setContent(newContent);
    sendChange(change);
    
    if (onChange) {
      onChange(newContent);
    }
  };

  // Handle composition events (for IME input)
  const handleCompositionStart = () => {
    isComposing.current = true;
  };

  const handleCompositionEnd = () => {
    isComposing.current = false;
  };

  // Render other users' selections
  const renderSelections = () => {
    if (!editorRef.current) return null;

    return Array.from(selections.entries()).map(([userId, selection]) => {
      const user = activeUsers.find(u => u.id === userId);
      if (!user) return null;

      // Calculate the position of the selection
      const text = editorRef.current!.innerText;
      const beforeSelection = text.substring(0, selection.start);
      const selectedText = text.substring(selection.start, selection.end);
      
      if (!selectedText) return null;

      // Create highlight spans
      const lines = beforeSelection.split('\n');
      const startLine = lines.length - 1;
      const startOffset = lines[startLine].length;

      return (
        <div
          key={userId}
          className="absolute pointer-events-none"
          style={{
            backgroundColor: user.color + '30',
            border: `2px solid ${user.color}`,
            borderRadius: '2px'
          }}
        >
          <span className="text-xs text-white bg-opacity-90 px-1 py-0.5 rounded absolute -top-5 left-0 whitespace-nowrap"
            style={{ backgroundColor: user.color }}>
            {user.name}
          </span>
        </div>
      );
    });
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div
        ref={editorRef}
        contentEditable={!readOnly}
        onInput={handleInput}
        onCompositionStart={handleCompositionStart}
        onCompositionEnd={handleCompositionEnd}
        className="min-h-[200px] p-4 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500 whitespace-pre-wrap"
        suppressContentEditableWarning
      >
        {content}
      </div>
      
      {/* Render collaborative cursors */}
      <CollaborativeCursors containerRef={containerRef} />
      
      {/* Render selections */}
      {renderSelections()}
    </div>
  );
};

export default CollaborativeEditor;