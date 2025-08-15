/**
 * Unified UI Components
 * Cross-platform accessible UI components
 * 
 * @fileoverview Exports unified UI components for all platforms
 * @version 1.0.0
 */

// Core UI components
export { FileUpload } from './FileUpload';

// Export types and interfaces
export type {
  UploadedFile
} from './FileUpload';

/**
 * Component Usage Examples:
 * 
 * File Upload:
 * ```tsx
 * import { FileUpload } from './components/ui';
 * 
 * <FileUpload
 *   accept="audio/*,video/*"
 *   multiple={true}
 *   maxFiles={5}
 *   maxSize={500 * 1024 * 1024} // 500MB
 *   onFileSelect={(files) => console.log('Selected:', files)}
 *   onUpload={async (file) => {
 *     // Upload implementation
 *     return { url: 'uploaded-url', id: 'file-id' };
 *   }}
 *   title="Upload Media Files"
 *   description="Drag and drop audio or video files"
 * />
 * ```
 * 
 * Compact File Upload:
 * ```tsx
 * <FileUpload
 *   variant="compact"
 *   accept="image/*"
 *   multiple={false}
 *   showPreview={true}
 *   autoUpload={true}
 * />
 * ```
 * 
 * Gallery File Upload:
 * ```tsx
 * <FileUpload
 *   variant="gallery"
 *   accept="image/*,video/*"
 *   showPreview={true}
 *   maxFiles={20}
 * />
 * ```
 */