import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { 
  FileUpload, 
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
  Scanner,
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
  Globe3,
  Earth
} from 'lucide-react';

const EnterpriseApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [notifications, setNotifications] = useState(12);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [recentFiles, setRecentFiles] = useState([
    { id: 1, name: 'Q4_Earnings_Call.mp4', size: '256 MB', status: 'completed', accuracy: 98.5, duration: '45:32', language: 'English', speaker_count: 5 },
    { id: 2, name: 'Product_Demo_2024.mp4', size: '128 MB', status: 'processing', accuracy: 0, duration: '23:15', language: 'English', speaker_count: 2 },
    { id: 3, name: 'Customer_Interview_John.wav', size: '89 MB', status: 'completed', accuracy: 97.2, duration: '18:45', language: 'Spanish', speaker_count: 3 },
    { id: 4, name: 'Board_Meeting_Dec.mp4', size: '512 MB', status: 'queued', accuracy: 0, duration: '1:23:45', language: 'English', speaker_count: 8 },
    { id: 5, name: 'Training_Session_AI.mp4', size: '342 MB', status: 'completed', accuracy: 99.1, duration: '56:12', language: 'English', speaker_count: 1 }
  ]);

  const stats = {
    totalTranscriptions: 1247,
    hoursProcessed: 3842,
    accuracy: 98.7,
    languages: 42,
    activeUsers: 156,
    storageUsed: 2.4,
    apiCalls: 45632,
    revenue: 125430
  };

  useEffect(() => {
    // Simulate upload progress
    if (uploadProgress > 0 && uploadProgress < 100) {
      const timer = setTimeout(() => {
        setUploadProgress(prev => Math.min(prev + Math.random() * 20, 100));
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [uploadProgress]);

  const gradientBg = theme === 'dark' 
    ? 'bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900'
    : 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50';

  const cardBg = theme === 'dark' ? 'bg-gray-800/90' : 'bg-white/90';
  const textColor = theme === 'dark' ? 'text-gray-100' : 'text-gray-800';
  const borderColor = theme === 'dark' ? 'border-gray-700' : 'border-gray-200';

  return (
    <div className={`min-h-screen ${gradientBg} ${textColor} transition-all duration-500`}>
      {/* Premium Header */}
      <header className={`${cardBg} backdrop-blur-xl shadow-2xl border-b ${borderColor} sticky top-0 z-50`}>
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur-lg opacity-75 animate-pulse"></div>
                  <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
                    <Mic className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    TranscribeAI Pro
                  </h1>
                  <p className="text-xs text-gray-500">Enterprise Edition v3.0</p>
                </div>
              </div>
              
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search transcriptions, files, or commands..."
                  className={`pl-10 pr-4 py-2 w-96 rounded-lg ${theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-gray-100'} focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all`}
                />
              </div>
            </div>

            <div className="flex items-center space-x-6">
              {/* Stats Mini Display */}
              <div className="flex items-center space-x-4">
                <div className="text-sm">
                  <span className="text-gray-500">API Status:</span>
                  <span className="ml-2 text-green-500 font-semibold">● Online</span>
                </div>
                <div className="text-sm">
                  <span className="text-gray-500">Queue:</span>
                  <span className="ml-2 font-semibold">3 jobs</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-3">
                <button className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                  <Bell className="w-5 h-5" />
                  {notifications > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {notifications}
                    </span>
                  )}
                </button>
                
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>

                <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 text-white">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-medium">Pro Plan</span>
                </div>

                <div className="flex items-center space-x-2 cursor-pointer">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                    JD
                  </div>
                  <ChevronDown className="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${sidebarCollapsed ? 'w-20' : 'w-64'} ${cardBg} backdrop-blur-xl shadow-xl h-[calc(100vh-73px)] sticky top-[73px] transition-all duration-300 border-r ${borderColor}`}>
          <div className="p-4">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="mb-6 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Grid className="w-5 h-5" />
            </button>

            <nav className="space-y-2">
              {[
                { icon: BarChart3, label: 'Dashboard', id: 'dashboard', badge: null },
                { icon: FileUpload, label: 'Upload', id: 'upload', badge: 'New' },
                { icon: FileText, label: 'Transcriptions', id: 'transcriptions', badge: '247' },
                { icon: Users, label: 'Team', id: 'team', badge: null },
                { icon: Globe, label: 'Languages', id: 'languages', badge: '42' },
                { icon: Zap, label: 'AI Models', id: 'models', badge: null },
                { icon: Database, label: 'Storage', id: 'storage', badge: '2.4 TB' },
                { icon: GitBranch, label: 'API', id: 'api', badge: null },
                { icon: Shield, label: 'Security', id: 'security', badge: null },
                { icon: Settings, label: 'Settings', id: 'settings', badge: null }
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg transition-all duration-200 ${
                    activeTab === item.id 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg transform scale-105' 
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <item.icon className="w-5 h-5" />
                    {!sidebarCollapsed && <span className="font-medium">{item.label}</span>}
                  </div>
                  {!sidebarCollapsed && item.badge && (
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      activeTab === item.id ? 'bg-white/20' : 'bg-blue-500 text-white'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {activeTab === 'dashboard' && (
            <div className="space-y-8">
              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-6">
                {[
                  { label: 'Total Transcriptions', value: stats.totalTranscriptions.toLocaleString(), change: '+12%', icon: FileText, color: 'blue' },
                  { label: 'Hours Processed', value: stats.hoursProcessed.toLocaleString(), change: '+18%', icon: Clock, color: 'purple' },
                  { label: 'Accuracy Rate', value: `${stats.accuracy}%`, change: '+2.3%', icon: Target, color: 'green' },
                  { label: 'Monthly Revenue', value: `$${stats.revenue.toLocaleString()}`, change: '+24%', icon: DollarSign, color: 'yellow' }
                ].map((stat, idx) => (
                  <div key={idx} className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border ${borderColor}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 rounded-xl bg-gradient-to-r from-${stat.color}-500 to-${stat.color}-600`}>
                        <stat.icon className="w-6 h-6 text-white" />
                      </div>
                      <span className="text-green-500 text-sm font-semibold">{stat.change}</span>
                    </div>
                    <h3 className="text-3xl font-bold mb-1">{stat.value}</h3>
                    <p className="text-gray-500 text-sm">{stat.label}</p>
                  </div>
                ))}
              </div>

              {/* Charts Section */}
              <div className="grid grid-cols-2 gap-6">
                <div className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl border ${borderColor}`}>
                  <h3 className="text-xl font-bold mb-4 flex items-center">
                    <Activity className="w-5 h-5 mr-2 text-blue-500" />
                    Processing Activity
                  </h3>
                  <div className="h-64 flex items-center justify-center bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl">
                    <span className="text-gray-500">Activity Chart Visualization</span>
                  </div>
                </div>

                <div className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl border ${borderColor}`}>
                  <h3 className="text-xl font-bold mb-4 flex items-center">
                    <Globe2 className="w-5 h-5 mr-2 text-purple-500" />
                    Language Distribution
                  </h3>
                  <div className="h-64 flex items-center justify-center bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl">
                    <span className="text-gray-500">Language Chart Visualization</span>
                  </div>
                </div>
              </div>

              {/* Recent Files Table */}
              <div className={`${cardBg} backdrop-blur-xl rounded-2xl shadow-xl border ${borderColor} overflow-hidden`}>
                <div className="p-6 border-b ${borderColor}">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold flex items-center">
                      <FolderOpen className="w-5 h-5 mr-2 text-blue-500" />
                      Recent Transcriptions
                    </h3>
                    <div className="flex items-center space-x-3">
                      <button className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center space-x-2">
                        <Filter className="w-4 h-4" />
                        <span>Filter</span>
                      </button>
                      <button className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:shadow-lg transition-all flex items-center space-x-2">
                        <Download className="w-4 h-4" />
                        <span>Export All</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className={`${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}`}>
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">File</th>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">Duration</th>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">Language</th>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">Speakers</th>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">Accuracy</th>
                        <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {recentFiles.map(file => (
                        <tr key={file.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center">
                              <Video className="w-8 h-8 text-blue-500 mr-3" />
                              <div>
                                <div className="font-medium">{file.name}</div>
                                <div className="text-sm text-gray-500">{file.size}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              file.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' :
                              file.status === 'processing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100' :
                              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                            }`}>
                              {file.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm">{file.duration}</td>
                          <td className="px-6 py-4 text-sm">{file.language}</td>
                          <td className="px-6 py-4 text-sm">{file.speaker_count}</td>
                          <td className="px-6 py-4">
                            {file.accuracy > 0 ? (
                              <div className="flex items-center">
                                <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                                  <div 
                                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                                    style={{ width: `${file.accuracy}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-medium">{file.accuracy}%</span>
                              </div>
                            ) : (
                              <span className="text-sm text-gray-500">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                                <Eye className="w-4 h-4" />
                              </button>
                              <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                                <Download className="w-4 h-4" />
                              </button>
                              <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                                <Share2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Active Processing */}
              <div className={`${cardBg} backdrop-blur-xl rounded-2xl p-6 shadow-xl border ${borderColor}`}>
                <h3 className="text-xl font-bold mb-4 flex items-center">
                  <Cpu className="w-5 h-5 mr-2 text-green-500 animate-pulse" />
                  Active Processing
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10">
                    <div className="flex items-center space-x-4">
                      <div className="relative">
                        <div className="w-12 h-12 rounded-full bg-blue-500 animate-ping absolute"></div>
                        <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center relative">
                          <Mic className="w-6 h-6 text-white" />
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold">Product_Demo_2024.mp4</p>
                        <p className="text-sm text-gray-500">Processing audio track 2 of 3</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="w-32">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Progress</span>
                          <span>67%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: '67%' }}></div>
                        </div>
                      </div>
                      <button className="p-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors">
                        <Pause className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="max-w-4xl mx-auto">
              <div className={`${cardBg} backdrop-blur-xl rounded-2xl shadow-2xl border ${borderColor} overflow-hidden`}>
                <div className="p-8">
                  <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Upload & Transcribe
                  </h2>
                  <p className="text-gray-500 mb-8">Upload your audio or video files for AI-powered transcription</p>

                  <div 
                    className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-2xl p-12 text-center hover:border-blue-500 transition-colors cursor-pointer bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-900/20 dark:to-purple-900/20"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      setUploadProgress(10);
                    }}
                  >
                    <div className="flex justify-center mb-6">
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full blur-2xl opacity-30 animate-pulse"></div>
                        <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 p-8 rounded-full">
                          <Cloud className="w-16 h-16 text-white" />
                        </div>
                      </div>
                    </div>
                    
                    <h3 className="text-2xl font-bold mb-3">Drop your files here</h3>
                    <p className="text-gray-500 mb-6">or click to browse from your computer</p>
                    
                    <div className="flex items-center justify-center space-x-4 mb-6">
                      <span className="px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 text-sm">MP4</span>
                      <span className="px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-300 text-sm">MP3</span>
                      <span className="px-3 py-1 rounded-full bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300 text-sm">WAV</span>
                      <span className="px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300 text-sm">MOV</span>
                      <span className="px-3 py-1 rounded-full bg-pink-100 dark:bg-pink-900 text-pink-600 dark:text-pink-300 text-sm">M4A</span>
                    </div>
                    
                    <p className="text-sm text-gray-500">Maximum file size: 5GB</p>
                  </div>

                  {uploadProgress > 0 && (
                    <div className="mt-8">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">Uploading...</span>
                        <span className="text-sm text-gray-500">{Math.round(uploadProgress)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}

                  <div className="mt-8 grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-200 dark:border-blue-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">Auto-detect Language</span>
                        <input type="checkbox" className="toggle" defaultChecked />
                      </div>
                      <p className="text-sm text-gray-500">AI will identify the spoken language</p>
                    </div>
                    
                    <div className="p-4 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-200 dark:border-purple-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">Speaker Diarization</span>
                        <input type="checkbox" className="toggle" defaultChecked />
                      </div>
                      <p className="text-sm text-gray-500">Identify different speakers</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default EnterpriseApp;