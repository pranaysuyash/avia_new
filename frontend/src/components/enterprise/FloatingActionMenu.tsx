import React, { useState } from 'react';
import {
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Backdrop,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Add as AddIcon,
  Upload as UploadIcon,
  Mic as MicIcon,
  VideoCall as VideoCallIcon,
  CloudUpload as CloudUploadIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
} from '@mui/icons-material';

interface FloatingActionMenuProps {
  onUpload?: () => void;
  onRecord?: () => void;
  onLiveCapture?: () => void;
  onCloudImport?: () => void;
  onSettings?: () => void;
  onHelp?: () => void;
}

export const FloatingActionMenu: React.FC<FloatingActionMenuProps> = ({
  onUpload,
  onRecord,
  onLiveCapture,
  onCloudImport,
  onSettings,
  onHelp,
}) => {
  const theme = useTheme();
  const [open, setOpen] = useState(false);

  const actions = [
    {
      icon: <UploadIcon />,
      name: 'Upload Files',
      onClick: onUpload,
      color: theme.palette.primary.main,
    },
    {
      icon: <MicIcon />,
      name: 'Record Audio',
      onClick: onRecord,
      color: theme.palette.success.main,
    },
    {
      icon: <VideoCallIcon />,
      name: 'Live Capture',
      onClick: onLiveCapture,
      color: theme.palette.warning.main,
    },
    {
      icon: <CloudUploadIcon />,
      name: 'Cloud Import',
      onClick: onCloudImport,
      color: theme.palette.info.main,
    },
    {
      icon: <SettingsIcon />,
      name: 'Settings',
      onClick: onSettings,
      color: theme.palette.secondary.main,
    },
    {
      icon: <HelpIcon />,
      name: 'Help',
      onClick: onHelp,
      color: theme.palette.error.main,
    },
  ];

  return (
    <>
      <Backdrop
        open={open}
        sx={{
          zIndex: theme.zIndex.speedDial - 1,
          backgroundColor: alpha(theme.palette.common.black, 0.3),
          backdropFilter: 'blur(4px)',
        }}
      />
      
      <SpeedDial
        ariaLabel="Quick Actions"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          '& .MuiFab-primary': {
            background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
            boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.3)}`,
            '&:hover': {
              background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.secondary.dark} 100%)`,
              transform: 'scale(1.1)',
              boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.4)}`,
            },
          },
        }}
        icon={<SpeedDialIcon />}
        onClose={() => setOpen(false)}
        onOpen={() => setOpen(true)}
        open={open}
        direction="up"
      >
        {actions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            tooltipOpen
            onClick={() => {
              action.onClick?.();
              setOpen(false);
            }}
            sx={{
              '& .MuiFab-primary': {
                backgroundColor: action.color,
                color: 'white',
                '&:hover': {
                  backgroundColor: action.color,
                  transform: 'scale(1.1)',
                  boxShadow: `0 8px 24px ${alpha(action.color, 0.4)}`,
                },
              },
            }}
          />
        ))}
      </SpeedDial>
    </>
  );
};

export default FloatingActionMenu;