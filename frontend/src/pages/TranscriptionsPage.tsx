import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const TranscriptionsPage: React.FC = () => {
  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <CardTitle>Transcriptions</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Transcription management interface will be displayed here.</p>
        </CardContent>
      </Card>
    </div>
  );
};