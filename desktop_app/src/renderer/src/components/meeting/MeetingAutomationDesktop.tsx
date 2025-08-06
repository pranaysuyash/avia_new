import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Tabs,
  Tab,
  Badge,
  Tooltip,
  Menu,
  Switch,
  FormControlLabel,
  Slider,
  Snackbar,
  Drawer,
  AppBar,
  Toolbar,
  SpeedDial,
  SpeedDialIcon,
  SpeedDialAction,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Avatar,
  AvatarGroup,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineDot,
  TimelineConnector,
  TimelineContent,
  TimelineOppositeContent,
  ToggleButton,
  ToggleButtonGroup,
  Backdrop,
  Fade,
  Zoom,
  Stack,
  ButtonGroup,
  RadioGroup,
  Radio,
  FormLabel,
  Skeleton,
} from '@mui/material';
import {
  VideoCall,
  Videocam,
  VideocamOff,
  Mic,
  MicOff,
  ScreenShare,
  StopScreenShare,
  CallEnd,
  PersonAdd,
  Group,
  RecordVoiceOver,
  Transcribe,
  Schedule,
  Event,
  AccessTime,
  PlayArrow,
  Pause,
  Stop,
  FiberManualRecord,
  Settings,
  Save,
  Share,
  Download,
  CloudUpload,
  ContentCopy,
  Edit,
  Delete,
  Add,
  Remove,
  ExpandMore,
  ChevronRight,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Info,
  NotificationsActive,
  NotificationsOff,
  Chat,
  ChatBubble,
  Send,
  AttachFile,
  InsertEmoticon,
  MoreVert,
  Dashboard,
  Analytics,
  Assignment,
  AssignmentTurnedIn,
  AssignmentLate,
  AssignmentInd,
  CalendarToday,
  Today,
  DateRange,
  Timer,
  TimerOff,
  Speed,
  Storage,
  Memory,
  Psychology,
  Translate,
  Language,
  Subtitles,
  ClosedCaption,
  Notes,
  Description,
  Summarize,
  QuestionAnswer,
  Poll,
  HowToVote,
  ThumbUp,
  ThumbDown,
  EmojiEmotions,
  SentimentSatisfied,
  SentimentDissatisfied,
  Refresh,
  Sync,
  SyncDisabled,
  CloudSync,
  CloudOff,
  Visibility,
  VisibilityOff,
  VolumeUp,
  VolumeOff,
  Fullscreen,
  FullscreenExit,
  PictureInPicture,
  ViewModule,
  ViewList,
  ViewStream,
  FilterList,
  Sort,
  Search,
  ZoomIn,
  ZoomOut,
  CameraAlt,
  Headset,
  Speaker,
  SpeakerPhone,
  PhoneInTalk,
  PhoneMissed,
  PhoneForwarded,
} from '@mui/icons-material';
import { Line, Bar, Doughnut, Radar, Scatter } from 'react-chartjs-2';
import { format, formatDistanceToNow, addMinutes, isAfter, isBefore } from 'date-fns';
import { io, Socket } from 'socket.io-client';
import Peer from 'simple-peer';
import RecordRTC from 'recordrtc';

interface Meeting {
  id: string;
  title: string;
  description?: string;
  scheduledTime: Date;
  duration: number; // in minutes
  type: 'instant' | 'scheduled' | 'recurring';
  status: 'scheduled' | 'live' | 'ended';
  host: Participant;
  participants: Participant[];
  recording?: Recording;
  transcript?: Transcript;
  settings: MeetingSettings;
  analytics?: MeetingAnalytics;
}

interface Participant {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'host' | 'co-host' | 'participant';
  status: 'invited' | 'joined' | 'left';
  joinedAt?: Date;
  leftAt?: Date;
  audioEnabled: boolean;
  videoEnabled: boolean;
  screenSharing: boolean;
  speaking: boolean;
  raisedHand: boolean;
}

interface Recording {
  id: string;
  startTime: Date;
  endTime?: Date;
  size?: number;
  url?: string;
  status: 'recording' | 'processing' | 'completed' | 'failed';
}

interface Transcript {
  id: string;
  segments: TranscriptSegment[];
  language: string;
  confidence: number;
  status: 'processing' | 'completed' | 'failed';
}

interface TranscriptSegment {
  id: string;
  speaker: string;
  speakerId?: string;
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
}

interface MeetingSettings {
  autoRecord: boolean;
  autoTranscribe: boolean;
  enableChat: boolean;
  allowParticipantVideo: boolean;
  allowParticipantAudio: boolean;
  allowScreenShare: boolean;
  enableWaitingRoom: boolean;
  requirePassword: boolean;
  password?: string;
  maxParticipants: number;
  enableBreakoutRooms: boolean;
  enablePolls: boolean;
  enableQA: boolean;
  recordingLayout: 'gallery' | 'speaker' | 'shared';
  transcriptionLanguages: string[];
}

interface MeetingAnalytics {
  totalDuration: number;
  participantCount: number;
  averageAttendance: number;
  engagementScore: number;
  speakingTime: Record<string, number>;
  participationRate: Record<string, number>;
  chatMessages: number;
  questionsAsked: number;
  pollsCreated: number;
  reactions: Record<string, number>;
}

interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: Date;
  type: 'text' | 'file' | 'system';
  reactions?: Record<string, string[]>;
}

interface Poll {
  id: string;
  question: string;
  options: string[];
  votes: Record<string, string>;
  anonymous: boolean;
  multipleChoice: boolean;
  createdBy: string;
  createdAt: Date;
  status: 'active' | 'closed';
}

interface ActionItem {
  id: string;
  title: string;
  assignedTo?: string;
  dueDate?: Date;
  completed: boolean;
  createdAt: Date;
}

const MeetingAutomationDesktop: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [currentMeeting, setCurrentMeeting] = useState<Meeting | null>(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'calendar'>('grid');
  
  // Meeting state
  const [isInMeeting, setIsInMeeting] = useState(false);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [screenSharing, setScreenSharing] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  
  // UI state
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [participantsDrawerOpen, setParticipantsDrawerOpen] = useState(false);
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);
  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  const [analyticsDialogOpen, setAnalyticsDialogOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [pip, setPip] = useState(false);
  const [galleryView, setGalleryView] = useState(true);
  
  // Form state
  const [meetingTitle, setMeetingTitle] = useState('');
  const [meetingDescription, setMeetingDescription] = useState('');
  const [meetingDate, setMeetingDate] = useState('');
  const [meetingTime, setMeetingTime] = useState('');
  const [meetingDuration, setMeetingDuration] = useState(60);
  const [meetingType, setMeetingType] = useState<'instant' | 'scheduled' | 'recurring'>('scheduled');
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [unreadMessages, setUnreadMessages] = useState(0);
  
  // Poll state
  const [polls, setPolls] = useState<Poll[]>([]);
  const [activePoll, setActivePoll] = useState<Poll | null>(null);
  
  // Action items
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  
  // Refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRefs = useRef<Map<string, HTMLVideoElement>>(new Map());
  const socketRef = useRef<Socket | null>(null);
  const peersRef = useRef<Map<string, Peer.Instance>>(new Map());
  const recorderRef = useRef<RecordRTC | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [snackbar, setSnackbar] = useState<{ 
    open: boolean; 
    message: string; 
    severity: 'success' | 'error' | 'warning' | 'info' 
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const [meetingSettings, setMeetingSettings] = useState<MeetingSettings>({
    autoRecord: false,
    autoTranscribe: true,
    enableChat: true,
    allowParticipantVideo: true,
    allowParticipantAudio: true,
    allowScreenShare: true,
    enableWaitingRoom: false,
    requirePassword: false,
    maxParticipants: 100,
    enableBreakoutRooms: true,
    enablePolls: true,
    enableQA: true,
    recordingLayout: 'gallery',
    transcriptionLanguages: ['en'],
  });

  useEffect(() => {
    loadMeetings();
    initializeWebRTC();
    
    return () => {
      cleanupWebRTC();
    };
  }, []);

  const loadMeetings = () => {
    // Mock meetings data
    const mockMeetings: Meeting[] = [
      {
        id: 'meeting_1',
        title: 'Weekly Team Standup',
        description: 'Regular team sync-up meeting',
        scheduledTime: new Date(Date.now() + 3600000),
        duration: 30,
        type: 'recurring',
        status: 'scheduled',
        host: {
          id: 'user_1',
          name: 'John Doe',
          email: 'john@example.com',
          role: 'host',
          status: 'invited',
          audioEnabled: true,
          videoEnabled: true,
          screenSharing: false,
          speaking: false,
          raisedHand: false,
        },
        participants: [],
        settings: meetingSettings,
      },
      {
        id: 'meeting_2',
        title: 'Product Demo',
        description: 'Customer product demonstration',
        scheduledTime: new Date(Date.now() + 7200000),
        duration: 60,
        type: 'scheduled',
        status: 'scheduled',
        host: {
          id: 'user_1',
          name: 'John Doe',
          email: 'john@example.com',
          role: 'host',
          status: 'invited',
          audioEnabled: true,
          videoEnabled: true,
          screenSharing: false,
          speaking: false,
          raisedHand: false,
        },
        participants: [],
        settings: meetingSettings,
      },
    ];
    
    setMeetings(mockMeetings);
  };

  const initializeWebRTC = async () => {
    try {
      // Initialize socket connection
      socketRef.current = io('http://localhost:3001', {
        transports: ['websocket'],
      });
      
      socketRef.current.on('connect', () => {
        console.log('Connected to signaling server');
      });
      
      socketRef.current.on('user-joined', handleUserJoined);
      socketRef.current.on('signal', handleSignal);
      socketRef.current.on('user-left', handleUserLeft);
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      
      setLocalStream(stream);
      streamRef.current = stream;
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Failed to initialize WebRTC:', error);
      showSnackbar('Failed to access camera/microphone', 'error');
    }
  };

  const cleanupWebRTC = () => {
    // Stop local stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    
    // Close peer connections
    peersRef.current.forEach(peer => peer.destroy());
    peersRef.current.clear();
    
    // Disconnect socket
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
  };

  const handleUserJoined = (userId: string) => {
    // Create peer connection for new user
    const peer = new Peer({
      initiator: true,
      stream: streamRef.current || undefined,
      trickle: false,
    });
    
    peer.on('signal', (signal) => {
      socketRef.current?.emit('signal', { userId, signal });
    });
    
    peer.on('stream', (stream) => {
      setRemoteStreams(prev => new Map(prev).set(userId, stream));
    });
    
    peersRef.current.set(userId, peer);
  };

  const handleSignal = ({ userId, signal }: { userId: string; signal: any }) => {
    const peer = peersRef.current.get(userId);
    if (peer) {
      peer.signal(signal);
    } else {
      // Create new peer for incoming connection
      const newPeer = new Peer({
        initiator: false,
        stream: streamRef.current || undefined,
        trickle: false,
      });
      
      newPeer.on('signal', (signal) => {
        socketRef.current?.emit('signal', { userId, signal });
      });
      
      newPeer.on('stream', (stream) => {
        setRemoteStreams(prev => new Map(prev).set(userId, stream));
      });
      
      newPeer.signal(signal);
      peersRef.current.set(userId, newPeer);
    }
  };

  const handleUserLeft = (userId: string) => {
    const peer = peersRef.current.get(userId);
    if (peer) {
      peer.destroy();
      peersRef.current.delete(userId);
    }
    
    setRemoteStreams(prev => {
      const newStreams = new Map(prev);
      newStreams.delete(userId);
      return newStreams;
    });
  };

  const startMeeting = async (meeting?: Meeting) => {
    setIsInMeeting(true);
    setCurrentMeeting(meeting || null);
    
    if (meeting?.settings.autoRecord) {
      startRecording();
    }
    
    if (meeting?.settings.autoTranscribe) {
      startTranscription();
    }
    
    showSnackbar('Meeting started', 'success');
  };

  const endMeeting = () => {
    if (recording) {
      stopRecording();
    }
    
    if (transcribing) {
      stopTranscription();
    }
    
    setIsInMeeting(false);
    setCurrentMeeting(null);
    showSnackbar('Meeting ended', 'success');
  };

  const toggleAudio = () => {
    if (streamRef.current) {
      const audioTrack = streamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setAudioEnabled(audioTrack.enabled);
      }
    }
  };

  const toggleVideo = () => {
    if (streamRef.current) {
      const videoTrack = streamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setVideoEnabled(videoTrack.enabled);
      }
    }
  };

  const toggleScreenShare = async () => {
    if (!screenSharing) {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: false,
        });
        
        const videoTrack = screenStream.getVideoTracks()[0];
        
        // Replace video track in peer connections
        peersRef.current.forEach(peer => {
          const sender = peer.streams[0]?.getVideoTracks()[0];
          if (sender) {
            peer.replaceTrack(sender, videoTrack, streamRef.current!);
          }
        });
        
        videoTrack.onended = () => {
          setScreenSharing(false);
          // Restore camera video
          toggleScreenShare();
        };
        
        setScreenSharing(true);
      } catch (error) {
        console.error('Failed to share screen:', error);
        showSnackbar('Failed to share screen', 'error');
      }
    } else {
      // Stop screen sharing and restore camera
      const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
      const videoTrack = cameraStream.getVideoTracks()[0];
      
      peersRef.current.forEach(peer => {
        const sender = peer.streams[0]?.getVideoTracks()[0];
        if (sender) {
          peer.replaceTrack(sender, videoTrack, streamRef.current!);
        }
      });
      
      setScreenSharing(false);
    }
  };

  const startRecording = () => {
    if (!streamRef.current) return;
    
    const recorder = new RecordRTC(streamRef.current, {
      type: 'video',
      mimeType: 'video/webm',
    });
    
    recorder.startRecording();
    recorderRef.current = recorder;
    setRecording(true);
    showSnackbar('Recording started', 'success');
  };

  const stopRecording = () => {
    if (!recorderRef.current) return;
    
    recorderRef.current.stopRecording(() => {
      const blob = recorderRef.current!.getBlob();
      const url = URL.createObjectURL(blob);
      
      // Save recording
      const a = document.createElement('a');
      a.href = url;
      a.download = `meeting_${Date.now()}.webm`;
      a.click();
      
      URL.revokeObjectURL(url);
    });
    
    setRecording(false);
    showSnackbar('Recording saved', 'success');
  };

  const startTranscription = () => {
    // Initialize speech recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showSnackbar('Speech recognition not supported', 'error');
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    
    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join('');
      
      // Process transcript
      console.log('Transcript:', transcript);
    };
    
    recognition.start();
    setTranscribing(true);
    showSnackbar('Transcription started', 'success');
  };

  const stopTranscription = () => {
    setTranscribing(false);
    showSnackbar('Transcription stopped', 'success');
  };

  const scheduleMeeting = () => {
    if (!meetingTitle.trim()) {
      showSnackbar('Please enter a meeting title', 'warning');
      return;
    }
    
    const scheduledTime = new Date(`${meetingDate}T${meetingTime}`);
    
    const newMeeting: Meeting = {
      id: `meeting_${Date.now()}`,
      title: meetingTitle,
      description: meetingDescription,
      scheduledTime,
      duration: meetingDuration,
      type: meetingType,
      status: 'scheduled',
      host: {
        id: 'current_user',
        name: 'Current User',
        email: 'user@example.com',
        role: 'host',
        status: 'invited',
        audioEnabled: true,
        videoEnabled: true,
        screenSharing: false,
        speaking: false,
        raisedHand: false,
      },
      participants: [],
      settings: meetingSettings,
    };
    
    setMeetings([...meetings, newMeeting]);
    setScheduleDialogOpen(false);
    resetScheduleForm();
    showSnackbar('Meeting scheduled successfully', 'success');
  };

  const resetScheduleForm = () => {
    setMeetingTitle('');
    setMeetingDescription('');
    setMeetingDate('');
    setMeetingTime('');
    setMeetingDuration(60);
    setMeetingType('scheduled');
  };

  const sendChatMessage = () => {
    if (!chatInput.trim()) return;
    
    const message: ChatMessage = {
      id: `msg_${Date.now()}`,
      senderId: 'current_user',
      senderName: 'You',
      content: chatInput.trim(),
      timestamp: new Date(),
      type: 'text',
    };
    
    setChatMessages([...chatMessages, message]);
    setChatInput('');
    
    // Emit to other participants
    socketRef.current?.emit('chat-message', message);
  };

  const createPoll = (question: string, options: string[]) => {
    const poll: Poll = {
      id: `poll_${Date.now()}`,
      question,
      options,
      votes: {},
      anonymous: false,
      multipleChoice: false,
      createdBy: 'current_user',
      createdAt: new Date(),
      status: 'active',
    };
    
    setPolls([...polls, poll]);
    setActivePoll(poll);
    showSnackbar('Poll created', 'success');
  };

  const addActionItem = (title: string, assignedTo?: string, dueDate?: Date) => {
    const actionItem: ActionItem = {
      id: `action_${Date.now()}`,
      title,
      assignedTo,
      dueDate,
      completed: false,
      createdAt: new Date(),
    };
    
    setActionItems([...actionItems, actionItem]);
    showSnackbar('Action item added', 'success');
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const toggleFullscreen = () => {
    if (!fullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setFullscreen(!fullscreen);
  };

  const togglePictureInPicture = async () => {
    if (!localVideoRef.current) return;
    
    try {
      if (!pip) {
        await localVideoRef.current.requestPictureInPicture();
      } else {
        await document.exitPictureInPicture();
      }
      setPip(!pip);
    } catch (error) {
      console.error('Failed to toggle PiP:', error);
    }
  };

  const speedDialActions = [
    { icon: <VideoCall />, name: 'Start Instant Meeting', action: () => startMeeting() },
    { icon: <Schedule />, name: 'Schedule Meeting', action: () => setScheduleDialogOpen(true) },
    { icon: <Group />, name: 'Join Meeting', action: () => {} },
    { icon: <Settings />, name: 'Settings', action: () => setSettingsDialogOpen(true) },
  ];

  const renderMeetingRoom = () => (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#000' }}>
      {/* Meeting Header */}
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, color: '#fff' }}>
            {currentMeeting?.title || 'Meeting Room'}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {recording && (
              <Chip
                icon={<FiberManualRecord />}
                label="Recording"
                color="error"
                size="small"
              />
            )}
            {transcribing && (
              <Chip
                icon={<Transcribe />}
                label="Transcribing"
                color="primary"
                size="small"
              />
            )}
            
            <IconButton color="inherit" onClick={() => setParticipantsDrawerOpen(true)}>
              <Badge badgeContent={remoteStreams.size + 1} color="primary">
                <Group />
              </Badge>
            </IconButton>
            
            <IconButton color="inherit" onClick={() => setChatDrawerOpen(true)}>
              <Badge badgeContent={unreadMessages} color="error">
                <Chat />
              </Badge>
            </IconButton>
            
            <IconButton color="inherit" onClick={toggleFullscreen}>
              {fullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Video Grid */}
      <Box sx={{ flexGrow: 1, p: 2, overflow: 'auto' }}>
        <Grid container spacing={2}>
          {/* Local Video */}
          <Grid item xs={galleryView ? 6 : 12} md={galleryView ? 4 : 12} lg={galleryView ? 3 : 12}>
            <Paper sx={{ position: 'relative', paddingTop: '56.25%', bgcolor: '#1a1a1a' }}>
              <video
                ref={localVideoRef}
                autoPlay
                playsInline
                muted
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transform: 'scaleX(-1)',
                }}
              />
              <Box sx={{ position: 'absolute', bottom: 8, left: 8 }}>
                <Chip
                  label="You"
                  size="small"
                  sx={{ bgcolor: 'rgba(0,0,0,0.7)', color: '#fff' }}
                />
              </Box>
              {!videoEnabled && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                  }}
                >
                  <Avatar sx={{ width: 80, height: 80 }}>You</Avatar>
                </Box>
              )}
            </Paper>
          </Grid>
          
          {/* Remote Videos */}
          {Array.from(remoteStreams.entries()).map(([userId, stream]) => (
            <Grid item xs={galleryView ? 6 : 12} md={galleryView ? 4 : 12} lg={galleryView ? 3 : 12} key={userId}>
              <Paper sx={{ position: 'relative', paddingTop: '56.25%', bgcolor: '#1a1a1a' }}>
                <video
                  ref={(el) => {
                    if (el) {
                      remoteVideoRefs.current.set(userId, el);
                      el.srcObject = stream;
                    }
                  }}
                  autoPlay
                  playsInline
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />
                <Box sx={{ position: 'absolute', bottom: 8, left: 8 }}>
                  <Chip
                    label={`User ${userId.slice(-4)}`}
                    size="small"
                    sx={{ bgcolor: 'rgba(0,0,0,0.7)', color: '#fff' }}
                  />
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Meeting Controls */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 2,
          bgcolor: 'rgba(0,0,0,0.8)',
        }}
      >
        <IconButton
          color={audioEnabled ? 'default' : 'error'}
          onClick={toggleAudio}
          sx={{ bgcolor: audioEnabled ? 'rgba(255,255,255,0.1)' : 'error.main' }}
        >
          {audioEnabled ? <Mic /> : <MicOff />}
        </IconButton>
        
        <IconButton
          color={videoEnabled ? 'default' : 'error'}
          onClick={toggleVideo}
          sx={{ bgcolor: videoEnabled ? 'rgba(255,255,255,0.1)' : 'error.main' }}
        >
          {videoEnabled ? <Videocam /> : <VideocamOff />}
        </IconButton>
        
        <IconButton
          color={screenSharing ? 'primary' : 'default'}
          onClick={toggleScreenShare}
          sx={{ bgcolor: screenSharing ? 'primary.main' : 'rgba(255,255,255,0.1)' }}
        >
          {screenSharing ? <StopScreenShare /> : <ScreenShare />}
        </IconButton>
        
        <IconButton
          color={recording ? 'error' : 'default'}
          onClick={recording ? stopRecording : startRecording}
          sx={{ bgcolor: recording ? 'error.main' : 'rgba(255,255,255,0.1)' }}
        >
          <FiberManualRecord />
        </IconButton>
        
        <IconButton
          color={transcribing ? 'primary' : 'default'}
          onClick={transcribing ? stopTranscription : startTranscription}
          sx={{ bgcolor: transcribing ? 'primary.main' : 'rgba(255,255,255,0.1)' }}
        >
          <Transcribe />
        </IconButton>
        
        <Button
          variant="contained"
          color="error"
          startIcon={<CallEnd />}
          onClick={endMeeting}
          sx={{ ml: 2 }}
        >
          End Meeting
        </Button>
      </Paper>

      {/* Participants Drawer */}
      <Drawer
        anchor="right"
        open={participantsDrawerOpen}
        onClose={() => setParticipantsDrawerOpen(false)}
      >
        <Box sx={{ width: 320, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Participants ({remoteStreams.size + 1})
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <Avatar>You</Avatar>
              </ListItemIcon>
              <ListItemText primary="You" secondary="Host" />
              <ListItemSecondaryAction>
                <IconButton size="small">
                  {audioEnabled ? <Mic /> : <MicOff />}
                </IconButton>
                <IconButton size="small">
                  {videoEnabled ? <Videocam /> : <VideocamOff />}
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
            
            {Array.from(remoteStreams.keys()).map((userId) => (
              <ListItem key={userId}>
                <ListItemIcon>
                  <Avatar>{userId.slice(-2)}</Avatar>
                </ListItemIcon>
                <ListItemText primary={`User ${userId.slice(-4)}`} secondary="Participant" />
                <ListItemSecondaryAction>
                  <IconButton size="small">
                    <MoreVert />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Chat Drawer */}
      <Drawer
        anchor="right"
        open={chatDrawerOpen}
        onClose={() => {
          setChatDrawerOpen(false);
          setUnreadMessages(0);
        }}
      >
        <Box sx={{ width: 320, height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ p: 2 }}>
            <Typography variant="h6">Meeting Chat</Typography>
          </Box>
          <Divider />
          
          <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
            {chatMessages.map((message) => (
              <Box
                key={message.id}
                sx={{
                  mb: 2,
                  textAlign: message.senderId === 'current_user' ? 'right' : 'left',
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  {message.senderName} • {format(message.timestamp, 'HH:mm')}
                </Typography>
                <Paper
                  sx={{
                    p: 1,
                    mt: 0.5,
                    display: 'inline-block',
                    bgcolor: message.senderId === 'current_user' ? 'primary.main' : 'grey.200',
                    color: message.senderId === 'current_user' ? 'primary.contrastText' : 'text.primary',
                  }}
                >
                  <Typography variant="body2">{message.content}</Typography>
                </Paper>
              </Box>
            ))}
          </Box>
          
          <Divider />
          <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Type a message..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
            />
            <IconButton color="primary" onClick={sendChatMessage}>
              <Send />
            </IconButton>
          </Box>
        </Box>
      </Drawer>
    </Box>
  );

  if (isInMeeting) {
    return renderMeetingRoom();
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: drawerOpen ? 280 : 0,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 280,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            Meeting Hub
          </Typography>
        </Toolbar>
        <Divider />
        
        <Box sx={{ p: 2 }}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<VideoCall />}
            onClick={() => startMeeting()}
            sx={{ mb: 2 }}
          >
            Start Instant Meeting
          </Button>
          
          <Button
            fullWidth
            variant="outlined"
            startIcon={<Schedule />}
            onClick={() => setScheduleDialogOpen(true)}
            sx={{ mb: 2 }}
          >
            Schedule Meeting
          </Button>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Upcoming Meetings
          </Typography>
          
          <List dense>
            {meetings
              .filter(m => m.status === 'scheduled')
              .slice(0, 5)
              .map((meeting) => (
                <ListItem key={meeting.id} button>
                  <ListItemIcon>
                    <Event />
                  </ListItemIcon>
                  <ListItemText
                    primary={meeting.title}
                    secondary={format(meeting.scheduledTime, 'MMM dd, HH:mm')}
                  />
                </ListItem>
              ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* App Bar */}
        <AppBar position="static" color="default" elevation={1}>
          <Toolbar>
            <IconButton
              edge="start"
              onClick={() => setDrawerOpen(!drawerOpen)}
              sx={{ mr: 2 }}
            >
              <Menu />
            </IconButton>
            
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Meeting Automation
            </Typography>
            
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(_, value) => value && setViewMode(value)}
              size="small"
              sx={{ mr: 2 }}
            >
              <ToggleButton value="grid">
                <ViewModule />
              </ToggleButton>
              <ToggleButton value="list">
                <ViewList />
              </ToggleButton>
              <ToggleButton value="calendar">
                <CalendarToday />
              </ToggleButton>
            </ToggleButtonGroup>
            
            <IconButton onClick={() => loadMeetings()}>
              <Refresh />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={selectedTab} onChange={(_, value) => setSelectedTab(value)}>
            <Tab label="Meetings" icon={<VideoCall />} />
            <Tab label="Recordings" icon={<FiberManualRecord />} />
            <Tab label="Transcripts" icon={<Transcribe />} />
            <Tab label="Analytics" icon={<Analytics />} />
            <Tab label="Action Items" icon={<Assignment />} />
          </Tabs>
        </Box>

        {/* Tab Content */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
          {selectedTab === 0 && (
            /* Meetings Tab */
            <Box>
              {viewMode === 'grid' && (
                <Grid container spacing={3}>
                  {meetings.map((meeting) => (
                    <Grid item xs={12} sm={6} md={4} key={meeting.id}>
                      <Card>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                              <VideoCall />
                            </Avatar>
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography variant="h6" noWrap>
                                {meeting.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {format(meeting.scheduledTime, 'MMM dd, yyyy')}
                              </Typography>
                            </Box>
                            <Chip
                              label={meeting.status}
                              size="small"
                              color={meeting.status === 'live' ? 'error' : 'default'}
                            />
                          </Box>
                          
                          <Typography variant="body2" sx={{ mb: 2 }}>
                            {meeting.description || 'No description'}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <AccessTime sx={{ mr: 1, fontSize: 20 }} />
                            <Typography variant="body2">
                              {format(meeting.scheduledTime, 'HH:mm')} • {meeting.duration} min
                            </Typography>
                          </Box>
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Group sx={{ mr: 1, fontSize: 20 }} />
                            <Typography variant="body2">
                              {meeting.participants.length} participants
                            </Typography>
                          </Box>
                          
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            {isAfter(new Date(), meeting.scheduledTime) && 
                             isBefore(new Date(), addMinutes(meeting.scheduledTime, meeting.duration)) ? (
                              <Button
                                fullWidth
                                variant="contained"
                                color="error"
                                startIcon={<VideoCall />}
                                onClick={() => startMeeting(meeting)}
                              >
                                Join Now
                              </Button>
                            ) : (
                              <Button
                                fullWidth
                                variant="contained"
                                startIcon={<VideoCall />}
                                onClick={() => startMeeting(meeting)}
                                disabled={meeting.status !== 'scheduled'}
                              >
                                Start
                              </Button>
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
              
              {viewMode === 'list' && (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Meeting</TableCell>
                        <TableCell>Date & Time</TableCell>
                        <TableCell>Duration</TableCell>
                        <TableCell>Participants</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {meetings.map((meeting) => (
                        <TableRow key={meeting.id}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                                <VideoCall />
                              </Avatar>
                              <Box>
                                <Typography variant="subtitle2">{meeting.title}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {meeting.description}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            {format(meeting.scheduledTime, 'MMM dd, yyyy HH:mm')}
                          </TableCell>
                          <TableCell>{meeting.duration} min</TableCell>
                          <TableCell>{meeting.participants.length}</TableCell>
                          <TableCell>
                            <Chip
                              label={meeting.status}
                              size="small"
                              color={meeting.status === 'live' ? 'error' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              startIcon={<VideoCall />}
                              onClick={() => startMeeting(meeting)}
                            >
                              Start
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          )}
          
          {selectedTab === 1 && (
            /* Recordings Tab */
            <Box>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Alert severity="info">
                    Meeting recordings will appear here after meetings end
                  </Alert>
                </Grid>
              </Grid>
            </Box>
          )}
          
          {selectedTab === 2 && (
            /* Transcripts Tab */
            <Box>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Alert severity="info">
                    Meeting transcripts will be available here after processing
                  </Alert>
                </Grid>
              </Grid>
            </Box>
          )}
          
          {selectedTab === 3 && (
            /* Analytics Tab */
            <Box>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {meetings.length}
                    </Typography>
                    <Typography variant="body2">Total Meetings</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {meetings.filter(m => m.status === 'ended').length}
                    </Typography>
                    <Typography variant="body2">Completed</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {meetings.filter(m => m.status === 'scheduled').length}
                    </Typography>
                    <Typography variant="body2">Scheduled</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {meetings.reduce((sum, m) => sum + m.participants.length, 0)}
                    </Typography>
                    <Typography variant="body2">Total Participants</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
          
          {selectedTab === 4 && (
            /* Action Items Tab */
            <Box>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => addActionItem('New Action Item')}
                    sx={{ mb: 2 }}
                  >
                    Add Action Item
                  </Button>
                  
                  <List>
                    {actionItems.map((item) => (
                      <ListItem key={item.id}>
                        <ListItemIcon>
                          <Checkbox
                            checked={item.completed}
                            onChange={(e) => {
                              setActionItems(
                                actionItems.map(i =>
                                  i.id === item.id ? { ...i, completed: e.target.checked } : i
                                )
                              );
                            }}
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.title}
                          secondary={
                            <Box>
                              {item.assignedTo && (
                                <Chip
                                  label={item.assignedTo}
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                              )}
                              {item.dueDate && (
                                <Typography variant="caption">
                                  Due: {format(item.dueDate, 'MMM dd')}
                                </Typography>
                              )}
                            </Box>
                          }
                          style={{
                            textDecoration: item.completed ? 'line-through' : 'none',
                          }}
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            edge="end"
                            onClick={() => {
                              setActionItems(actionItems.filter(i => i.id !== item.id));
                            }}
                          >
                            <Delete />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      </Box>

      {/* Speed Dial */}
      <SpeedDial
        ariaLabel="Meeting Actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        {speedDialActions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={action.action}
          />
        ))}
      </SpeedDial>

      {/* Schedule Meeting Dialog */}
      <Dialog
        open={scheduleDialogOpen}
        onClose={() => setScheduleDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Schedule Meeting</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Meeting Title"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description (Optional)"
                value={meetingDescription}
                onChange={(e) => setMeetingDescription(e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                label="Date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="time"
                label="Time"
                value={meetingTime}
                onChange={(e) => setMeetingTime(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Duration</InputLabel>
                <Select
                  value={meetingDuration}
                  onChange={(e) => setMeetingDuration(e.target.value as number)}
                >
                  <MenuItem value={15}>15 minutes</MenuItem>
                  <MenuItem value={30}>30 minutes</MenuItem>
                  <MenuItem value={45}>45 minutes</MenuItem>
                  <MenuItem value={60}>1 hour</MenuItem>
                  <MenuItem value={90}>1.5 hours</MenuItem>
                  <MenuItem value={120}>2 hours</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Meeting Type</InputLabel>
                <Select
                  value={meetingType}
                  onChange={(e) => setMeetingType(e.target.value as any)}
                >
                  <MenuItem value="instant">Instant</MenuItem>
                  <MenuItem value="scheduled">Scheduled</MenuItem>
                  <MenuItem value="recurring">Recurring</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Meeting Settings
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={meetingSettings.autoRecord}
                    onChange={(e) => setMeetingSettings({
                      ...meetingSettings,
                      autoRecord: e.target.checked
                    })}
                  />
                }
                label="Auto-record meeting"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={meetingSettings.autoTranscribe}
                    onChange={(e) => setMeetingSettings({
                      ...meetingSettings,
                      autoTranscribe: e.target.checked
                    })}
                  />
                }
                label="Auto-transcribe meeting"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={meetingSettings.enableWaitingRoom}
                    onChange={(e) => setMeetingSettings({
                      ...meetingSettings,
                      enableWaitingRoom: e.target.checked
                    })}
                  />
                }
                label="Enable waiting room"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScheduleDialogOpen(false)}>Cancel</Button>
          <Button onClick={scheduleMeeting} variant="contained">
            Schedule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MeetingAutomationDesktop;