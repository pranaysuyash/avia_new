/**
 * Collaborative Workspace Component for Electron Desktop App
 * Enhanced with native desktop features, keyboard shortcuts, and medical schema integration
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  AvatarGroup,
  Chip,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Divider,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Grid,
  Tabs,
  Tab,
  Popper,
  ClickAwayListener,
  Grow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Breadcrumbs,
  Link,
  Fab
} from '@mui/material';
import {
  Edit as EditIcon,
  People as PeopleIcon,
  Comment as CommentIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  PersonAdd as PersonAddIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Share as ShareIcon,
  Save as SaveIcon,
  Sync as SyncIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  MoreVert as MoreVertIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  PictureInPicture as PictureInPictureIcon,
  ScreenShare as ScreenShareIcon,
  RecordVoiceOver as RecordVoiceOverIcon,
  Chat as ChatIcon,
  VideoCall as VideoCallIcon,
  Phone as PhoneIcon,
  FileDownload as FileDownloadIcon,
  FileUpload as FileUploadIcon,
  CloudSync as CloudSyncIcon,
  ExpandMore as ExpandMoreIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  FitScreen as FitScreenIcon,
  GridView as GridViewIcon,
  ViewColumn as ViewColumnIcon,
  Dashboard as DashboardIcon,
  MedicalServices as MedicalServicesIcon,
  Assignment as AssignmentIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useHotkeys } from 'react-hotkeys-hook';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { DesktopCollaborationEngine } from '../../services/desktopCollaborationEngine';
import { NativeIntegrations } from '../../services/nativeIntegrations';
import { MedicalSchemaValidator } from '../../services/medicalSchemaValidator';
import { PresenceAwareness } from '../../services/presenceAwareness';
import { VoiceCommunication } from '../../services/voiceCommunication';
import { ScreenSharingManager } from '../../services/screenSharingManager';

// Enhanced desktop-specific styling
const DesktopWorkspace = styled(Paper)(({ theme }) => ({
  height: '100vh',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: theme.palette.background.default,
  borderRadius: 0,
  overflow: 'hidden',
  position: 'relative'
}));

const WorkspaceHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1, 2),
  borderBottom: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  backgroundColor: theme.palette.background.paper,
  minHeight: '64px',
  zIndex: 1000
}));

const WorkspaceMain = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  overflow: 'hidden',
  position: 'relative'
}));

const EditorPanel = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: theme.palette.background.paper,
  position: 'relative'
}));

const SidePanel = styled(Box)(({ theme, width = 320 }) => ({
  width: width,
  backgroundColor: theme.palette.background.default,
  borderLeft: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  flexDirection: 'column',
  transition: 'width 0.3s ease'
}));

const FloatingToolbar = styled(Paper)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(2),
  right: theme.spacing(2),
  padding: theme.spacing(1),
  display: 'flex',
  gap: theme.spacing(1),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.spacing(3),
  boxShadow: theme.shadows[8],
  zIndex: 1100
}));

const PresenceCursor = styled(Box)(({ theme, color }) => ({
  position: 'absolute',
  width: '2px',
  height: '20px',
  backgroundColor: color || theme.palette.primary.main,
  zIndex: 999,
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '-4px',
    left: '-4px',
    width: '10px',
    height: '10px',
    backgroundColor: color || theme.palette.primary.main,
    borderRadius: '50%'
  }
}));

const MedicalValidationPanel = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.spacing(1),
  margin: theme.spacing(1),
  border: `1px solid ${theme.palette.divider}`
}));

const ZoomControls = styled(Box)(({ theme }) => ({
  position: 'absolute',
  bottom: theme.spacing(2),
  left: theme.spacing(2),
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.spacing(3),
  padding: theme.spacing(1),
  boxShadow: theme.shadows[4],
  zIndex: 1000
}));

// Types
interface CollaborationUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'owner' | 'editor' | 'reviewer' | 'viewer' | 'medical_professional';
  color: string;
  isOnline: boolean;
  isTyping: boolean;
  isScreenSharing: boolean;
  isInVoiceChat: boolean;
  cursor?: { x: number; y: number; line: number; column: number };
  selection?: { start: number; end: number };
  lastActivity: Date;
  nativeStatus: {
    platform: string;
    version: string;
    capabilities: string[];
  };
}

interface MedicalValidation {
  isValid: boolean;
  errors: Array<{
    type: 'terminology' | 'format' | 'completeness' | 'consistency';
    message: string;
    line: number;
    column: number;
    severity: 'error' | 'warning' | 'info';
    suggestions: string[];
  }>;
  completeness: number;
  accuracy: number;
  medicalTermCount: number;
}

interface Props {
  documentId: string;
  initialContent?: string;
  readOnly?: boolean;
  enableMedicalValidation?: boolean;
  enableVoiceChat?: boolean;
  enableScreenSharing?: boolean;
  currentUser: CollaborationUser;
  onSave?: (content: string) => void;
  onError?: (error: Error) => void;
}

const CollaborativeWorkspace: React.FC<Props> = ({
  documentId,
  initialContent = '',
  readOnly = false,
  enableMedicalValidation = true,
  enableVoiceChat = false,
  enableScreenSharing = false,
  currentUser,
  onSave,
  onError
}) => {
  // State management
  const [content, setContent] = useState(initialContent);
  const [users, setUsers] = useState<CollaborationUser[]>([currentUser]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'syncing'>('connecting');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPictureInPicture, setIsPictureInPicture] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [showSidePanel, setShowSidePanel] = useState(true);
  const [sidePanelWidth, setSidePanelWidth] = useState(320);
  const [selectedTab, setSelectedTab] = useState(0);
  const [medicalValidation, setMedicalValidation] = useState<MedicalValidation | null>(null);
  
  // Dialog states
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [showMedicalPanel, setShowMedicalPanel] = useState(enableMedicalValidation);
  const [showPresencePanel, setShowPresencePanel] = useState(true);
  
  // Voice and screen sharing states
  const [isVoiceChatActive, setIsVoiceChatActive] = useState(false);
  const [isSharingScreen, setIsSharingScreen] = useState(false);
  const [viewingSharedScreen, setViewingSharedScreen] = useState<string | null>(null);
  
  // Persistent settings
  const [workspaceSettings, setWorkspaceSettings] = useLocalStorage('workspace-settings', {
    theme: 'system',
    fontSize: 14,
    lineHeight: 1.5,
    showLineNumbers: true,
    enableAutoSave: true,
    autoSaveInterval: 30,
    soundEnabled: true,
    notificationsEnabled: true,
    medicalValidationEnabled: true
  });
  
  // Refs
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);
  const collaborationEngineRef = useRef<DesktopCollaborationEngine | null>(null);
  const nativeIntegrationsRef = useRef<NativeIntegrations | null>(null);
  const medicalValidatorRef = useRef<MedicalSchemaValidator | null>(null);
  const presenceAwarenessRef = useRef<PresenceAwareness | null>(null);
  const voiceCommunicationRef = useRef<VoiceCommunication | null>(null);
  const screenSharingRef = useRef<ScreenSharingManager | null>(null);
  
  // Memoized values
  const activeUsers = useMemo(() => users.filter(user => user.isOnline), [users]);
  const typingUsers = useMemo(() => users.filter(user => user.isTyping && user.id !== currentUser.id), [users, currentUser.id]);
  const voiceChatUsers = useMemo(() => users.filter(user => user.isInVoiceChat), [users]);
  const screenSharingUsers = useMemo(() => users.filter(user => user.isScreenSharing), [users]);
  
  // Keyboard shortcuts
  useHotkeys('ctrl+s, cmd+s', (event) => {
    event.preventDefault();
    handleSave();
  }, [content]);
  
  useHotkeys('ctrl+shift+f, cmd+shift+f', (event) => {
    event.preventDefault();
    handleToggleFullscreen();
  }, []);
  
  useHotkeys('ctrl+shift+v, cmd+shift+v', (event) => {
    event.preventDefault();
    if (enableVoiceChat) handleToggleVoiceChat();
  }, [enableVoiceChat, isVoiceChatActive]);
  
  useHotkeys('ctrl+shift+s, cmd+shift+s', (event) => {
    event.preventDefault();
    if (enableScreenSharing) handleToggleScreenSharing();
  }, [enableScreenSharing, isSharingScreen]);
  
  useHotkeys('ctrl+plus, cmd+plus', (event) => {
    event.preventDefault();
    handleZoomIn();
  }, [zoomLevel]);
  
  useHotkeys('ctrl+minus, cmd+minus', (event) => {
    event.preventDefault();
    handleZoomOut();
  }, [zoomLevel]);
  
  useHotkeys('ctrl+0, cmd+0', (event) => {
    event.preventDefault();
    setZoomLevel(100);
  }, []);
  
  // Initialize collaboration systems
  useEffect(() => {
    const initializeDesktopCollaboration = async () => {
      try {
        // Initialize native integrations
        nativeIntegrationsRef.current = new NativeIntegrations();
        await nativeIntegrationsRef.current.initialize();
        
        // Initialize desktop collaboration engine
        collaborationEngineRef.current = new DesktopCollaborationEngine(documentId, currentUser);
        await collaborationEngineRef.current.initialize();
        
        // Initialize medical validator
        if (enableMedicalValidation) {
          medicalValidatorRef.current = new MedicalSchemaValidator();
          await medicalValidatorRef.current.initialize();
        }
        
        // Initialize presence awareness
        presenceAwarenessRef.current = new PresenceAwareness(documentId, currentUser);
        await presenceAwarenessRef.current.initialize();
        
        // Initialize voice communication
        if (enableVoiceChat) {
          voiceCommunicationRef.current = new VoiceCommunication(documentId, currentUser);
          await voiceCommunicationRef.current.initialize();
        }
        
        // Initialize screen sharing
        if (enableScreenSharing) {
          screenSharingRef.current = new ScreenSharingManager(documentId, currentUser);
          await screenSharingRef.current.initialize();
        }
        
        // Set up event handlers
        setupDesktopEventHandlers();
        
        setConnectionStatus('connected');
        showNativeNotification('Connected to collaboration session');
      } catch (error) {
        console.error('Failed to initialize desktop collaboration:', error);
        setConnectionStatus('disconnected');
        showNativeNotification('Failed to connect to collaboration session', 'error');
        onError?.(error as Error);
      }
    };
    
    initializeDesktopCollaboration();
    
    return () => {
      // Cleanup
      collaborationEngineRef.current?.cleanup();
      nativeIntegrationsRef.current?.cleanup();
      presenceAwarenessRef.current?.cleanup();
      voiceCommunicationRef.current?.cleanup();
      screenSharingRef.current?.cleanup();
    };
  }, [documentId, currentUser, enableMedicalValidation, enableVoiceChat, enableScreenSharing, onError]);
  
  // Event handlers setup
  const setupDesktopEventHandlers = useCallback(() => {
    if (!collaborationEngineRef.current || !presenceAwarenessRef.current) return;
    
    // Content change events
    collaborationEngineRef.current.onContentChange((newContent) => {
      setContent(newContent);
      setConnectionStatus('connected');
      
      // Auto-save if enabled
      if (workspaceSettings.enableAutoSave) {
        const autoSaveTimer = setTimeout(() => {
          handleSave();
        }, workspaceSettings.autoSaveInterval * 1000);
        
        return () => clearTimeout(autoSaveTimer);
      }
    });
    
    // User presence events
    presenceAwarenessRef.current.onUserJoin((user) => {
      setUsers(prev => [...prev.filter(u => u.id !== user.id), user]);
      showNativeNotification(`${user.name} joined the session`);
    });
    
    presenceAwarenessRef.current.onUserLeave((userId) => {
      const user = users.find(u => u.id === userId);
      if (user) {
        showNativeNotification(`${user.name} left the session`);
      }
      setUsers(prev => prev.filter(u => u.id !== userId));
    });
    
    presenceAwarenessRef.current.onUserActivity((userId, activity) => {
      setUsers(prev => prev.map(user => 
        user.id === userId 
          ? { ...user, ...activity, lastActivity: new Date() }
          : user
      ));
    });
    
    // Voice chat events
    if (voiceCommunicationRef.current) {
      voiceCommunicationRef.current.onUserJoinedVoice((userId) => {
        setUsers(prev => prev.map(user =>
          user.id === userId ? { ...user, isInVoiceChat: true } : user
        ));
        showNativeNotification(`${users.find(u => u.id === userId)?.name || 'User'} joined voice chat`);
      });
      
      voiceCommunicationRef.current.onUserLeftVoice((userId) => {
        setUsers(prev => prev.map(user =>
          user.id === userId ? { ...user, isInVoiceChat: false } : user
        ));
      });
    }
    
    // Screen sharing events
    if (screenSharingRef.current) {
      screenSharingRef.current.onScreenShareStarted((userId) => {
        setUsers(prev => prev.map(user =>
          user.id === userId ? { ...user, isScreenSharing: true } : user
        ));
        showNativeNotification(`${users.find(u => u.id === userId)?.name || 'User'} is sharing their screen`);
      });
      
      screenSharingRef.current.onScreenShareStopped((userId) => {
        setUsers(prev => prev.map(user =>
          user.id === userId ? { ...user, isScreenSharing: false } : user
        ));
      });
    }
    
    // Medical validation events
    if (medicalValidatorRef.current) {
      medicalValidatorRef.current.onValidationComplete((validation) => {
        setMedicalValidation(validation);
        if (validation.errors.length > 0) {
          showNativeNotification(`${validation.errors.length} medical validation issues found`, 'warning');
        }
      });
    }
  }, [users, workspaceSettings]);
  
  // Content change handler
  const handleContentChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = event.target.value;
    setContent(newContent);
    setConnectionStatus('syncing');
    
    // Apply changes through collaboration engine
    collaborationEngineRef.current?.applyChange(newContent);
    
    // Update cursor position for presence awareness
    const cursorPosition = event.target.selectionStart;
    presenceAwarenessRef.current?.updateCursorPosition(cursorPosition);
    
    // Medical validation
    if (workspaceSettings.medicalValidationEnabled && medicalValidatorRef.current) {
      medicalValidatorRef.current.validateContent(newContent);
    }
  }, [workspaceSettings.medicalValidationEnabled]);
  
  // Save handler
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(content);
      showNativeNotification('Document saved successfully', 'success');
    }
  }, [content, onSave]);
  
  // Fullscreen toggle
  const handleToggleFullscreen = useCallback(() => {
    if (nativeIntegrationsRef.current) {
      nativeIntegrationsRef.current.toggleFullscreen();
      setIsFullscreen(prev => !prev);
    }
  }, []);
  
  // Picture-in-picture mode
  const handleTogglePictureInPicture = useCallback(() => {
    if (nativeIntegrationsRef.current) {
      nativeIntegrationsRef.current.togglePictureInPicture();
      setIsPictureInPicture(prev => !prev);
    }
  }, []);
  
  // Voice chat toggle
  const handleToggleVoiceChat = useCallback(() => {
    if (voiceCommunicationRef.current) {
      if (isVoiceChatActive) {
        voiceCommunicationRef.current.leaveVoiceChat();
      } else {
        voiceCommunicationRef.current.joinVoiceChat();
      }
      setIsVoiceChatActive(prev => !prev);
    }
  }, [isVoiceChatActive]);
  
  // Screen sharing toggle
  const handleToggleScreenSharing = useCallback(() => {
    if (screenSharingRef.current) {
      if (isSharingScreen) {
        screenSharingRef.current.stopScreenShare();
      } else {
        screenSharingRef.current.startScreenShare();
      }
      setIsSharingScreen(prev => !prev);
    }
  }, [isSharingScreen]);
  
  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev + 10, 200));
  }, []);
  
  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev - 10, 50));
  }, []);
  
  // Native notification helper
  const showNativeNotification = useCallback((message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    if (workspaceSettings.notificationsEnabled && nativeIntegrationsRef.current) {
      nativeIntegrationsRef.current.showNotification(message, type);
    }
  }, [workspaceSettings.notificationsEnabled]);

  return (
    <DesktopWorkspace ref={workspaceRef}>
      {/* Header */}
      <WorkspaceHeader>
        <Box display="flex" alignItems="center" gap={2}>
          {/* Connection status */}
          <Box display="flex" alignItems="center" gap={1}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: 
                  connectionStatus === 'connected' ? 'success.main' :
                  connectionStatus === 'connecting' ? 'warning.main' :
                  connectionStatus === 'syncing' ? 'info.main' : 'error.main'
              }}
            />
            <Typography variant="body2" color="textSecondary">
              {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
            </Typography>
          </Box>
          
          {/* Active users */}
          <AvatarGroup max={6}>
            {activeUsers.map(user => (
              <Tooltip key={user.id} title={`${user.name} (${user.role})`}>
                <Badge
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  badgeContent={
                    user.isScreenSharing ? <ScreenShareIcon fontSize="small" /> :
                    user.isInVoiceChat ? <VolumeUpIcon fontSize="small" /> :
                    user.isTyping ? <EditIcon fontSize="small" /> : null
                  }
                >
                  <Avatar
                    sx={{ 
                      bgcolor: user.color,
                      width: 36,
                      height: 36
                    }}
                  >
                    {user.name.charAt(0).toUpperCase()}
                  </Avatar>
                </Badge>
              </Tooltip>
            ))}
          </AvatarGroup>
          
          {/* Typing indicators */}
          {typingUsers.length > 0 && (
            <Chip
              size="small"
              icon={<EditIcon />}
              label={`${typingUsers.map(u => u.name).join(', ')} typing...`}
              color="primary"
              variant="outlined"
            />
          )}
          
          {/* Voice chat indicator */}
          {voiceChatUsers.length > 0 && (
            <Chip
              size="small"
              icon={<VolumeUpIcon />}
              label={`${voiceChatUsers.length} in voice chat`}
              color="secondary"
              variant="outlined"
            />
          )}
        </Box>
        
        <Box display="flex" alignItems="center" gap={1}>
          {/* Medical validation status */}
          {medicalValidation && (
            <Chip
              size="small"
              icon={<MedicalServicesIcon />}
              label={`${Math.round(medicalValidation.accuracy * 100)}% accuracy`}
              color={medicalValidation.accuracy > 0.9 ? 'success' : 'warning'}
              variant="outlined"
            />
          )}
          
          {/* Quick action buttons */}
          <Tooltip title="Save (Ctrl+S)">
            <IconButton onClick={handleSave}>
              <SaveIcon />
            </IconButton>
          </Tooltip>
          
          {enableVoiceChat && (
            <Tooltip title="Toggle Voice Chat (Ctrl+Shift+V)">
              <IconButton 
                onClick={handleToggleVoiceChat}
                color={isVoiceChatActive ? 'primary' : 'default'}
              >
                {isVoiceChatActive ? <VolumeUpIcon /> : <VolumeOffIcon />}
              </IconButton>
            </Tooltip>
          )}
          
          {enableScreenSharing && (
            <Tooltip title="Toggle Screen Sharing (Ctrl+Shift+S)">
              <IconButton 
                onClick={handleToggleScreenSharing}
                color={isSharingScreen ? 'primary' : 'default'}
              >
                <ScreenShareIcon />
              </IconButton>
            </Tooltip>
          )}
          
          <Tooltip title="Picture in Picture">
            <IconButton 
              onClick={handleTogglePictureInPicture}
              color={isPictureInPicture ? 'primary' : 'default'}
            >
              <PictureInPictureIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Fullscreen (Ctrl+Shift+F)">
            <IconButton 
              onClick={handleToggleFullscreen}
              color={isFullscreen ? 'primary' : 'default'}
            >
              {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Settings">
            <IconButton onClick={() => setShowSettingsDialog(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </WorkspaceHeader>
      
      {/* Main workspace */}
      <WorkspaceMain>
        {/* Editor panel */}
        <EditorPanel style={{ fontSize: `${zoomLevel}%` }}>
          <Box position="relative" height="100%">
            <TextField
              ref={editorRef}
              multiline
              fullWidth
              value={content}
              onChange={handleContentChange}
              disabled={readOnly}
              placeholder={readOnly ? "Read-only mode" : "Start typing to collaborate..."}
              variant="outlined"
              InputProps={{
                sx: {
                  height: '100%',
                  fontSize: `${workspaceSettings.fontSize}px`,
                  lineHeight: workspaceSettings.lineHeight,
                  fontFamily: 'Consolas, Monaco, "Lucida Console", monospace',
                  '& .MuiInputBase-input': {
                    height: '100% !important',
                    overflow: 'auto !important',
                    padding: '16px !important'
                  }
                }
              }}
              sx={{
                height: '100%',
                '& .MuiOutlinedInput-root': {
                  height: '100%'
                }
              }}
            />
            
            {/* Presence cursors */}
            {users.filter(u => u.id !== currentUser.id && u.cursor).map(user => (
              <PresenceCursor
                key={`cursor-${user.id}`}
                color={user.color}
                style={{
                  top: user.cursor?.y,
                  left: user.cursor?.x
                }}
              />
            ))}
            
            {/* Medical validation highlights */}
            {medicalValidation?.errors.map((error, index) => (
              <Box
                key={`error-${index}`}
                sx={{
                  position: 'absolute',
                  // Position based on line/column
                  backgroundColor: error.severity === 'error' ? 'error.main' : 'warning.main',
                  opacity: 0.3,
                  pointerEvents: 'none'
                }}
              />
            ))}
          </Box>
          
          {/* Floating toolbar */}
          <FloatingToolbar>
            <Tooltip title="Add Comment">
              <IconButton size="small">
                <CommentIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Medical Annotation">
              <IconButton size="small">
                <MedicalServicesIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share Selection">
              <IconButton size="small">
                <ShareIcon />
              </IconButton>
            </Tooltip>
          </FloatingToolbar>
        </EditorPanel>
        
        {/* Side panel */}
        {showSidePanel && (
          <SidePanel width={sidePanelWidth}>
            <Tabs
              value={selectedTab}
              onChange={(_, newValue) => setSelectedTab(newValue)}
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab label={`Users (${activeUsers.length})`} icon={<PeopleIcon />} />
              <Tab label="Medical" icon={<MedicalServicesIcon />} />
              <Tab label="History" icon={<HistoryIcon />} />
              <Tab label="Chat" icon={<ChatIcon />} />
            </Tabs>
            
            <Box flex={1} overflow="auto">
              {/* Users panel */}
              {selectedTab === 0 && (
                <List>
                  {users.map(user => (
                    <ListItem key={user.id}>
                      <ListItemAvatar>
                        <Badge
                          overlap="circular"
                          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                          badgeContent={
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                backgroundColor: user.isOnline ? 'success.main' : 'grey.400',
                                border: '2px solid white'
                              }}
                            />
                          }
                        >
                          <Avatar sx={{ bgcolor: user.color }}>
                            {user.name.charAt(0).toUpperCase()}
                          </Avatar>
                        </Badge>
                      </ListItemAvatar>
                      <ListItemText
                        primary={user.name}
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              {user.role.replace('_', ' ').toUpperCase()}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {user.nativeStatus.platform} • {user.nativeStatus.version}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box display="flex" gap={0.5}>
                          {user.isInVoiceChat && <VolumeUpIcon fontSize="small" />}
                          {user.isScreenSharing && <ScreenShareIcon fontSize="small" />}
                          {user.isTyping && <EditIcon fontSize="small" />}
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
              
              {/* Medical validation panel */}
              {selectedTab === 1 && medicalValidation && (
                <MedicalValidationPanel>
                  <Typography variant="h6" gutterBottom>
                    Medical Validation
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Accuracy
                      </Typography>
                      <Typography variant="h6">
                        {Math.round(medicalValidation.accuracy * 100)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Completeness
                      </Typography>
                      <Typography variant="h6">
                        {Math.round(medicalValidation.completeness * 100)}%
                      </Typography>
                    </Grid>
                  </Grid>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Issues Found ({medicalValidation.errors.length})
                  </Typography>
                  <List>
                    {medicalValidation.errors.map((error, index) => (
                      <ListItem key={index}>
                        <ListItemAvatar>
                          <Avatar sx={{ 
                            bgcolor: error.severity === 'error' ? 'error.main' : 'warning.main',
                            width: 24,
                            height: 24
                          }}>
                            {error.severity === 'error' ? <ErrorIcon /> : <WarningIcon />}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={error.message}
                          secondary={`Line ${error.line}, Column ${error.column}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </MedicalValidationPanel>
              )}
            </Box>
          </SidePanel>
        )}
      </WorkspaceMain>
      
      {/* Zoom controls */}
      <ZoomControls>
        <IconButton size="small" onClick={handleZoomOut}>
          <ZoomOutIcon />
        </IconButton>
        <Typography variant="body2" sx={{ minWidth: '50px', textAlign: 'center' }}>
          {zoomLevel}%
        </Typography>
        <IconButton size="small" onClick={handleZoomIn}>
          <ZoomInIcon />
        </IconButton>
        <IconButton size="small" onClick={() => setZoomLevel(100)}>
          <FitScreenIcon />
        </IconButton>
      </ZoomControls>
      
      {/* Speed dial for quick actions */}
      <SpeedDial
        ariaLabel="Collaboration actions"
        sx={{ position: 'absolute', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        <SpeedDialAction
          icon={<PersonAddIcon />}
          tooltipTitle="Invite Users"
          onClick={() => {/* Handle invite */}}
        />
        <SpeedDialAction
          icon={<FileUploadIcon />}
          tooltipTitle="Upload File"
          onClick={() => {/* Handle upload */}}
        />
        <SpeedDialAction
          icon={<CloudSyncIcon />}
          tooltipTitle="Sync to Cloud"
          onClick={() => {/* Handle sync */}}
        />
      </SpeedDial>
      
      {/* Progress indicator */}
      {connectionStatus === 'syncing' && (
        <LinearProgress 
          sx={{ 
            position: 'absolute', 
            bottom: 0, 
            left: 0, 
            right: 0 
          }} 
        />
      )}
    </DesktopWorkspace>
  );
};

export default CollaborativeWorkspace;