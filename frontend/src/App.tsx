import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import AudioEnhancement from './components/audio/AudioEnhancement';
import RealTimeTranscription from './components/transcription/RealTimeTranscription';
import EnhancedDocumentAnalysis from './components/document/EnhancedDocumentAnalysis';
import SmartBRollSuggestions from './components/smart-broll/SmartBRollSuggestions';
import RealTimeCollaborativeEditor from './components/collaboration/RealTimeCollaborativeEditor';
import AIAnalyticsDashboard from './components/analytics/AIAnalyticsDashboard';
import { 
  Upload as FileUpload, 
  Mic, 
  Globe, 
  Users, 
  BarChart3, 
  Settings,
  Search,
  Bell,
  User,
  ChevronDown,
  Play,
  Pause,
  Volume2,
  Download,
  Share2,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  DollarSign,
  Activity,
  Layers,
  Zap,
  Shield,
  Cloud,
  Database,
  Cpu,
  GitBranch,
  Terminal,
  Code,
  FileText,
  MessageSquare,
  Video,
  Music,
  Image,
  File,
  FolderOpen,
  Grid,
  List,
  Filter,
  SortAsc,
  MoreVertical,
  Edit3,
  Trash2,
  Copy,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  RefreshCw,
  Send,
  Inbox,
  Archive,
  Star,
  Heart,
  ThumbsUp,
  MessageCircle,
  Share,
  Bookmark,
  Flag,
  MapPin,
  Calendar,
  CreditCard,
  Package,
  ShoppingCart,
  Gift,
  Award,
  Target,
  Briefcase,
  Clipboard,
  FileCheck,
  FilePlus,
  FileMinus,
  FileX,
  FolderPlus,
  FolderMinus,
  Folder,
  HardDrive,
  Server,
  Wifi,
  WifiOff,
  Bluetooth,
  Cast,
  Airplay,
  Smartphone,
  Tablet,
  Monitor,
  Watch,
  Camera,
  Printer,
  ScanLine as Scanner,
  Keyboard,
  Mouse,
  Headphones,
  Speaker,
  Battery,
  BatteryCharging,
  Power,
  Sunrise,
  Sunset,
  Moon,
  Sun,
  CloudRain,
  CloudSnow,
  Wind,
  Thermometer,
  Droplet,
  Umbrella,
  Navigation,
  Compass,
  Map,
  Navigation2,
  Anchor,
  Flag as FlagIcon,
  Home,
  Building,
  Building2,
  Store,
  Hotel,
  Train,
  Car,
  Truck,
  Bus,
  Bike,
  Ship,
  Plane,
  Rocket,
  Globe2,
  Globe as Globe3,
  Globe as Earth,
  ChevronRight,
  Plus,
  X,
  Minimize2,
  Maximize2
} from 'lucide-react';

// Import custom styles
import './styles/enterprise.css';

// API integration hook
const useApiData = (endpoint: string) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/v1${endpoint}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('api_key') || 'demo-key'}`
          }
        });
        if (response.ok) {
          const result = await response.json();
          setData(result);
        } else {
          // Use demo data if API is not available
          setData(getDemoData(endpoint));
        }
      } catch (err) {
        // Use demo data on error
        setData(getDemoData(endpoint));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
};

// Demo data fallback
const getDemoData = (endpoint: string) => {
  switch (endpoint) {
    case '/stats':
      return {
        totalTranscriptions: 1247,
        hoursProcessed: 3842,
        accuracy: 98.7,
        languages: 42,
        activeUsers: 156,
        storageUsed: 2.4,
        apiCalls: 45632,
        revenue: 125430
      };
    case '/recent-files':
      return [
        { id: 1, name: 'Q4_Earnings_Call.mp4', size: '256 MB', status: 'completed', accuracy: 98.5, duration: '45:32', language: 'English', speaker_count: 5, created_at: '2024-01-15T10:30:00Z' },
        { id: 2, name: 'Product_Demo_2024.mp4', size: '128 MB', status: 'processing', accuracy: 0, duration: '23:15', language: 'English', speaker_count: 2, created_at: '2024-01-15T09:15:00Z' },
        { id: 3, name: 'Customer_Interview_John.wav', size: '89 MB', status: 'completed', accuracy: 97.2, duration: '18:45', language: 'Spanish', speaker_count: 3, created_at: '2024-01-15T08:45:00Z' },
        { id: 4, name: 'Board_Meeting_Dec.mp4', size: '512 MB', status: 'queued', accuracy: 0, duration: '1:23:45', language: 'English', speaker_count: 8, created_at: '2024-01-15T08:00:00Z' },
        { id: 5, name: 'Training_Session_AI.mp4', size: '342 MB', status: 'completed', accuracy: 99.1, duration: '56:12', language: 'English', speaker_count: 1, created_at: '2024-01-15T07:30:00Z' }
      ];
    case '/processing-queue':
      return [
        { id: 1, name: 'Product_Demo_2024.mp4', progress: 67, stage: 'Processing audio track 2 of 3', eta: '2 min remaining' }
      ];
    default:
      return {};
  }
};

const EnterpriseApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [notifications, setNotifications] = useState(12);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentUser] = useState({
    name: 'John Doe',
    email: 'john@company.com',
    avatar: 'JD',
    plan: 'Pro Plan'
  });

  // API data hooks
  const { data: stats } = useApiData('/stats');
  const { data: recentFiles } = useApiData('/recent-files');
  const { data: processingQueue } = useApiData('/processing-queue');

  useEffect(() => {
    // Simulate upload progress
    if (uploadProgress > 0 && uploadProgress < 100) {
      const timer = setTimeout(() => {
        setUploadProgress(prev => Math.min(prev + Math.random() * 20, 100));
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [uploadProgress]);

  // Format time ago
  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  // Handle file upload
  const handleFileUpload = (files: FileList) => {
    if (files.length > 0) {
      setUploadProgress(10);
      // Simulate upload process
      const file = files[0];
      console.log('Uploading file:', file.name);
    }
  };

  const gradientBg = theme === 'dark' 
    ? 'enterprise-bg-dark'
    : 'enterprise-bg-light';

  const headerBg = theme === 'dark' ? 'enterprise-header-dark' : 'enterprise-header-light';
  const sidebarBg = theme === 'dark' ? 'enterprise-sidebar-dark' : 'enterprise-sidebar-light';
  const cardBg = theme === 'dark' ? 'enterprise-card-dark' : 'enterprise-card-light';
  const textColor = theme === 'dark' ? 'text-gray-100' : 'text-gray-800';

  return (
    <div className={`min-h-screen ${gradientBg} ${textColor} transition-all duration-500`}>
      {/* Enhanced Header */}
      <header className={`${headerBg} backdrop-blur-xl shadow-2xl border-b border-opacity-20 sticky top-0 z-50 transition-all duration-300`}>
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              {/* Enhanced Logo */}
              <div className="flex items-center space-x-3">
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 p-3 rounded-xl hover:scale-105 transition-transform duration-300">
                    <Mic className="w-7 h-7 text-white" />
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    TranscribeAI Pro
                  </h1>
                  <p className="text-xs text-gray-500 font-medium">Enterprise Edition v3.0</p>
                </div>
              </div>
              
              {/* Enhanced Search Bar */}
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                <input
                  type="text"
                  placeholder="Search transcriptions, files, or commands..."
                  className={`pl-12 pr-4 py-3 w-96 rounded-xl ${theme === 'dark' ? 'bg-gray-800/80 text-white border-gray-600' : 'bg-white/80 border-gray-200'} border-2 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all duration-300`}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <kbd className="px-2 py-1 text-xs font-semibold text-gray-400 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">
                    ⌘K
                  </kbd>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              {/* Enhanced Stats Mini Display */}
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-green-100/80 dark:bg-green-900/30">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-700 dark:text-green-300">API Online</span>
                </div>
                <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-blue-100/80 dark:bg-blue-900/30">
                  <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    {processingQueue?.length || 0} in queue
                  </span>
                </div>
              </div>

              {/* Enhanced Action Buttons */}
              <div className="flex items-center space-x-3">
                <button className="relative p-3 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 hover:scale-105">
                  <Bell className="w-5 h-5" />
                  {notifications > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold animate-bounce">
                      {notifications}
                    </span>
                  )}
                </button>
                
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-3 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 hover:scale-105"
                >
                  {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>

                <div className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg hover:shadow-xl transition-all duration-200">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-semibold">{currentUser.plan}</span>
                </div>

                <div className="flex items-center space-x-3 cursor-pointer group">
                  <div className="flex flex-col items-end">
                    <span className="text-sm font-semibold">{currentUser.name}</span>
                    <span className="text-xs text-gray-500">{currentUser.email}</span>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg group-hover:scale-105 transition-transform duration-200">
                    {currentUser.avatar}
                  </div>
                  <ChevronDown className="w-4 h-4 group-hover:rotate-180 transition-transform duration-200" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Enhanced Sidebar */}
        <aside className={`${sidebarCollapsed ? 'w-20' : 'w-72'} ${sidebarBg} backdrop-blur-xl shadow-2xl h-[calc(100vh-89px)] sticky top-[89px] transition-all duration-300 border-r border-opacity-20`}>
          <div className="p-6">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="mb-8 p-3 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
            >
              <Grid className={`w-5 h-5 ${sidebarCollapsed ? 'rotate-45' : ''} transition-transform duration-300`} />
            </button>

            <nav className="space-y-3">
              {[
                { icon: BarChart3, label: 'Dashboard', id: 'dashboard', badge: null, color: 'from-blue-500 to-blue-600' },
                { icon: FileUpload, label: 'Upload', id: 'upload', badge: 'New', color: 'from-green-500 to-green-600' },
                { icon: FileText, label: 'Transcriptions', id: 'transcriptions', badge: stats?.totalTranscriptions?.toString() || '247', color: 'from-purple-500 to-purple-600' },
                { icon: Volume2, label: 'Audio Enhancement', id: 'enhancement', badge: 'AI', color: 'from-purple-500 to-pink-600' },
                { icon: Activity, label: 'Real-time', id: 'realtime', badge: 'Live', color: 'from-red-500 to-red-600' },
                { icon: FileText, label: 'Document Analysis', id: 'document', badge: 'OCR', color: 'from-cyan-500 to-blue-600' },
                { icon: Video, label: 'Smart B-Roll', id: 'broll', badge: 'Beta', color: 'from-indigo-500 to-purple-600' },
                { icon: Edit3, label: 'Collaboration', id: 'collaboration', badge: 'Live', color: 'from-emerald-500 to-teal-600' },
                { icon: BarChart3, label: 'AI Analytics', id: 'ai-analytics', badge: 'AI', color: 'from-violet-500 to-purple-600' },
                { icon: Users, label: 'Team', id: 'team', badge: null, color: 'from-orange-500 to-orange-600' },
                { icon: Globe, label: 'Languages', id: 'languages', badge: stats?.languages?.toString() || '42', color: 'from-teal-500 to-teal-600' },
                { icon: Zap, label: 'AI Models', id: 'models', badge: null, color: 'from-yellow-500 to-yellow-600' },
                { icon: Database, label: 'Storage', id: 'storage', badge: `${stats?.storageUsed || 2.4} TB`, color: 'from-indigo-500 to-indigo-600' },
                { icon: GitBranch, label: 'API', id: 'api', badge: null, color: 'from-pink-500 to-pink-600' },
                { icon: Shield, label: 'Security', id: 'security', badge: null, color: 'from-red-500 to-red-600' },
                { icon: Settings, label: 'Settings', id: 'settings', badge: null, color: 'from-gray-500 to-gray-600' }
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between p-4 rounded-xl transition-all duration-300 group ${
                    activeTab === item.id 
                      ? `bg-gradient-to-r ${item.color} text-white shadow-lg transform scale-105` 
                      : 'hover:bg-white/10 hover:scale-102'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <item.icon className={`w-6 h-6 ${activeTab === item.id ? 'text-white' : ''}`} />
                    {!sidebarCollapsed && (
                      <span className={`font-semibold ${activeTab === item.id ? 'text-white' : ''}`}>
                        {item.label}
                      </span>
                    )}
                  </div>
                  {!sidebarCollapsed && item.badge && (
                    <span className={`text-xs px-3 py-1 rounded-full font-bold ${
                      activeTab === item.id 
                        ? 'bg-white/20 text-white' 
                        : 'bg-blue-500 text-white'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                  {!sidebarCollapsed && (
                    <ChevronRight className={`w-4 h-4 opacity-0 group-hover:opacity-100 transition-all duration-200 ${
                      activeTab === item.id ? 'opacity-100 text-white' : ''
                    }`} />
                  )}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Enhanced Main Content */}
        <main className="flex-1 p-8 overflow-auto">
          {activeTab === 'dashboard' && (
            <div className="space-y-8">
              {/* Enhanced Stats Grid */}
              <div className="grid grid-cols-4 gap-6">
                {[
                  { 
                    label: 'Total Transcriptions', 
                    value: stats?.totalTranscriptions?.toLocaleString() || '1,247', 
                    change: '+12%', 
                    icon: FileText, 
                    color: 'blue',
                    gradient: 'from-blue-500 to-blue-600'
                  },
                  { 
                    label: 'Hours Processed', 
                    value: stats?.hoursProcessed?.toLocaleString() || '3,842', 
                    change: '+18%', 
                    icon: Clock, 
                    color: 'purple',
                    gradient: 'from-purple-500 to-purple-600'
                  },
                  { 
                    label: 'Accuracy Rate', 
                    value: `${stats?.accuracy || 98.7}%`, 
                    change: '+2.3%', 
                    icon: Target, 
                    color: 'green',
                    gradient: 'from-green-500 to-green-600'
                  },
                  { 
                    label: 'Monthly Revenue', 
                    value: `$${stats?.revenue?.toLocaleString() || '125,430'}`, 
                    change: '+24%', 
                    icon: DollarSign, 
                    color: 'orange',
                    gradient: 'from-orange-500 to-orange-600'
                  }
                ].map((stat, idx) => (
                  <div 
                    key={idx} 
                    className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 border border-opacity-20 group`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-4 rounded-xl bg-gradient-to-r ${stat.gradient} group-hover:scale-110 transition-transform duration-300`}>
                        <stat.icon className="w-8 h-8 text-white" />
                      </div>
                      <div className="flex items-center space-x-1 text-green-500 font-bold">
                        <TrendingUp className="w-4 h-4" />
                        <span className="text-sm">{stat.change}</span>
                      </div>
                    </div>
                    <h3 className="text-4xl font-bold mb-2 bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                      {stat.value}
                    </h3>
                    <p className="text-gray-500 font-medium">{stat.label}</p>
                    <div className="mt-4 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className={`h-full bg-gradient-to-r ${stat.gradient} rounded-full animate-pulse`} style={{ width: '75%' }}></div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Enhanced Charts Section */}
              <div className="grid grid-cols-2 gap-6">
                <div className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-opacity-20`}>
                  <h3 className="text-xl font-bold mb-4 flex items-center">
                    <Activity className="w-6 h-6 mr-3 text-blue-500" />
                    Processing Activity
                    <div className="ml-auto flex space-x-2">
                      <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </h3>
                  <div className="h-64 flex items-center justify-center bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-xl border-2 border-dashed border-blue-300/50">
                    <div className="text-center">
                      <Activity className="w-12 h-12 text-blue-500 mx-auto mb-2 animate-pulse" />
                      <span className="text-gray-500 font-medium">Real-time Activity Chart</span>
                      <p className="text-sm text-gray-400 mt-1">Data visualization coming soon</p>
                    </div>
                  </div>
                </div>

                <div className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-opacity-20`}>
                  <h3 className="text-xl font-bold mb-4 flex items-center">
                    <Globe2 className="w-6 h-6 mr-3 text-purple-500" />
                    Language Distribution
                    <div className="ml-auto flex space-x-2">
                      <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </h3>
                  <div className="h-64 flex items-center justify-center bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-xl border-2 border-dashed border-purple-300/50">
                    <div className="text-center">
                      <Globe2 className="w-12 h-12 text-purple-500 mx-auto mb-2 animate-pulse" />
                      <span className="text-gray-500 font-medium">Language Analytics</span>
                      <p className="text-sm text-gray-400 mt-1">Interactive charts coming soon</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Enhanced Recent Files Table */}
              <div className={`${cardBg} backdrop-blur-xl rounded-2xl shadow-xl border border-opacity-20 overflow-hidden`}>
                <div className="p-6 border-b border-opacity-20">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold flex items-center">
                      <FolderOpen className="w-6 h-6 mr-3 text-blue-500" />
                      Recent Transcriptions
                      <span className="ml-3 px-3 py-1 text-sm font-semibold bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded-full">
                        {recentFiles?.length || 5} files
                      </span>
                    </h3>
                    <div className="flex items-center space-x-3">
                      <button className="px-4 py-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-200 flex items-center space-x-2 hover:scale-105">
                        <Filter className="w-4 h-4" />
                        <span className="font-medium">Filter</span>
                      </button>
                      <button className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:shadow-lg transition-all duration-200 flex items-center space-x-2 hover:scale-105">
                        <Download className="w-4 h-4" />
                        <span className="font-medium">Export All</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'}`}>
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">File</th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Duration</th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Language</th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Speakers</th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Accuracy</th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {(recentFiles || []).map((file: any) => (
                        <tr key={file.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-all duration-200 group">
                          <td className="px-6 py-4">
                            <div className="flex items-center">
                              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900 mr-4 group-hover:scale-110 transition-transform duration-200">
                                <Video className="w-6 h-6 text-blue-500" />
                              </div>
                              <div>
                                <div className="font-semibold text-gray-900 dark:text-white">{file.name}</div>
                                <div className="text-sm text-gray-500 flex items-center space-x-2">
                                  <span>{file.size}</span>
                                  <span>•</span>
                                  <span>{timeAgo(file.created_at)}</span>
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                              file.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' :
                              file.status === 'processing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100' :
                              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                            }`}>
                              {file.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 font-medium">{file.duration}</td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              <Globe className="w-4 h-4 text-gray-400" />
                              <span className="font-medium">{file.language}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              <Users className="w-4 h-4 text-gray-400" />
                              <span className="font-medium">{file.speaker_count}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            {file.accuracy > 0 ? (
                              <div className="flex items-center">
                                <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-3">
                                  <div 
                                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${file.accuracy}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-bold text-green-600 dark:text-green-400">{file.accuracy}%</span>
                              </div>
                            ) : (
                              <span className="text-sm text-gray-500">Pending</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              <button className="p-2 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900 transition-all duration-200 hover:scale-110">
                                <Eye className="w-4 h-4 text-blue-500" />
                              </button>
                              <button className="p-2 rounded-lg hover:bg-green-100 dark:hover:bg-green-900 transition-all duration-200 hover:scale-110">
                                <Download className="w-4 h-4 text-green-500" />
                              </button>
                              <button className="p-2 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900 transition-all duration-200 hover:scale-110">
                                <Share2 className="w-4 h-4 text-purple-500" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Enhanced Active Processing */}
              {processingQueue && processingQueue.length > 0 && (
                <div className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-opacity-20`}>
                  <h3 className="text-xl font-bold mb-6 flex items-center">
                    <Cpu className="w-6 h-6 mr-3 text-green-500 animate-pulse" />
                    Active Processing
                    <div className="ml-3 px-3 py-1 text-sm font-semibold bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300 rounded-full">
                      {processingQueue.length} active
                    </div>
                  </h3>
                  <div className="space-y-4">
                    {processingQueue.map((item: any) => (
                      <div key={item.id} className="flex items-center justify-between p-6 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-200/30 dark:border-blue-700/30">
                        <div className="flex items-center space-x-4">
                          <div className="relative">
                            <div className="w-16 h-16 rounded-xl bg-blue-500 animate-ping absolute opacity-75"></div>
                            <div className="w-16 h-16 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center relative">
                              <Mic className="w-8 h-8 text-white" />
                            </div>
                          </div>
                          <div>
                            <p className="font-bold text-lg">{item.name}</p>
                            <p className="text-gray-500 font-medium">{item.stage}</p>
                            <p className="text-sm text-blue-600 dark:text-blue-400 font-semibold">{item.eta}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-6">
                          <div className="w-48">
                            <div className="flex justify-between text-sm mb-2 font-semibold">
                              <span>Progress</span>
                              <span className="text-blue-600 dark:text-blue-400">{item.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                              <div 
                                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 relative"
                                style={{ width: `${item.progress}%` }}
                              >
                                <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
                              </div>
                            </div>
                          </div>
                          <button className="p-3 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-all duration-200 hover:scale-105">
                            <Pause className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="max-w-5xl mx-auto">
              <div className={`${cardBg} backdrop-blur-xl rounded-2xl shadow-2xl border border-opacity-20 overflow-hidden`}>
                <div className="p-8">
                  <div className="text-center mb-8">
                    <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      Upload & Transcribe
                    </h2>
                    <p className="text-gray-500 text-lg">Upload your audio or video files for AI-powered transcription</p>
                  </div>

                  <div 
                    className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-2xl p-16 text-center hover:border-blue-500 transition-all duration-300 cursor-pointer bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-900/20 dark:to-purple-900/20 group"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      handleFileUpload(e.dataTransfer.files);
                    }}
                  >
                    <div className="flex justify-center mb-8">
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full blur-3xl opacity-30 group-hover:opacity-50 transition-opacity duration-300"></div>
                        <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 p-12 rounded-full group-hover:scale-110 transition-transform duration-300">
                          <Cloud className="w-20 h-20 text-white" />
                        </div>
                      </div>
                    </div>
                    
                    <h3 className="text-3xl font-bold mb-4">Drop your files here</h3>
                    <p className="text-gray-500 text-lg mb-8">or click to browse from your computer</p>
                    
                    <div className="flex items-center justify-center space-x-4 mb-8">
                      {['MP4', 'MP3', 'WAV', 'MOV', 'M4A'].map((format, idx) => (
                        <span key={format} className={`px-4 py-2 rounded-full text-sm font-bold transition-all duration-200 hover:scale-110 ${
                          idx === 0 ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300' :
                          idx === 1 ? 'bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-300' :
                          idx === 2 ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300' :
                          idx === 3 ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300' :
                          'bg-pink-100 dark:bg-pink-900 text-pink-600 dark:text-pink-300'
                        }`}>
                          {format}
                        </span>
                      ))}
                    </div>
                    
                    <p className="text-sm text-gray-500 font-medium">Maximum file size: 5GB • Supports batch upload</p>
                    
                    <input
                      type="file"
                      multiple
                      accept="audio/*,video/*"
                      className="hidden"
                      onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                      id="file-upload"
                    />
                    <label 
                      htmlFor="file-upload"
                      className="mt-6 inline-block px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl hover:shadow-lg transition-all duration-200 cursor-pointer hover:scale-105"
                    >
                      Choose Files
                    </label>
                  </div>

                  {uploadProgress > 0 && (
                    <div className="mt-8 p-6 rounded-xl bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200/50 dark:border-blue-700/50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-bold text-lg">Uploading...</span>
                        <span className="text-blue-600 dark:text-blue-400 font-bold">{Math.round(uploadProgress)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-4 rounded-full transition-all duration-500 relative"
                          style={{ width: `${uploadProgress}%` }}
                        >
                          <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="mt-8 grid grid-cols-2 gap-6">
                    <div className="p-6 rounded-xl bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-2 border-blue-200/50 dark:border-blue-800/50 hover:scale-105 transition-transform duration-200">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-bold text-lg">Auto-detect Language</span>
                        <div className="relative">
                          <input type="checkbox" className="sr-only" defaultChecked />
                          <div className="w-12 h-6 bg-blue-500 rounded-full shadow-inner flex items-center">
                            <div className="w-5 h-5 bg-white rounded-full shadow ml-6 transition-transform duration-200"></div>
                          </div>
                        </div>
                      </div>
                      <p className="text-gray-600 dark:text-gray-300 font-medium">AI will identify the spoken language automatically</p>
                    </div>
                    
                    <div className="p-6 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-2 border-purple-200/50 dark:border-purple-800/50 hover:scale-105 transition-transform duration-200">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-bold text-lg">Speaker Diarization</span>
                        <div className="relative">
                          <input type="checkbox" className="sr-only" defaultChecked />
                          <div className="w-12 h-6 bg-purple-500 rounded-full shadow-inner flex items-center">
                            <div className="w-5 h-5 bg-white rounded-full shadow ml-6 transition-transform duration-200"></div>
                          </div>
                        </div>
                      </div>
                      <p className="text-gray-600 dark:text-gray-300 font-medium">Identify and separate different speakers</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'enhancement' && (
            <div className="h-full">
              <AudioEnhancement />
            </div>
          )}

          {activeTab === 'realtime' && (
            <div className="h-full">
              <RealTimeTranscription />
            </div>
          )}

          {activeTab === 'document' && (
            <div className="h-full">
              <EnhancedDocumentAnalysis />
            </div>
          )}

          {activeTab === 'broll' && (
            <div className="h-full">
              <SmartBRollSuggestions />
            </div>
          )}

          {activeTab === 'collaboration' && (
            <div className="h-full">
              <RealTimeCollaborativeEditor
                documentId="demo-document-123"
                currentUser={{
                  user_id: '1',
                  username: currentUser.name,
                  email: currentUser.email,
                  avatar: undefined,
                  color: '#3B82F6',
                  role: 'editor',
                  joined_at: new Date().toISOString(),
                  last_seen: new Date().toISOString(),
                  is_typing: false,
                  cursor_position: 0,
                  selection_start: undefined,
                  selection_end: undefined
                }}
                initialContent="Welcome to Real-time Collaborative Editing! 

This is a demo of our collaborative editor where multiple users can edit documents simultaneously with real-time synchronization, conflict resolution, and commenting features.

Start typing to see the collaborative editing in action..."
              />
            </div>
          )}

          {activeTab === 'ai-analytics' && (
            <div className="h-full">
              <AIAnalyticsDashboard
                refreshInterval={30000}
                enableRealtime={true}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default EnterpriseApp;