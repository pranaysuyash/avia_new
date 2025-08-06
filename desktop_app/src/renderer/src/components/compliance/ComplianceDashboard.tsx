import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, Tabs, List, Alert, Progress, Timeline } from 'antd';
import {
  SafetyOutlined,
  AuditOutlined,
  LockOutlined,
  FileProtectOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  UserOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { apiClient, ConsentRecord, AuditLog } from '../../services/apiClient';

const { TabPane } = Tabs;

const ComplianceDashboard: React.FC = () => {
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [securityPosture, setSecurityPosture] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadComplianceData();
  }, []);

  const loadComplianceData = async () => {
    try {
      setLoading(true);
      const [consentsData, posture] = await Promise.all([
        apiClient.getMyConsents(),
        apiClient.getSecurityPosture()
      ]);
      setConsents(consentsData);
      setSecurityPosture(posture);
      
      // Load audit logs if admin
      try {
        const logs = await apiClient.getAuditLogs({ limit: 100 });
        setAuditLogs(logs.logs);
      } catch (error) {
        // Not admin, skip audit logs
      }
    } catch (error) {
      console.error('Failed to load compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const consentColumns = [
    {
      title: 'Purpose',
      dataIndex: 'purpose',
      key: 'purpose',
      render: (text: string) => <strong>{text}</strong>
    },
    {
      title: 'Data Categories',
      dataIndex: 'data_categories',
      key: 'data_categories',
      render: (categories: string[]) => (
        <Space>
          {categories.map(cat => (
            <Tag key={cat}>{cat}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: any, record: ConsentRecord) => {
        if (record.is_withdrawn) {
          return <Tag color="error">Withdrawn</Tag>;
        }
        const now = new Date();
        const validUntil = new Date(record.valid_until);
        if (validUntil < now) {
          return <Tag color="warning">Expired</Tag>;
        }
        return <Tag color="success">Active</Tag>;
      }
    },
    {
      title: 'Valid Until',
      dataIndex: 'valid_until',
      key: 'valid_until',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: ConsentRecord) => (
        <Space>
          {!record.is_withdrawn && (
            <Button 
              size="small" 
              danger
              onClick={() => handleWithdrawConsent(record.id)}
            >
              Withdraw
            </Button>
          )}
        </Space>
      )
    }
  ];

  const auditColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: 'Event',
      dataIndex: 'event_type',
      key: 'event_type',
      render: (type: string) => <Tag>{type}</Tag>
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: 'Actor',
      dataIndex: 'actor_id',
      key: 'actor_id',
      render: (id: string) => <UserOutlined /> 
    },
    {
      title: 'Risk',
      dataIndex: 'risk_score',
      key: 'risk_score',
      render: (score: number) => {
        let color = 'success';
        if (score > 70) color = 'error';
        else if (score > 40) color = 'warning';
        return <Tag color={color}>{score}</Tag>;
      }
    }
  ];

  const handleWithdrawConsent = async (consentId: string) => {
    try {
      await apiClient.withdrawConsent(consentId);
      await loadComplianceData(); // Reload data
    } catch (error) {
      console.error('Failed to withdraw consent:', error);
    }
  };

  const handleExportData = async () => {
    try {
      const data = await apiClient.exportMyData('json');
      // Create download link
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'my_data_export.json';
      a.click();
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1>Compliance & Security Dashboard</h1>

      {/* Security Posture Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Security Score"
              value={securityPosture?.overall_score || 0}
              suffix="/100"
              prefix={<SafetyOutlined />}
              valueStyle={{ color: securityPosture?.overall_score > 80 ? '#52c41a' : '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Consents"
              value={consents.filter(c => !c.is_withdrawn).length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Compliance Status"
              value="GDPR"
              valueStyle={{ color: '#52c41a', fontSize: '20px' }}
              prefix={<GlobalOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Last Audit"
              value="2 days ago"
              prefix={<AuditOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="privacy">
        <TabPane
          tab={
            <span>
              <FileProtectOutlined />
              Privacy & Consent
            </span>
          }
          key="privacy"
        >
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="Your Privacy Rights"
              description="You have the right to access, rectify, delete, and port your data. You can also withdraw consent at any time."
              type="info"
              showIcon
              action={
                <Space>
                  <Button onClick={handleExportData}>Export My Data</Button>
                  <Button>Request Deletion</Button>
                </Space>
              }
            />

            <Card title="Consent Records">
              <Table
                dataSource={consents}
                columns={consentColumns}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
              />
            </Card>
          </Space>
        </TabPane>

        <TabPane
          tab={
            <span>
              <AuditOutlined />
              Audit Logs
            </span>
          }
          key="audit"
        >
          <Card 
            title="Recent Activity" 
            extra={
              <Space>
                <Button>Filter</Button>
                <Button>Export</Button>
              </Space>
            }
          >
            {auditLogs.length > 0 ? (
              <Table
                dataSource={auditLogs}
                columns={auditColumns}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 20 }}
              />
            ) : (
              <Alert
                message="Access Restricted"
                description="Audit logs are only available to administrators."
                type="warning"
                showIcon
              />
            )}
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <LockOutlined />
              Security
            </span>
          }
          key="security"
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="Security Posture">
                {securityPosture && (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <strong>Overall Score</strong>
                      <Progress 
                        percent={securityPosture.overall_score} 
                        status={securityPosture.overall_score > 80 ? 'success' : 'exception'}
                      />
                    </div>
                    
                    {Object.entries(securityPosture.categories || {}).map(([category, score]) => (
                      <div key={category}>
                        <strong>{category}</strong>
                        <Progress 
                          percent={score as number} 
                          size="small"
                          status={(score as number) > 70 ? 'success' : 'exception'}
                        />
                      </div>
                    ))}
                  </Space>
                )}
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="Security Recommendations">
                <List
                  dataSource={securityPosture?.recommendations || []}
                  renderItem={(item: any) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          item.severity === 'high' 
                            ? <WarningOutlined style={{ color: '#ff4d4f' }} />
                            : <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        }
                        title={item.title}
                        description={item.description}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>

          <Card title="Data Retention" style={{ marginTop: '16px' }}>
            <Timeline>
              <Timeline.Item color="green">
                <strong>Transcripts:</strong> Retained for 90 days
              </Timeline.Item>
              <Timeline.Item color="blue">
                <strong>Analytics Data:</strong> Retained for 1 year
              </Timeline.Item>
              <Timeline.Item color="orange">
                <strong>User Data:</strong> Retained until account deletion
              </Timeline.Item>
              <Timeline.Item color="red">
                <strong>Audit Logs:</strong> Retained for 7 years (compliance requirement)
              </Timeline.Item>
            </Timeline>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ComplianceDashboard;