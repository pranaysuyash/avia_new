import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  FormControlLabel,
  Grid,
  Alert,
  LinearProgress,
  Chip,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CloudUpload,
  Gavel,
  Security,
  Download,
  Search,
  ExpandMore,
  Visibility,
  Edit,
  Delete
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

interface LegalEntity {
  type: string;
  text: string;
  confidence: number;
  start_pos: number;
  end_pos: number;
}

interface TranscriptionResult {
  status: string;
  transcript: string;
  legal_analysis: {
    entities: LegalEntity[];
    document_type: string;
    confidence_score: number;
  };
  compliance_check: {
    overall_score: number;
    checks: Array<{
      name: string;
      status: string;
      score: number;
    }>;
    recommendations: string[];
  };
  metadata: {
    case_number: string;
    proceeding_type: string;
    participants: string[];
    processing_time: number;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`legal-tabpanel-${index}`}
      aria-labelledby={`legal-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const LegalTranscription: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<TranscriptionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [caseNumber, setCaseNumber] = useState('');
  const [proceedingType, setProceedingType] = useState('hearing');
  const [courtJurisdiction, setCourtJurisdiction] = useState('');
  const [confidentialityLevel, setConfidentialityLevel] = useState('standard');
  const [participants, setParticipants] = useState('');
  const [attorneyClientPrivilege, setAttorneyClientPrivilege] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadedFile(acceptedFiles[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.mp4', '.m4a', '.flac']
    },
    multiple: false
  });

  const handleProcessTranscription = async () => {
    if (!uploadedFile) {
      setError('Please upload an audio file first');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('case_number', caseNumber);
      formData.append('proceeding_type', proceedingType);
      formData.append('court_jurisdiction', courtJurisdiction);
      formData.append('confidentiality_level', confidentialityLevel);
      formData.append('participants', JSON.stringify(participants.split('\n').filter(p => p.trim())));
      formData.append('attorney_client_privilege', attorneyClientPrivilege.toString());

      const response = await fetch('/api/legal/transcribe', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setTranscriptionResult(result);
      setActiveTab(1); // Switch to results tab
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during transcription');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const renderUploadTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <CloudUpload sx={{ mr: 1, verticalAlign: 'middle' }} />
              Upload Legal Audio
            </Typography>
            
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? '#f5f5f5' : 'transparent',
                mb: 3
              }}
            >
              <input {...getInputProps()} />
              {uploadedFile ? (
                <Typography>
                  Selected: {uploadedFile.name} ({(uploadedFile.size / 1024 / 1024).toFixed(2)} MB)
                </Typography>
              ) : (
                <Typography>
                  {isDragActive
                    ? 'Drop the audio file here...'
                    : 'Drag & drop an audio file here, or click to select'}
                </Typography>
              )}
            </Box>

            <Typography variant="h6" gutterBottom>
              Case Information
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Case Number"
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  placeholder="2023-CV-1234"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Proceeding Type</InputLabel>
                  <Select
                    value={proceedingType}
                    onChange={(e) => setProceedingType(e.target.value)}
                  >
                    <MenuItem value="hearing">Hearing</MenuItem>
                    <MenuItem value="deposition">Deposition</MenuItem>
                    <MenuItem value="trial">Trial</MenuItem>
                    <MenuItem value="mediation">Mediation</MenuItem>
                    <MenuItem value="arbitration">Arbitration</MenuItem>
                    <MenuItem value="conference">Conference</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Court Jurisdiction"
                  value={courtJurisdiction}
                  onChange={(e) => setCourtJurisdiction(e.target.value)}
                  placeholder="Federal District Court"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Confidentiality Level</InputLabel>
                  <Select
                    value={confidentialityLevel}
                    onChange={(e) => setConfidentialityLevel(e.target.value)}
                  >
                    <MenuItem value="standard">Standard</MenuItem>
                    <MenuItem value="confidential">Confidential</MenuItem>
                    <MenuItem value="privileged">Privileged</MenuItem>
                    <MenuItem value="sealed">Sealed</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Participants (one per line)"
                  value={participants}
                  onChange={(e) => setParticipants(e.target.value)}
                  placeholder="Judge Smith&#10;Attorney Jones&#10;Witness Doe"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={attorneyClientPrivilege}
                      onChange={(e) => setAttorneyClientPrivilege(e.target.checked)}
                    />
                  }
                  label="Contains Attorney-Client Privileged Communications"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
              Processing Options
            </Typography>
            
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Enable Speaker Diarization"
            />
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Enhance Legal Terminology"
            />
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Auto-suggest Redactions"
            />
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Format Legal Citations"
            />
            
            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleProcessTranscription}
              disabled={!uploadedFile || isProcessing}
              sx={{ mt: 2 }}
            >
              {isProcessing ? 'Processing...' : 'Process Legal Transcription'}
            </Button>
            
            {isProcessing && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                  Processing legal audio transcription...
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderResultsTab = () => {
    if (!transcriptionResult) {
      return (
        <Alert severity="info">
          No transcription results available. Please process an audio file first.
        </Alert>
      );
    }

    return (
      <Box>
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6">Document Type</Typography>
                <Typography variant="h4" color="primary">
                  {transcriptionResult.legal_analysis.document_type}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6">Confidence Score</Typography>
                <Typography variant="h4" color="primary">
                  {(transcriptionResult.legal_analysis.confidence_score * 100).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6">Legal Entities</Typography>
                <Typography variant="h4" color="primary">
                  {transcriptionResult.legal_analysis.entities.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6">Processing Time</Typography>
                <Typography variant="h4" color="primary">
                  {transcriptionResult.metadata.processing_time.toFixed(1)}s
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Tabs value={0} sx={{ mb: 2 }}>
          <Tab label="Transcript" />
          <Tab label="Legal Entities" />
          <Tab label="Compliance" />
        </Tabs>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Full Transcript
            </Typography>
            <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
              <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                {transcriptionResult.transcript}
              </Typography>
            </Paper>
          </CardContent>
        </Card>

        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Legal Entities
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Text</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Position</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transcriptionResult.legal_analysis.entities.map((entity, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Chip label={entity.type} size="small" />
                      </TableCell>
                      <TableCell>{entity.text}</TableCell>
                      <TableCell>{(entity.confidence * 100).toFixed(1)}%</TableCell>
                      <TableCell>{entity.start_pos}-{entity.end_pos}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Compliance Check
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body1">
                Overall Score: {transcriptionResult.compliance_check.overall_score.toFixed(1)}/10
              </Typography>
              <LinearProgress
                variant="determinate"
                value={transcriptionResult.compliance_check.overall_score * 10}
                sx={{ mt: 1 }}
              />
            </Box>
            
            {transcriptionResult.compliance_check.recommendations.length > 0 && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Recommendations:
                </Typography>
                {transcriptionResult.compliance_check.recommendations.map((rec, index) => (
                  <Alert key={index} severity="info" sx={{ mb: 1 }}>
                    {rec}
                  </Alert>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderAnalysisTab = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <Search sx={{ mr: 1, verticalAlign: 'middle' }} />
          Legal Text Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Analyze legal text for entities, compliance, and structure.
        </Typography>
        
        <TextField
          fullWidth
          multiline
          rows={8}
          label="Legal Text"
          placeholder="Paste legal document text here..."
          sx={{ mt: 2, mb: 2 }}
        />
        
        <Button variant="contained" startIcon={<Search />}>
          Analyze Legal Text
        </Button>
      </CardContent>
    </Card>
  );

  const renderExportTab = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <Download sx={{ mr: 1, verticalAlign: 'middle' }} />
          Export & Reports
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Export Format</InputLabel>
              <Select defaultValue="court">
                <MenuItem value="court">Court Reporter Format</MenuItem>
                <MenuItem value="brief">Legal Brief Format</MenuItem>
                <MenuItem value="discovery">Discovery Format</MenuItem>
                <MenuItem value="json">JSON Data</MenuItem>
                <MenuItem value="pdf">PDF Report</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<Download />}
              disabled={!transcriptionResult}
            >
              Generate Export
            </Button>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 2 }}>
          <FormControlLabel
            control={<Checkbox defaultChecked />}
            label="Include Legal Analysis"
          />
          <FormControlLabel
            control={<Checkbox defaultChecked />}
            label="Redact Privileged Content"
          />
          <FormControlLabel
            control={<Checkbox defaultChecked />}
            label="Include Metadata"
          />
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <Gavel sx={{ mr: 2, verticalAlign: 'middle' }} />
        Legal Transcription & Analysis
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Professional legal document processing with compliance features
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Upload & Process" />
          <Tab label="Results" />
          <Tab label="Text Analysis" />
          <Tab label="Export" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        {renderUploadTab()}
      </TabPanel>
      <TabPanel value={activeTab} index={1}>
        {renderResultsTab()}
      </TabPanel>
      <TabPanel value={activeTab} index={2}>
        {renderAnalysisTab()}
      </TabPanel>
      <TabPanel value={activeTab} index={3}>
        {renderExportTab()}
      </TabPanel>
    </Box>
  );
};

export default LegalTranscription;