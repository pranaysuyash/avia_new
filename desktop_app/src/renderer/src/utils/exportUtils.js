import { jsPDF } from 'jspdf';
import { saveAs } from 'file-saver';

// Export transcription as PDF
export const exportToPDF = (transcription) => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 20;
  const maxWidth = pageWidth - 2 * margin;
  let yPosition = margin;

  // Title
  doc.setFontSize(18);
  doc.setFont(undefined, 'bold');
  doc.text(transcription.title || 'Transcription', margin, yPosition);
  yPosition += 10;

  // Metadata
  doc.setFontSize(10);
  doc.setFont(undefined, 'normal');
  doc.setTextColor(100);
  const metadata = [
    `Date: ${new Date(transcription.created_at).toLocaleString()}`,
    `Duration: ${Math.round(transcription.duration / 60)} minutes`,
    `Words: ${transcription.word_count.toLocaleString()}`,
    `Language: ${transcription.language.toUpperCase()}`
  ];
  
  metadata.forEach(line => {
    doc.text(line, margin, yPosition);
    yPosition += 5;
  });
  
  yPosition += 10;
  doc.setTextColor(0);

  // Summary (if available)
  if (transcription.summary) {
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('Summary', margin, yPosition);
    yPosition += 8;
    
    doc.setFontSize(11);
    doc.setFont(undefined, 'normal');
    const summaryLines = doc.splitTextToSize(transcription.summary, maxWidth);
    summaryLines.forEach(line => {
      if (yPosition > pageHeight - margin) {
        doc.addPage();
        yPosition = margin;
      }
      doc.text(line, margin, yPosition);
      yPosition += 6;
    });
    yPosition += 10;
  }

  // Entities
  if (transcription.entities && transcription.entities.length > 0) {
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('Named Entities', margin, yPosition);
    yPosition += 8;
    
    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    
    // Group entities by type
    const entitiesByType = {};
    transcription.entities.forEach(entity => {
      const type = entity.label || 'OTHER';
      if (!entitiesByType[type]) entitiesByType[type] = [];
      entitiesByType[type].push(entity.text);
    });
    
    Object.entries(entitiesByType).forEach(([type, entities]) => {
      if (yPosition > pageHeight - margin - 10) {
        doc.addPage();
        yPosition = margin;
      }
      doc.setFont(undefined, 'bold');
      doc.text(`${type}:`, margin, yPosition);
      doc.setFont(undefined, 'normal');
      doc.text(entities.join(', '), margin + 30, yPosition);
      yPosition += 6;
    });
    yPosition += 10;
  }

  // Transcript
  doc.setFontSize(14);
  doc.setFont(undefined, 'bold');
  doc.text('Transcript', margin, yPosition);
  yPosition += 8;
  
  doc.setFontSize(11);
  doc.setFont(undefined, 'normal');
  
  // Handle segments or full text
  if (transcription.segments) {
    transcription.segments.forEach(segment => {
      if (yPosition > pageHeight - margin - 10) {
        doc.addPage();
        yPosition = margin;
      }
      
      // Timestamp and speaker
      doc.setFontSize(9);
      doc.setTextColor(100);
      const timestamp = formatTimestamp(segment.start);
      let prefix = `[${timestamp}]`;
      if (segment.speaker) {
        prefix += ` ${segment.speaker}:`;
      }
      doc.text(prefix, margin, yPosition);
      yPosition += 5;
      
      // Segment text
      doc.setFontSize(11);
      doc.setTextColor(0);
      const lines = doc.splitTextToSize(segment.text, maxWidth - 10);
      lines.forEach(line => {
        if (yPosition > pageHeight - margin) {
          doc.addPage();
          yPosition = margin;
        }
        doc.text(line, margin + 10, yPosition);
        yPosition += 6;
      });
      yPosition += 4;
    });
  } else {
    // Full text without segments
    const lines = doc.splitTextToSize(transcription.text, maxWidth);
    lines.forEach(line => {
      if (yPosition > pageHeight - margin) {
        doc.addPage();
        yPosition = margin;
      }
      doc.text(line, margin, yPosition);
      yPosition += 6;
    });
  }

  // Save the PDF
  doc.save(`${transcription.title || 'transcription'}_${new Date().toISOString().split('T')[0]}.pdf`);
};

// Export transcription as DOCX
export const exportToDOCX = async (transcription) => {
  // Dynamic import to reduce bundle size
  const { Document, Packer, Paragraph, TextRun, HeadingLevel } = await import('docx');
  
  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        // Title
        new Paragraph({
          text: transcription.title || 'Transcription',
          heading: HeadingLevel.HEADING_1,
        }),
        
        // Metadata
        new Paragraph({
          children: [
            new TextRun({
              text: `Date: ${new Date(transcription.created_at).toLocaleString()}`,
              size: 20,
              color: '666666',
            }),
          ],
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: `Duration: ${Math.round(transcription.duration / 60)} minutes | Words: ${transcription.word_count.toLocaleString()} | Language: ${transcription.language.toUpperCase()}`,
              size: 20,
              color: '666666',
            }),
          ],
        }),
        
        // Empty paragraph for spacing
        new Paragraph({ text: '' }),
        
        // Summary
        ...(transcription.summary ? [
          new Paragraph({
            text: 'Summary',
            heading: HeadingLevel.HEADING_2,
          }),
          new Paragraph({
            text: transcription.summary,
            spacing: { after: 400 },
          }),
        ] : []),
        
        // Entities
        ...(transcription.entities && transcription.entities.length > 0 ? [
          new Paragraph({
            text: 'Named Entities',
            heading: HeadingLevel.HEADING_2,
          }),
          ...Object.entries(groupEntitiesByType(transcription.entities)).map(([type, entities]) => 
            new Paragraph({
              children: [
                new TextRun({
                  text: `${type}: `,
                  bold: true,
                }),
                new TextRun({
                  text: entities.join(', '),
                }),
              ],
            })
          ),
          new Paragraph({ text: '' }),
        ] : []),
        
        // Transcript
        new Paragraph({
          text: 'Transcript',
          heading: HeadingLevel.HEADING_2,
        }),
        
        // Transcript content
        ...(transcription.segments ? 
          transcription.segments.flatMap(segment => [
            new Paragraph({
              children: [
                new TextRun({
                  text: `[${formatTimestamp(segment.start)}]`,
                  color: '666666',
                  size: 18,
                }),
                ...(segment.speaker ? [
                  new TextRun({
                    text: ` ${segment.speaker}:`,
                    bold: true,
                    size: 20,
                  }),
                ] : []),
              ],
            }),
            new Paragraph({
              text: segment.text,
              spacing: { after: 200 },
              indent: { left: 720 }, // 0.5 inch indent
            }),
          ]) : [
            new Paragraph({
              text: transcription.text,
            }),
          ]
        ),
      ],
    }],
  });

  const blob = await Packer.toBlob(doc);
  saveAs(blob, `${transcription.title || 'transcription'}_${new Date().toISOString().split('T')[0]}.docx`);
};

// Export transcription as TXT
export const exportToTXT = (transcription) => {
  let content = '';
  
  // Title and metadata
  content += `${transcription.title || 'Transcription'}\n`;
  content += '='.repeat((transcription.title || 'Transcription').length) + '\n\n';
  content += `Date: ${new Date(transcription.created_at).toLocaleString()}\n`;
  content += `Duration: ${Math.round(transcription.duration / 60)} minutes\n`;
  content += `Words: ${transcription.word_count.toLocaleString()}\n`;
  content += `Language: ${transcription.language.toUpperCase()}\n\n`;
  
  // Summary
  if (transcription.summary) {
    content += 'SUMMARY\n';
    content += '-------\n';
    content += `${transcription.summary}\n\n`;
  }
  
  // Entities
  if (transcription.entities && transcription.entities.length > 0) {
    content += 'NAMED ENTITIES\n';
    content += '--------------\n';
    const entitiesByType = groupEntitiesByType(transcription.entities);
    Object.entries(entitiesByType).forEach(([type, entities]) => {
      content += `${type}: ${entities.join(', ')}\n`;
    });
    content += '\n';
  }
  
  // Transcript
  content += 'TRANSCRIPT\n';
  content += '----------\n';
  
  if (transcription.segments) {
    transcription.segments.forEach(segment => {
      const timestamp = formatTimestamp(segment.start);
      content += `[${timestamp}]`;
      if (segment.speaker) {
        content += ` ${segment.speaker}:`;
      }
      content += '\n';
      content += `${segment.text}\n\n`;
    });
  } else {
    content += transcription.text;
  }
  
  // Create and download the file
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  saveAs(blob, `${transcription.title || 'transcription'}_${new Date().toISOString().split('T')[0]}.txt`);
};

// Helper functions
const formatTimestamp = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const groupEntitiesByType = (entities) => {
  const grouped = {};
  entities.forEach(entity => {
    const type = entity.label || 'OTHER';
    if (!grouped[type]) grouped[type] = [];
    if (!grouped[type].includes(entity.text)) {
      grouped[type].push(entity.text);
    }
  });
  return grouped;
};