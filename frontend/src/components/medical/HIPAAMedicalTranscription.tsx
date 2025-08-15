import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Security,
  LocalHospital,
  Warning,
  CheckCircle,
  ExpandMore,
  Visibility,
  VisibilityOff,
  Download,
  Share,
  Info
} from '@mui/icons-material';

interface MedicalEntity {
  text: string;
  entity_type: string;
  confidence: number;
  start_pos: number;
  end_pos: number;
  normalized_form: string;
  medical_code?: string;
  context?: string;
}

interface PHIViolation {
  violation_type: string;
  text: string;
  position: [number, number];
  severity: string;
  recommendation: string;
}

interface MedicalCode {
  code: string;
  description: string;
  confidence: number;
  category: string;
}

interface TranscriptionResult {
  transcript_id: string;
  original_text: string;
  anonymized_text: string;
  medical_entities: MedicalEntity[];
  phi_violations: PHIViolation[];
  medical_codes: {
    icd10_codes: MedicalCode[];
    cpt_codes: MedicalCode[];
  };
  compliance_score: number;
  processing_time: number;
  timestamp: string;
  compliance_status: string;
}

interface HIPAAMedicalTranscriptionProps {
  onTranscriptionComplete?: (result: TranscriptionResult) => void;
}

const HIPAAMedicalTranscription: React.FC<HIPAAMedicalTranscriptionProps> = ({
  onTranscriptionComplete
}) => {
  const [transcriptText, setTranscriptText] = useState('');
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [showOriginalText, setShowOriginalText] = useState(false);
  const [complianceLevel, setComplianceLevel] = useState('standard');
  const [enablePHIDetection, setEnablePHIDetection] = useState(true);
  const [enableMedicalCoding, setEnableMedicalCoding] = useState(true);
  const [enableAuditLogging, setEnableAuditLogging] = useState(true);
  const [complianceDialogOpen, setComplianceDialogOpen] = useState(false);

  // Sample medical transcripts
  const sampleTranscripts = {
    'Cardiology Consultation': `Patient: John Smith, DOB: 03/15/1975, MRN: 12345678

Chief Complaint: Chest pain and shortness of breath

History of Present Illness: 
48-year-old male presents with acute onset chest pain that started 2 hours ago. 
Pain is substernal, radiating to left arm. Associated with diaphoresis and nausea.
Patient has history of hypertension and diabetes mellitus.

Physical Examination:
Vital Signs: BP 160/95, HR 110, RR 22, Temp 98.6°F
Cardiovascular: Irregular rhythm, S3 gallop present
Pulmonary: Bilateral rales at bases

Assessment and Plan:
1. Acute myocardial infarction - Start aspirin 325mg, metoprolol 25mg BID
2. Hypertension - Continue lisinopril 10mg daily
3. Diabetes mellitus - Monitor blood glucose, continue metformin

Follow-up in cardiology clinic in 1 week.`,

    'Emergency Department Note': `Patient: Mary Johnson, DOB: 07/22/1982, Phone: 555-123-4567

Chief Complaint: Severe abdominal pain

HPI: 41-year-old female presents with sudden onset severe RUQ abdominal pain 
radiating to right shoulder. Pain started 4 hours ago after eating fatty meal.
Associated with nausea and vomiting. No fever.

Physical Exam:
Abdomen: Tender RUQ with positive Murphy's sign

Labs: WBC 12,000, Total bilirubin 2.5

Imaging: Ultrasound shows gallbladder wall thickening and stones

Assessment: Acute cholecystitis
Plan: NPO, IV fluids, pain control, surgery consult`,

    'Progress Note': `Patient: Robert Davis, MRN: 87654321, Room 302

Subjective: Patient reports feeling better today. Pain decreased from 8/10 to 4/10.
Appetite improving. No nausea or vomiting.

Objective: 
Vital Signs: BP 130/80, HR 85, RR 18, Temp 99.1°F
General: Alert and oriented x3, appears comfortable
Abdomen: Soft, mild tenderness RUQ, bowel sounds present

Assessment: Post-operative day 2 status post laparoscopic cholecystectomy
Recovering well, no complications

Plan: 
1. Continue current medications
2. Advance diet as tolerated
3. Ambulation with PT
4. Discharge planning for tomorrow`
  };

  const handleSampleSelect = (sampleName: string) => {
    setTranscriptText(sampleTranscripts[sampleName as keyof typeof sampleTranscripts]);
  };

  const processTranscription = async () => {
    if (!transcriptText.trim()) {
      setError('Please enter medical transcript text');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/medical/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'demo_token'}`
        },
        body: JSON.stringify({
          text: transcriptText,
          compliance_level: complianceLevel,
          enable_phi_detection: enablePHIDetection,
          enable_medical_coding: enableMedicalCoding,
          enable_audit_logging: enableAuditLogging
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TranscriptionResult = await response.json();
      setResult(data);
      onTranscriptionComplete?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getComplianceColor = (score: number) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.7) return 'warning';
    return 'error';
  };

  const TabPanel = ({ children, value, index }: { children: React.ReactNode; value: number; index: number }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <LocalHospital sx={{ mr: 2, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              HIPAA-Compliant Medical Transcription
            </Typography>
          </Box>
          
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Enterprise-grade medical transcription with comprehensive HIPAA compliance,
            PHI detection, medical coding, and clinical documentation features.
          </Typography>

          {/* Configuration Panel */}
          <Accordion sx={{ mb: 3 }}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6">Configuration Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Compliance Level</InputLabel>
                    <Select
                      value={complianceLevel}
                      onChange={(e) => setComplianceLevel(e.target.value)}
                      label="Compliance Level"
                    >
                      <MenuItem value="strict">Strict</MenuItem>
                      <MenuItem value="standard">Standard</MenuItem>
                      <MenuItem value="research">Research</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enablePHIDetection}
                        onChange={(e) => setEnablePHIDetection(e.target.checked)}
                      />
                    }
                    label="PHI Detection"
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enableMedicalCoding}
                        onChange={(e) => setEnableMedicalCoding(e.target.checked)}
                      />
                    }
                    label="Medical Coding"
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enableAuditLogging}
                        onChange={(e) => setEnableAuditLogging(e.target.checked)}
                      />
                    }
                    label="Audit Logging"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Sample Transcripts */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Sample Medical Transcripts:</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.keys(sampleTranscripts).map((sampleName) => (
                <Button
                  key={sampleName}
                  variant="outlined"
                  size="small"
                  onClick={() => handleSampleSelect(sampleName)}
                >
                  {sampleName}
                </Button>
              ))}
            </Box>
          </Box>

          {/* Input Area */}
          <TextField
            fullWidth
            multiline
            rows={12}
            variant="outlined"
            label="Medical Transcript"
            placeholder="Enter medical transcript text here..."
            value={transcriptText}
            onChange={(e) => setTranscriptText(e.target.value)}
            sx={{ mb: 3 }}
          />

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={processTranscription}
              disabled={loading || !transcriptText.trim()}
              startIcon={<Security />}
            >
              {loading ? 'Processing...' : 'Process with HIPAA Compliance'}
            </Button>
            
            <Button
              variant="outlined"
              onClick={() => setComplianceDialogOpen(true)}
              startIcon={<Info />}
            >
              Compliance Info
            </Button>
          </Box>

          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Processing medical transcript with HIPAA compliance...
              </Typography>
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Processing Results</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Chip
                  label={`Compliance: ${(result.compliance_score * 100).toFixed(1)}%`}
                  color={getComplianceColor(result.compliance_score)}
                  icon={result.compliance_score >= 0.8 ? <CheckCircle /> : <Warning />}
                />
                <Chip
                  label={`${result.processing_time.toFixed(2)}s`}
                  variant="outlined"
                />
              </Box>
            </Box>

            <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
              <Tab label="Transcript" />
              <Tab label="PHI Analysis" />
              <Tab label="Medical Entities" />
              <Tab label="Medical Codes" />
              <Tab label="Compliance Report" />
            </Tabs>

            <TabPanel value={activeTab} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Original Transcript</Typography>
                    <IconButton
                      onClick={() => setShowOriginalText(!showOriginalText)}
                      sx={{ ml: 1 }}
                    >
                      {showOriginalText ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </Box>
                  {showOriginalText ? (
                    <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {result.original_text}
                      </Typography>
                    </Paper>
                  ) : (
                    <Alert severity="warning">
                      Original text hidden for PHI protection. Click the eye icon to view.
                    </Alert>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" sx={{ mb: 2 }}>De-identified Transcript</Typography>
                  <Paper sx={{ p: 2, bgcolor: 'success.50', maxHeight: 400, overflow: 'auto' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.anonymized_text}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Typography variant="h6" sx={{ mb: 2 }}>PHI Violations Detected</Typography>
              {result.phi_violations.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Text</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell>Recommendation</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.phi_violations.map((violation, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Chip
                              label={violation.violation_type.replace('potential_', '')}
                              size="small"
                              color={getSeverityColor(violation.severity)}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                              {violation.text}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={violation.severity}
                              size="small"
                              color={getSeverityColor(violation.severity)}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {violation.recommendation}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="success">
                  No PHI violations detected. Text is HIPAA compliant.
                </Alert>
              )}
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Typography variant="h6" sx={{ mb: 2 }}>Medical Entities Extracted</Typography>
              {result.medical_entities.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Entity</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Medical Code</TableCell>
                        <TableCell>Context</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.medical_entities.map((entity, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                              {entity.text}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {entity.normalized_form}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={entity.entity_type}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {(entity.confidence * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {entity.medical_code ? (
                              <Chip label={entity.medical_code} size="small" />
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                N/A
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 200 }}>
                              {entity.context || 'N/A'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  No medical entities detected in the transcript.
                </Alert>
              )}
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" sx={{ mb: 2 }}>ICD-10 Diagnostic Codes</Typography>
                  {result.medical_codes.icd10_codes.length > 0 ? (
                    <TableContainer component={Paper}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Code</TableCell>
                            <TableCell>Description</TableCell>
                            <TableCell>Confidence</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {result.medical_codes.icd10_codes.map((code, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <Chip label={code.code} size="small" color="primary" />
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {code.description}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {(code.confidence * 100).toFixed(1)}%
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Alert severity="info">No ICD-10 codes suggested.</Alert>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" sx={{ mb: 2 }}>CPT Procedure Codes</Typography>
                  {result.medical_codes.cpt_codes.length > 0 ? (
                    <TableContainer component={Paper}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Code</TableCell>
                            <TableCell>Description</TableCell>
                            <TableCell>Confidence</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {result.medical_codes.cpt_codes.map((code, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <Chip label={code.code} size="small" color="secondary" />
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {code.description}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {(code.confidence * 100).toFixed(1)}%
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Alert severity="info">No CPT codes suggested.</Alert>
                  )}
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={4}>
              <Typography variant="h6" sx={{ mb: 2 }}>HIPAA Compliance Report</Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        Overall Score
                      </Typography>
                      <Typography variant="h3" color={getComplianceColor(result.compliance_score)}>
                        {(result.compliance_score * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {result.compliance_status.replace('_', ' ').toUpperCase()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        PHI Violations
                      </Typography>
                      <Typography variant="h3" color={result.phi_violations.length > 0 ? 'error' : 'success'}>
                        {result.phi_violations.length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Detected Issues
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        Processing Time
                      </Typography>
                      <Typography variant="h3">
                        {result.processing_time.toFixed(2)}s
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Analysis Duration
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Compliance Summary</Typography>
                <Alert severity={result.compliance_score >= 0.8 ? 'success' : 'warning'}>
                  {result.compliance_score >= 0.8 ? (
                    <>
                      <strong>HIPAA Compliant:</strong> The transcript meets HIPAA compliance standards.
                      {result.phi_violations.length > 0 && ' Some PHI was detected and properly de-identified.'}
                    </>
                  ) : (
                    <>
                      <strong>Compliance Issues:</strong> The transcript has {result.phi_violations.length} PHI violations
                      that need to be addressed before sharing or storing.
                    </>
                  )}
                </Alert>
              </Box>
            </TabPanel>
          </CardContent>
        </Card>
      )}

      {/* Compliance Information Dialog */}
      <Dialog
        open={complianceDialogOpen}
        onClose={() => setComplianceDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>HIPAA Compliance Information</DialogTitle>
        <DialogContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Protected Health Information (PHI)</Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            PHI includes any information that can identify a patient, including:
          </Typography>
          <ul>
            <li>Names and addresses</li>
            <li>Dates of birth and death</li>
            <li>Phone and fax numbers</li>
            <li>Email addresses</li>
            <li>Social Security numbers</li>
            <li>Medical record numbers</li>
            <li>Account numbers</li>
            <li>Certificate/license numbers</li>
          </ul>

          <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>Compliance Levels</Typography>
          <ul>
            <li><strong>Strict:</strong> Maximum security with comprehensive PHI detection</li>
            <li><strong>Standard:</strong> Balanced approach for typical healthcare use</li>
            <li><strong>Research:</strong> Optimized for research and analytics use cases</li>
          </ul>

          <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>Security Features</Typography>
          <ul>
            <li>End-to-end encryption for all medical data</li>
            <li>Comprehensive audit logging</li>
            <li>Role-based access controls</li>
            <li>Automated breach detection</li>
            <li>Safe Harbor de-identification</li>
          </ul>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComplianceDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HIPAAMedicalTranscription;