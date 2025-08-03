import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Upgrade as UpgradeIcon,
  Payment as PaymentIcon,
  Analytics as AnalyticsIcon,
  Warning as WarningIcon,
  Star as StarIcon,
  Business as BusinessIcon
} from '@mui/icons-material';

interface SubscriptionStatus {
  has_subscription: boolean;
  tier: string;
  status: string;
  billing_interval?: string;
  current_period_start?: string;
  current_period_end?: string;
  plan: PricingPlan;
  limits: Record<string, any>;
  usage: Record<string, number>;
  usage_percentages: Record<string, number>;
  canceled_at?: string;
}

interface PricingPlan {
  tier: string;
  name: string;
  description: string;
  monthly_price: number;
  yearly_price: number;
  features: string[];
  limits: Record<string, any>;
}

interface Invoice {
  invoice_id: string;
  amount_due: number;
  amount_paid: number;
  status: string;
  billing_period_start: string;
  billing_period_end: string;
  created_at: string;
  paid_at?: string;
}

const SubscriptionManager: React.FC = () => {
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [availablePlans, setAvailablePlans] = useState<PricingPlan[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');

  useEffect(() => {
    loadSubscriptionData();
  }, []);

  const loadSubscriptionData = async () => {
    setLoading(true);
    try {
      // Mock API calls - replace with actual API endpoints
      const [statusResponse, plansResponse, invoicesResponse] = await Promise.all([
        fetch('/api/subscription/status'),
        fetch('/api/subscription/plans'),
        fetch('/api/subscription/invoices')
      ]);

      // Mock data for demo
      const mockStatus: SubscriptionStatus = {
        has_subscription: true,
        tier: 'pro',
        status: 'active',
        billing_interval: 'monthly',
        current_period_start: '2024-03-01T00:00:00Z',
        current_period_end: '2024-04-01T00:00:00Z',
        plan: {
          tier: 'pro',
          name: 'Pro',
          description: 'For professionals and small teams',
          monthly_price: 2900,
          yearly_price: 29000,
          features: [
            '50 hours of transcription per month',
            'Advanced AI analysis',
            'Priority support',
            'Up to 10 team members',
            '50GB storage'
          ],
          limits: {
            transcription_hours: 50,
            api_calls: 10000,
            team_members: 10,
            storage_gb: 50
          }
        },
        limits: {
          transcription_hours: 50,
          api_calls: 10000,
          team_members: 10,
          storage_gb: 50
        },
        usage: {
          transcription_hours: 23.5,
          api_calls: 3200,
          team_members: 4,
          storage_gb: 12.3
        },
        usage_percentages: {
          transcription_hours: 47,
          api_calls: 32,
          team_members: 40,
          storage_gb: 24.6
        }
      };

      const mockPlans: PricingPlan[] = [
        {
          tier: 'free',
          name: 'Free',
          description: 'Perfect for individuals getting started',
          monthly_price: 0,
          yearly_price: 0,
          features: [
            '5 hours of transcription per month',
            'Basic entity extraction',
            'Standard support',
            '1 team member',
            '1GB storage'
          ],
          limits: {
            transcription_hours: 5,
            api_calls: 1000,
            team_members: 1,
            storage_gb: 1
          }
        },
        {
          tier: 'pro',
          name: 'Pro',
          description: 'For professionals and small teams',
          monthly_price: 2900,
          yearly_price: 29000,
          features: [
            '50 hours of transcription per month',
            'Advanced AI analysis',
            'Priority support',
            'Up to 10 team members',
            '50GB storage',
            'API access'
          ],
          limits: {
            transcription_hours: 50,
            api_calls: 10000,
            team_members: 10,
            storage_gb: 50
          }
        },
        {
          tier: 'enterprise',
          name: 'Enterprise',
          description: 'For large organizations with advanced needs',
          monthly_price: 9900,
          yearly_price: 99000,
          features: [
            'Unlimited transcription',
            'Advanced AI analysis',
            '24/7 priority support',
            'Unlimited team members',
            '500GB storage',
            'Custom integrations',
            'SSO integration'
          ],
          limits: {
            transcription_hours: -1,
            api_calls: -1,
            team_members: -1,
            storage_gb: 500
          }
        }
      ];

      const mockInvoices: Invoice[] = [
        {
          invoice_id: 'inv_1',
          amount_due: 2900,
          amount_paid: 2900,
          status: 'paid',
          billing_period_start: '2024-02-01T00:00:00Z',
          billing_period_end: '2024-03-01T00:00:00Z',
          created_at: '2024-02-01T00:00:00Z',
          paid_at: '2024-02-01T10:30:00Z'
        },
        {
          invoice_id: 'inv_2',
          amount_due: 2900,
          amount_paid: 2900,
          status: 'paid',
          billing_period_start: '2024-01-01T00:00:00Z',
          billing_period_end: '2024-02-01T00:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
          paid_at: '2024-01-01T09:15:00Z'
        }
      ];

      setSubscriptionStatus(mockStatus);
      setAvailablePlans(mockPlans);
      setInvoices(mockInvoices);
    } catch (err) {
      setError('Failed to load subscription data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan: PricingPlan) => {
    setLoading(true);
    try {
      const response = await fetch('/api/subscription/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: plan.tier,
          billing_interval: billingInterval
        })
      });

      if (response.ok) {
        await loadSubscriptionData();
        setUpgradeDialogOpen(false);
        setSelectedPlan(null);
      } else {
        throw new Error('Upgrade failed');
      }
    } catch (err) {
      setError('Failed to upgrade subscription');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (immediate: boolean = false) => {
    setLoading(true);
    try {
      const response = await fetch('/api/subscription/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ immediate })
      });

      if (response.ok) {
        await loadSubscriptionData();
        setCancelDialogOpen(false);
      } else {
        throw new Error('Cancellation failed');
      }
    } catch (err) {
      setError('Failed to cancel subscription');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 70) return 'warning';
    return 'primary';
  };

  const renderCurrentPlan = () => {
    if (!subscriptionStatus) return null;

    const { plan, status, billing_interval, current_period_end, canceled_at } = subscriptionStatus;

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box>
              <Typography variant="h5" gutterBottom>
                Current Plan: {plan.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {plan.description}
              </Typography>
              <Chip 
                label={status.toUpperCase()} 
                color={status === 'active' ? 'success' : 'default'}
                size="small"
              />
            </Box>
            <Box textAlign="right">
              <Typography variant="h6">
                {formatPrice(billing_interval === 'yearly' ? plan.yearly_price : plan.monthly_price)}
                <Typography component="span" variant="body2" color="text.secondary">
                  /{billing_interval === 'yearly' ? 'year' : 'month'}
                </Typography>
              </Typography>
              {canceled_at && (
                <Typography variant="body2" color="error">
                  Cancels on {formatDate(canceled_at)}
                </Typography>
              )}
            </Box>
          </Box>

          {current_period_end && (
            <Typography variant="body2" color="text.secondary" mb={2}>
              Next billing date: {formatDate(current_period_end)}
            </Typography>
          )}

          <Box display="flex" gap={2}>
            {plan.tier !== 'enterprise' && !canceled_at && (
              <Button
                variant="contained"
                startIcon={<UpgradeIcon />}
                onClick={() => setUpgradeDialogOpen(true)}
              >
                Upgrade Plan
              </Button>
            )}
            {plan.tier !== 'free' && !canceled_at && (
              <Button
                variant="outlined"
                color="error"
                onClick={() => setCancelDialogOpen(true)}
              >
                Cancel Subscription
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<PaymentIcon />}
              onClick={() => {/* Open billing portal */}}
            >
              Manage Billing
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderUsageMetrics = () => {
    if (!subscriptionStatus) return null;

    const { usage, usage_percentages, limits } = subscriptionStatus;

    const metrics = [
      {
        name: 'Transcription Hours',
        key: 'transcription_hours',
        unit: 'hours',
        icon: '🎙️'
      },
      {
        name: 'API Calls',
        key: 'api_calls',
        unit: 'calls',
        icon: '🔌'
      },
      {
        name: 'Team Members',
        key: 'team_members',
        unit: 'members',
        icon: '👥'
      },
      {
        name: 'Storage',
        key: 'storage_gb',
        unit: 'GB',
        icon: '💾'
      }
    ];

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Usage This Period
          </Typography>
          
          <Grid container spacing={3}>
            {metrics.map((metric) => {
              const current = usage[metric.key] || 0;
              const limit = limits[metric.key];
              const percentage = usage_percentages[metric.key] || 0;
              const isUnlimited = limit === -1;

              return (
                <Grid item xs={12} sm={6} key={metric.key}>
                  <Box>
                    <Box display="flex" alignItems="center" mb={1}>
                      <Typography variant="body2" sx={{ mr: 1 }}>
                        {metric.icon}
                      </Typography>
                      <Typography variant="subtitle2">
                        {metric.name}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2">
                        {current.toLocaleString()} {metric.unit}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {isUnlimited ? 'Unlimited' : `${limit.toLocaleString()} ${metric.unit}`}
                      </Typography>
                    </Box>
                    
                    {!isUnlimited && (
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(percentage, 100)}
                        color={getUsageColor(percentage)}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    )}
                    
                    {percentage >= 90 && !isUnlimited && (
                      <Typography variant="caption" color="error" display="block" mt={0.5}>
                        ⚠️ Approaching limit
                      </Typography>
                    )}
                  </Box>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  const renderPricingPlans = () => {
    if (!subscriptionStatus) return null;

    const currentTier = subscriptionStatus.tier;

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Available Plans
          </Typography>
          
          <Grid container spacing={3}>
            {availablePlans.map((plan) => {
              const isCurrent = plan.tier === currentTier;
              const price = billingInterval === 'yearly' ? plan.yearly_price : plan.monthly_price;
              const savings = billingInterval === 'yearly' ? 
                ((plan.monthly_price * 12 - plan.yearly_price) / 100).toFixed(0) : 0;

              return (
                <Grid item xs={12} md={4} key={plan.tier}>
                  <Card 
                    variant={isCurrent ? "outlined" : "elevation"}
                    sx={{ 
                      height: '100%',
                      border: isCurrent ? 2 : 1,
                      borderColor: isCurrent ? 'primary.main' : 'divider',
                      position: 'relative'
                    }}
                  >
                    {isCurrent && (
                      <Chip
                        label="Current Plan"
                        color="primary"
                        size="small"
                        sx={{
                          position: 'absolute',
                          top: 16,
                          right: 16
                        }}
                      />
                    )}
                    
                    <CardContent>
                      <Box textAlign="center" mb={2}>
                        <Typography variant="h5" gutterBottom>
                          {plan.name}
                          {plan.tier === 'enterprise' && <BusinessIcon sx={{ ml: 1 }} />}
                          {plan.tier === 'pro' && <StarIcon sx={{ ml: 1, color: 'gold' }} />}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {plan.description}
                        </Typography>
                        
                        <Typography variant="h4" color="primary">
                          {formatPrice(price)}
                          <Typography component="span" variant="body2" color="text.secondary">
                            /{billingInterval === 'yearly' ? 'year' : 'month'}
                          </Typography>
                        </Typography>
                        
                        {billingInterval === 'yearly' && savings > 0 && (
                          <Typography variant="caption" color="success.main">
                            Save ${savings} per year
                          </Typography>
                        )}
                      </Box>
                      
                      <List dense>
                        {plan.features.map((feature, index) => (
                          <ListItem key={index} sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <CheckIcon color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={feature}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                      </List>
                      
                      <Box mt={2}>
                        {!isCurrent && plan.tier !== 'free' && (
                          <Button
                            fullWidth
                            variant="contained"
                            onClick={() => {
                              setSelectedPlan(plan);
                              setUpgradeDialogOpen(true);
                            }}
                            disabled={loading}
                          >
                            {plan.tier === 'enterprise' ? 'Contact Sales' : 'Upgrade'}
                          </Button>
                        )}
                        {isCurrent && (
                          <Button fullWidth variant="outlined" disabled>
                            Current Plan
                          </Button>
                        )}
                        {plan.tier === 'free' && currentTier !== 'free' && (
                          <Button fullWidth variant="outlined" disabled>
                            Downgrade to Free
                          </Button>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  const renderBillingHistory = () => {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Billing History
          </Typography>
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Period</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invoices.map((invoice) => (
                  <TableRow key={invoice.invoice_id}>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {invoice.invoice_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {formatPrice(invoice.amount_due)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={invoice.status.toUpperCase()}
                        color={invoice.status === 'paid' ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(invoice.billing_period_start)} - {formatDate(invoice.billing_period_end)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {formatDate(invoice.created_at)}
                    </TableCell>
                    <TableCell>
                      <Button size="small" variant="outlined">
                        Download
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    );
  };

  if (loading && !subscriptionStatus) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading subscription data...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Typography variant="h4" gutterBottom>
        Subscription & Billing
      </Typography>

      {/* Billing Interval Toggle */}
      <Box mb={3}>
        <FormControlLabel
          control={
            <Switch
              checked={billingInterval === 'yearly'}
              onChange={(e) => setBillingInterval(e.target.checked ? 'yearly' : 'monthly')}
            />
          }
          label={
            <Box display="flex" alignItems="center">
              <Typography>Annual Billing</Typography>
              <Chip label="Save 20%" color="success" size="small" sx={{ ml: 1 }} />
            </Box>
          }
        />
      </Box>

      {renderCurrentPlan()}
      {renderUsageMetrics()}
      {renderPricingPlans()}
      {renderBillingHistory()}

      {/* Upgrade Dialog */}
      <Dialog open={upgradeDialogOpen} onClose={() => setUpgradeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Upgrade to {selectedPlan?.name}
        </DialogTitle>
        <DialogContent>
          {selectedPlan && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {formatPrice(billingInterval === 'yearly' ? selectedPlan.yearly_price : selectedPlan.monthly_price)}
                /{billingInterval === 'yearly' ? 'year' : 'month'}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" paragraph>
                You'll be charged immediately and your billing cycle will restart.
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>
                What you'll get:
              </Typography>
              <List dense>
                {selectedPlan.features.map((feature, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={feature} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpgradeDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={() => selectedPlan && handleUpgrade(selectedPlan)}
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Upgrade Now'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Cancel Subscription
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Are you sure you want to cancel your subscription? You'll lose access to premium features.
            </Typography>
          </Alert>
          
          <Typography variant="body2" paragraph>
            Your subscription will remain active until the end of your current billing period 
            ({subscriptionStatus?.current_period_end && formatDate(subscriptionStatus.current_period_end)}).
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>
            Keep Subscription
          </Button>
          <Button 
            onClick={() => handleCancel(false)}
            color="error"
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Cancel at Period End'}
          </Button>
          <Button 
            onClick={() => handleCancel(true)}
            color="error"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Cancel Immediately'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SubscriptionManager;