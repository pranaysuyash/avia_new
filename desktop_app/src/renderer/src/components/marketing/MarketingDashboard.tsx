import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, Tabs, Progress, List, Timeline } from 'antd';
import {
  RocketOutlined,
  MailOutlined,
  ShareAltOutlined,
  UserAddOutlined,
  LineChartOutlined,
  ExperimentOutlined,
  GiftOutlined
} from '@ant-design/icons';
import { Line, Column, Pie } from '@ant-design/charts';
import { apiClient, Campaign } from '../../services/apiClient';

const { TabPane } = Tabs;

const MarketingDashboard: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [growthMetrics, setGrowthMetrics] = useState<any>(null);
  const [referralStats, setReferralStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMarketingData();
  }, []);

  const loadMarketingData = async () => {
    try {
      setLoading(true);
      const [campaignsData, growthData, referralData] = await Promise.all([
        apiClient.getCampaigns(),
        apiClient.getGrowthMetrics(),
        apiClient.getReferralStats()
      ]);
      setCampaigns(campaignsData);
      setGrowthMetrics(growthData);
      setReferralStats(referralData);
    } catch (error) {
      console.error('Failed to load marketing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const campaignColumns = [
    {
      title: 'Campaign',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Campaign) => (
        <div>
          <strong>{text}</strong>
          <br />
          <Tag>{record.type}</Tag>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          draft: 'default',
          scheduled: 'blue',
          running: 'processing',
          paused: 'warning',
          completed: 'success'
        };
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Performance',
      key: 'performance',
      render: (_: any, record: Campaign) => (
        <Space direction="vertical" size="small">
          <span>CTR: {((record.metrics.clicks / record.metrics.impressions) * 100).toFixed(2)}%</span>
          <span>Conv: {record.metrics.conversions}</span>
        </Space>
      )
    },
    {
      title: 'Budget',
      key: 'budget',
      render: (_: any, record: Campaign) => (
        <div>
          <Progress 
            percent={Math.round((record.spent / record.budget) * 100)} 
            size="small"
            status={record.spent > record.budget ? 'exception' : 'active'}
          />
          <small>${record.spent} / ${record.budget}</small>
        </div>
      )
    },
    {
      title: 'ROI',
      dataIndex: ['metrics', 'roi'],
      key: 'roi',
      render: (roi: number) => (
        <Statistic
          value={roi}
          suffix="%"
          valueStyle={{ 
            color: roi > 0 ? '#3f8600' : '#cf1322',
            fontSize: '14px'
          }}
        />
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Campaign) => (
        <Space>
          <Button size="small" type="link">View</Button>
          <Button size="small" type="link">Edit</Button>
        </Space>
      )
    }
  ];

  const channelData = growthMetrics?.by_channel 
    ? Object.entries(growthMetrics.by_channel).map(([channel, data]: [string, any]) => ({
        channel,
        revenue: data.revenue,
        conversions: data.conversions
      }))
    : [];

  return (
    <div style={{ padding: '24px' }}>
      <h1>Marketing & Growth Dashboard</h1>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Campaigns"
              value={growthMetrics?.summary?.total_campaigns || 0}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Marketing Spend"
              value={growthMetrics?.summary?.total_spent || 0}
              prefix="$"
              precision={0}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Revenue Generated"
              value={growthMetrics?.summary?.total_revenue || 0}
              prefix="$"
              precision={0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Overall ROI"
              value={growthMetrics?.summary?.overall_roi || 0}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="campaigns">
        <TabPane
          tab={
            <span>
              <RocketOutlined />
              Campaigns
            </span>
          }
          key="campaigns"
        >
          <Card 
            title="Active Campaigns" 
            extra={
              <Space>
                <Button>Filter</Button>
                <Button type="primary">New Campaign</Button>
              </Space>
            }
          >
            <Table
              dataSource={campaigns}
              columns={campaignColumns}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <LineChartOutlined />
              Analytics
            </span>
          }
          key="analytics"
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="Revenue by Channel">
                {channelData.length > 0 && (
                  <Column
                    data={channelData}
                    xField="channel"
                    yField="revenue"
                    height={300}
                    label={{
                      position: 'top',
                      formatter: (v: any) => `$${(v.revenue / 1000).toFixed(0)}k`
                    }}
                  />
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Conversion Funnel">
                {growthMetrics?.funnel && (
                  <div style={{ padding: '20px' }}>
                    <Timeline>
                      {Object.entries(growthMetrics.funnel).map(([stage, value]) => (
                        <Timeline.Item key={stage}>
                          <strong>{stage}:</strong> {value as number}
                        </Timeline.Item>
                      ))}
                    </Timeline>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane
          tab={
            <span>
              <GiftOutlined />
              Referrals
            </span>
          }
          key="referrals"
        >
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Total Referrals"
                  value={referralStats?.total_referrals || 0}
                  prefix={<UserAddOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Successful Referrals"
                  value={referralStats?.successful_referrals || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Total Rewards"
                  value={referralStats?.total_rewards?.credits || 0}
                  prefix="$"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>

          <Card title="Referral Activity" style={{ marginTop: '16px' }}>
            <List
              dataSource={referralStats?.referrals || []}
              renderItem={(referral: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={`Referral Code: ${referral.code}`}
                    description={`Status: ${referral.status} | Created: ${new Date(referral.created_at).toLocaleDateString()}`}
                  />
                  <Tag color={referral.status === 'converted' ? 'success' : 'processing'}>
                    {referral.status}
                  </Tag>
                </List.Item>
              )}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <ExperimentOutlined />
              A/B Tests
            </span>
          }
          key="experiments"
        >
          <Card title="Running Experiments">
            <p>A/B testing interface coming soon...</p>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default MarketingDashboard;