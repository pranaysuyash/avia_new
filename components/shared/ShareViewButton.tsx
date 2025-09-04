import React from 'react';

import { logUxEvent } from './uxTelemetry';

type ShareViewButtonProps = {
  label?: string;
  className?: string;
  extraParams?: Record<string, string | null | undefined>;
};

export const ShareViewButton: React.FC<ShareViewButtonProps> = ({ label = 'Share', className = '', extraParams }) => {
  const onClick = async () => {
    try {
      const url = new URL(window.location.href);
      if (extraParams) {
        Object.entries(extraParams).forEach(([k, v]) => {
          if (v === null || v === undefined || v === '') url.searchParams.delete(k);
          else url.searchParams.set(k, String(v));
        });
      }
      await navigator.clipboard.writeText(url.toString());
      try { logUxEvent('share_view_copied', Object.assign({ href: url.toString() }, extraParams || {})); } catch {}
    } catch {}
  };

  return (
    <button onClick={onClick} className={className} aria-label="Copy shareable link" title="Copy shareable link">
      {label}
    </button>
  );
};

export default ShareViewButton;

