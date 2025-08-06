import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Table, Tag, Button, Space, Tabs, List, Modal, Form, Input, Select, InputNumber, Alert, Typography, Divider } from 'antd';
import {
  ApiOutlined,
  KeyOutlined,
  LinkOutlined,
  CodeOutlined,
  BarChartOutlined,
  PlusOutlined,
  CopyOutlined,
  DeleteOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { Line } from '@ant-design/charts';
import { apiClient, ApiKey, Webhook } from '../../services/apiClient';

const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const DeveloperPortal: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [sdks, setSdks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [newApiKey, setNewApiKey] = useState<string>('');

  const [form] = Form.useForm();
  const [webhookForm] = Form.useForm();

  useEffect(() => {
    loadDeveloperData();
  }, []);

  const loadDeveloperData = async () => {
    try {
      setLoading(true);
      const [keysData, webhooksData, usageData, sdksData] = await Promise.all([
        apiClient.getApiKeys(),
        apiClient.getWebhooks(),
        apiClient.getApiUsage(),
        apiClient.getSdks()
      ]);
      setApiKeys(keysData);
      setWebhooks(webhooksData);
      setUsage(usageData);
      setSdks(sdksData);
    } catch (error) {
      console.error('Failed to load developer data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async (values: any) => {
    try {
      const response = await apiClient.createApiKey(values);
      setNewApiKey(response.key);
      await loadDeveloperData();
      form.resetFields();
    } catch (error) {
      console.error('Failed to create API key:', error);
    }
  };

  const handleRevokeApiKey = async (keyId: string) => {
    Modal.confirm({
      title: 'Revoke API Key',
      content: 'Are you sure you want to revoke this API key? This action cannot be undone.',
      okText: 'Revoke',
      okType: 'danger',
      onOk: async () => {
        try {
          await apiClient.revokeApiKey(keyId);
          await loadDeveloperData();
        } catch (error) {
          console.error('Failed to revoke API key:', error);
        }
      }
    });
  };

  const handleCreateWebhook = async (values: any) => {
    try {
      await apiClient.createWebhook(values);
      setShowWebhookModal(false);
      webhookForm.resetFields();
      await loadDeveloperData();
    } catch (error) {
      console.error('Failed to create webhook:', error);
    }
  };

  const apiKeyColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: 'Key ID',
      dataIndex: 'key_id',
      key: 'key_id',
      render: (text: string) => <Text code>{text.substring(0, 8)}...</Text>
    },
    {
      title: 'Scopes',
      dataIndex: 'scopes',
      key: 'scopes',
      render: (scopes: string[]) => (
        <Space wrap>
          {scopes.map(scope => (
            <Tag key={scope}>{scope}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Rate Limit',
      dataIndex: 'rate_limit',
      key: 'rate_limit',
      render: (limit: number) => `${limit}/hour`
    },
    {
      title: 'Last Used',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : 'Never'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: ApiKey) => (
        <Space>
          <Button 
            size="small" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleRevokeApiKey(record.key_id)}
          >
            Revoke
          </Button>
        </Space>
      )
    }
  ];

  const webhookColumns = [
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true
    },
    {
      title: 'Events',
      dataIndex: 'events',
      key: 'events',
      render: (events: string[]) => (
        <Space wrap>
          {events.map(event => (
            <Tag key={event}>{event}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Failures',
      dataIndex: 'failure_count',
      key: 'failure_count',
      render: (count: number) => (
        <Tag color={count > 5 ? 'error' : 'default'}>{count}</Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Webhook) => (
        <Space>
          <Button size="small">Test</Button>
          <Button size="small">Edit</Button>
          <Button size="small" danger>Delete</Button>
        </Space>
      )
    }
  ];

  const usageData = usage?.usage_by_period 
    ? Object.entries(usage.usage_by_period).map(([period, data]: [string, any]) => ({
        date: period,
        requests: data.requests,
        errors: data.errors
      }))
    : [];

  return (
    <div style={{ padding: '24px' }}>
      <h1>Developer Portal</h1>

      {/* API Usage Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Space direction="vertical" align="center" style={{ width: '100%' }}>
              <BarChartOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              <Text type="secondary">Total Requests</Text>
              <Title level={3}>{usage?.total_requests || 0}</Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" align="center" style={{ width: '100%' }}>
              <ApiOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
              <Text type="secondary">Active API Keys</Text>
              <Title level={3}>{apiKeys.length}</Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" align="center" style={{ width: '100%' }}>
              <LinkOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />
              <Text type="secondary">Active Webhooks</Text>
              <Title level={3}>{webhooks.filter(w => w.is_active).length}</Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" align="center" style={{ width: '100%' }}>
              <Text type="secondary">Error Rate</Text>
              <Title level={3}>{usage?.error_rate?.toFixed(2) || 0}%</Title>
            </Space>
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="keys">
        <TabPane
          tab={
            <span>
              <KeyOutlined />
              API Keys
            </span>
          }
          key="keys"
        >
          <Card 
            title="API Keys" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => setShowApiKeyModal(true)}
              >
                Create API Key
              </Button>
            }
          >
            <Table
              dataSource={apiKeys}
              columns={apiKeyColumns}
              rowKey="key_id"
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <LinkOutlined />
              Webhooks
            </span>
          }
          key="webhooks"
        >
          <Card 
            title="Webhooks" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => setShowWebhookModal(true)}
              >
                Create Webhook
              </Button>
            }
          >
            <Table
              dataSource={webhooks}
              columns={webhookColumns}
              rowKey="webhook_id"
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              Usage
            </span>
          }
          key="usage"
        >
          <Card title="API Usage Over Time">
            {usageData.length > 0 && (
              <Line
                data={usageData}
                xField="date"
                yField="requests"
                height={300}
                smooth
                point={{ size: 5 }}
                label={{
                  style: { fill: '#aaa' }
                }}
              />
            )}
          </Card>

          <Card title="Top Endpoints" style={{ marginTop: '16px' }}>
            <List
              dataSource={Object.entries(usage?.top_endpoints || {})}
              renderItem={([endpoint, data]: [string, any]) => (
                <List.Item>
                  <List.Item.Meta
                    title={endpoint}
                    description={`${data.count} requests | ${data.avg_response_time.toFixed(0)}ms avg`}
                  />
                  <Tag color={data.errors > 0 ? 'error' : 'success'}>
                    {data.errors} errors
                  </Tag>
                </List.Item>
              )}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <CodeOutlined />
              SDKs & Docs
            </span>
          }
          key="sdks"
        >
          <Row gutter={[16, 16]}>
            {sdks.map(sdk => (
              <Col span={12} key={sdk.language}>
                <Card 
                  title={`${sdk.language} SDK`}
                  extra={<Tag color="blue">v{sdk.version}</Tag>}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Button 
                      type="primary" 
                      href={sdk.download_url}
                      target="_blank"
                      block
                    >
                      Download
                    </Button>
                    <Button href={sdk.documentation_url} target="_blank" block>
                      Documentation
                    </Button>
                    <Button href={sdk.examples_url} target="_blank" block>
                      Examples
                    </Button>
                    <Text type="secondary">
                      Last updated: {new Date(sdk.last_updated).toLocaleDateString()}
                    </Text>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>
      </Tabs>

      {/* Create API Key Modal */}
      <Modal
        title="Create API Key"
        visible={showApiKeyModal}
        onCancel={() => {
          setShowApiKeyModal(false);
          setNewApiKey('');
          form.resetFields();
        }}
        footer={null}
      >
        {newApiKey ? (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message="API Key Created Successfully"
              description="Make sure to copy your API key now. You won't be able to see it again!"
              type="success"
              showIcon
            />
            <Input.Group compact>
              <Input value={newApiKey} readOnly style={{ width: 'calc(100% - 32px)' }} />
              <Button 
                icon={<CopyOutlined />}
                onClick={() => {
                  navigator.clipboard.writeText(newApiKey);
                }}
              />
            </Input.Group>
            <Button 
              type="primary" 
              block
              onClick={() => {
                setShowApiKeyModal(false);
                setNewApiKey('');
              }}
            >
              Done
            </Button>
          </Space>
        ) : (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateApiKey}
          >
            <Form.Item
              name="name"
              label="Key Name"
              rules={[{ required: true, message: 'Please enter a name' }]}
            >
              <Input placeholder="Production API Key" />
            </Form.Item>

            <Form.Item
              name="scopes"
              label="Scopes"
              rules={[{ required: true, message: 'Please select scopes' }]}
            >
              <Select mode="multiple" placeholder="Select scopes">
                <Select.Option value="read">Read</Select.Option>
                <Select.Option value="write">Write</Select.Option>
                <Select.Option value="delete">Delete</Select.Option>
                <Select.Option value="admin">Admin</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="rate_limit"
              label="Rate Limit (requests/hour)"
              initialValue={1000}
            >
              <InputNumber min={100} max={10000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="description"
              label="Description"
            >
              <TextArea rows={2} placeholder="Optional description" />
            </Form.Item>

            <Form.Item>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button onClick={() => setShowApiKeyModal(false)}>Cancel</Button>
                <Button type="primary" htmlType="submit">Create</Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Create Webhook Modal */}
      <Modal
        title="Create Webhook"
        visible={showWebhookModal}
        onCancel={() => {
          setShowWebhookModal(false);
          webhookForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={webhookForm}
          layout="vertical"
          onFinish={handleCreateWebhook}
        >
          <Form.Item
            name="url"
            label="Webhook URL"
            rules={[
              { required: true, message: 'Please enter a URL' },
              { type: 'url', message: 'Please enter a valid URL' }
            ]}
          >
            <Input placeholder="https://your-server.com/webhook" />
          </Form.Item>

          <Form.Item
            name="events"
            label="Events"
            rules={[{ required: true, message: 'Please select events' }]}
          >
            <Select mode="multiple" placeholder="Select events to subscribe">
              <Select.Option value="transcription.completed">Transcription Completed</Select.Option>
              <Select.Option value="transcription.failed">Transcription Failed</Select.Option>
              <Select.Option value="lead.created">Lead Created</Select.Option>
              <Select.Option value="ticket.created">Ticket Created</Select.Option>
              <Select.Option value="campaign.completed">Campaign Completed</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={2} placeholder="Optional description" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setShowWebhookModal(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit">Create</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DeveloperPortal;