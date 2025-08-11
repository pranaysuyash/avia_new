import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Badge,
  Tooltip,
  useTheme,
  alpha,
  Collapse,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AudioFile as AudioFileIcon,
  Description as DescriptionIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Payment as PaymentIcon,
  Api as ApiIcon,
  Notifications as NotificationsIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Logout as LogoutIcon,
  ChevronLeft as ChevronLeftIcon,
  ExpandLess,
  ExpandMore,
  Analytics as AnalyticsIcon,
  Storage as StorageIcon,
  Security as SecurityIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

const drawerWidth = 280;
const collapsedDrawerWidth = 72;

interface EnterpriseLayoutProps {
  onThemeToggle?: () => void;
}

export const EnterpriseLayout: React.FC<EnterpriseLayoutProps> = ({ onThemeToggle }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchor(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigationItems = [
    {
      title: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard',
      badge: null,
    },
    {
      title: 'Audio Processing',
      icon: <AudioFileIcon />,
      path: '/processing',
      badge: { content: 'NEW', color: 'success' },
    },
    {
      title: 'Transcriptions',
      icon: <DescriptionIcon />,
      path: '/transcriptions',
      badge: { content: 12, color: 'primary' },
    },
    {
      title: 'Analytics',
      icon: <AnalyticsIcon />,
      path: '/analytics',
      badge: null,
    },
    {
      title: 'Team',
      icon: <PeopleIcon />,
      path: '/team',
      badge: null,
    },
  ];

  const adminItems = [
    {
      title: 'User Management',
      icon: <PeopleIcon />,
      path: '/admin/users',
    },
    {
      title: 'Security',
      icon: <SecurityIcon />,
      path: '/admin/security',
    },
    {
      title: 'Storage',
      icon: <StorageIcon />,
      path: '/admin/storage',
    },
    {
      title: 'API Keys',
      icon: <ApiIcon />,
      path: '/admin/api-keys',
    },
  ];

  const bottomNavigationItems = [
    {
      title: 'Settings',
      icon: <SettingsIcon />,
      path: '/settings',
    },
    {
      title: 'Billing',
      icon: <PaymentIcon />,
      path: '/billing',
    },
    {
      title: 'API Docs',
      icon: <ApiIcon />,
      path: '/api-docs',
    },
    {
      title: 'Help',
      icon: <HelpIcon />,
      path: '/help',
    },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${drawerOpen ? drawerWidth : collapsedDrawerWidth}px)`,
          ml: `${drawerOpen ? drawerWidth : collapsedDrawerWidth}px`,
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          background: theme.palette.mode === 'light' 
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : theme.palette.grey[900],
          boxShadow: 'none',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{ mr: 2 }}
          >
            {drawerOpen ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navigationItems.find(item => item.path === location.pathname)?.title || 'Audio Intelligence Suite'}
          </Typography>

          {/* Theme Toggle */}
          <IconButton color="inherit" onClick={onThemeToggle} sx={{ mr: 1 }}>
            {theme.palette.mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>

          {/* Notifications */}
          <IconButton color="inherit" onClick={handleNotificationOpen} sx={{ mr: 1 }}>
            <Badge badgeContent={4} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* Profile Menu */}
          <Tooltip title="Account settings">
            <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0 }}>
              <Avatar 
                alt={user?.name || 'User'} 
                src={user?.avatar}
                sx={{ 
                  width: 32, 
                  height: 32,
                  border: `2px solid ${theme.palette.common.white}`,
                }}
              >
                {user?.name?.charAt(0) || 'U'}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        sx={{
          width: drawerOpen ? drawerWidth : collapsedDrawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerOpen ? drawerWidth : collapsedDrawerWidth,
            boxSizing: 'border-box',
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            backgroundColor: theme.palette.mode === 'light' 
              ? theme.palette.background.paper 
              : theme.palette.grey[900],
            borderRight: 'none',
            boxShadow: '2px 0 10px rgba(0,0,0,0.05)',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        {/* Logo Area */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: drawerOpen ? 'flex-start' : 'center',
            p: 2,
            minHeight: 64,
            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          {drawerOpen ? (
            <>
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  bgcolor: theme.palette.primary.main,
                  mr: 2,
                }}
              >
                AI
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1 }}>
                  Audio Intel
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Enterprise Edition
                </Typography>
              </Box>
            </>
          ) : (
            <Avatar
              sx={{
                width: 40,
                height: 40,
                bgcolor: theme.palette.primary.main,
              }}
            >
              AI
            </Avatar>
          )}
        </Box>

        {/* Navigation Items */}
        <List sx={{ px: 1, py: 2 }}>
          {navigationItems.map((item) => (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                selected={isActive(item.path)}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  '&.Mui-selected': {
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.15),
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: drawerOpen ? 40 : 'auto' }}>
                  {item.badge ? (
                    <Badge 
                      badgeContent={item.badge.content} 
                      color={item.badge.color as any}
                    >
                      {item.icon}
                    </Badge>
                  ) : (
                    item.icon
                  )}
                </ListItemIcon>
                {drawerOpen && (
                  <ListItemText 
                    primary={item.title}
                    primaryTypographyProps={{ fontSize: '0.875rem' }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        {/* Admin Section */}
        {user?.role === 'admin' && drawerOpen && (
          <>
            <Divider sx={{ mx: 2 }} />
            <List sx={{ px: 1, py: 1 }}>
              <ListItemButton onClick={() => setAdminMenuOpen(!adminMenuOpen)} sx={{ mx: 1, borderRadius: 2 }}>
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <SecurityIcon />
                </ListItemIcon>
                <ListItemText primary="Administration" primaryTypographyProps={{ fontSize: '0.875rem' }} />
                {adminMenuOpen ? <ExpandLess /> : <ExpandMore />}
              </ListItemButton>
              <Collapse in={adminMenuOpen} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {adminItems.map((item) => (
                    <ListItemButton
                      key={item.path}
                      sx={{ pl: 4, mx: 1, borderRadius: 2 }}
                      onClick={() => navigate(item.path)}
                    >
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText 
                        primary={item.title}
                        primaryTypographyProps={{ fontSize: '0.875rem' }}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </Collapse>
            </List>
          </>
        )}

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Bottom Navigation */}
        <List sx={{ px: 1, pb: 2 }}>
          <Divider sx={{ mx: 2, mb: 1 }} />
          {bottomNavigationItems.map((item) => (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                selected={isActive(item.path)}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  '&.Mui-selected': {
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: drawerOpen ? 40 : 'auto' }}>
                  {item.icon}
                </ListItemIcon>
                {drawerOpen && (
                  <ListItemText 
                    primary={item.title}
                    primaryTypographyProps={{ fontSize: '0.875rem' }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        {/* User Info */}
        {drawerOpen && (
          <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar sx={{ width: 32, height: 32 }} src={user?.avatar}>
                {user?.name?.charAt(0)}
              </Avatar>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="body2" noWrap sx={{ fontWeight: 500 }}>
                  {user?.name}
                </Typography>
                <Typography variant="caption" color="textSecondary" noWrap>
                  {user?.email}
                </Typography>
              </Box>
            </Box>
            {user?.subscription && (
              <Chip
                label={user.subscription}
                size="small"
                color="primary"
                sx={{ mt: 1, width: '100%' }}
              />
            )}
          </Box>
        )}
      </Drawer>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="body2" fontWeight="medium">
            {user?.name}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {user?.email}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={() => { handleProfileMenuClose(); navigate('/settings'); }}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          Account Settings
        </MenuItem>
        <MenuItem onClick={() => { handleProfileMenuClose(); navigate('/billing'); }}>
          <ListItemIcon>
            <PaymentIcon fontSize="small" />
          </ListItemIcon>
          Billing
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>

      {/* Notification Menu */}
      <Menu
        anchorEl={notificationAnchor}
        open={Boolean(notificationAnchor)}
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        PaperProps={{ sx: { width: 320, maxHeight: 400 } }}
      >
        <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
          <Typography variant="h6">Notifications</Typography>
        </Box>
        <List sx={{ p: 0 }}>
          {[1, 2, 3, 4].map((i) => (
            <ListItem key={i} sx={{ borderBottom: `1px solid ${theme.palette.divider}` }}>
              <ListItemText
                primary={`Processing completed for audio_${i}.mp3`}
                secondary="2 minutes ago"
                primaryTypographyProps={{ fontSize: '0.875rem' }}
                secondaryTypographyProps={{ fontSize: '0.75rem' }}
              />
            </ListItem>
          ))}
        </List>
        <Box sx={{ p: 1, textAlign: 'center' }}>
          <Typography
            variant="body2"
            color="primary"
            sx={{ cursor: 'pointer' }}
            onClick={() => navigate('/notifications')}
          >
            View all notifications
          </Typography>
        </Box>
      </Menu>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: theme.palette.grey[50],
          p: 3,
          width: `calc(100% - ${drawerOpen ? drawerWidth : collapsedDrawerWidth}px)`,
          marginTop: '64px',
          minHeight: 'calc(100vh - 64px)',
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};
