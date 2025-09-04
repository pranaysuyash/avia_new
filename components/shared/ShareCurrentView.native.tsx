import React from 'react';
import { Share } from 'react-native';
import { logUxEvent } from './uxTelemetry.native';

type Props = {
  label?: string;
  url?: string; // Optional deep link to share; if not provided, share app homepage
  params?: Record<string, string | number | boolean | null | undefined>;
  onShared?: () => void;
  style?: any;
};

export const ShareCurrentView: React.FC<Props> = ({ label = 'Share', url, params, onShared, style }) => {
  const onPress = async () => {
    try {
      let link = url ?? 'nerapp://home';
      if (params && Object.keys(params).length > 0) {
        const usp = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => {
          if (v === null || v === undefined || v === '') return;
          usp.set(k, String(v));
        });
        link += (link.includes('?') ? '&' : '?') + usp.toString();
      }
      await Share.share({ message: link });
      try { await logUxEvent('share_view_invoked', { href: link }); } catch {}
      onShared?.();
    } catch (e) {
      // noop
    }
  };

  return (
    <>
      {/* Keep it minimal; apps can wrap this in a styled Button */}
      {/* eslint-disable-next-line react-native/no-inline-styles */}
      <button onClick={onPress as any} style={style}>{label}</button>
    </>
  );
};

export default ShareCurrentView;

