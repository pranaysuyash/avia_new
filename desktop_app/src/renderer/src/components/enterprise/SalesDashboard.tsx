import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Progress, Tag, Button, Space, Spin } from 'antd';
import {
  DollarOutlined,
  UserAddOutlined,
  RiseOutlined,
  TeamOutlined,
  TrophyOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { Line, Funnel, Pie } from '@ant-design/charts';
import { apiClient, PipelineMetrics, Lead, LeadStatus } from '../../services/apiClient';

const SalesDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [metricsData, leadsData] = await Promise.all([
        apiClient.getPipelineMetrics(),
        apiClient.getLeads()
      ]);
      setMetrics(metricsData);
      setLeads(leadsData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const leadColumns = [
    {
      title: 'Company',
      dataIndex: 'company_name',
      key: 'company_name',
      render: (text: string, record: Lead) => (
        <div>
          <strong>{text}</strong>
          <br />
          <small>{record.contact_name}</small>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: LeadStatus) => {
        const colors: Record<LeadStatus, string> = {
          [LeadStatus.NEW]: 'blue',
          [LeadStatus.CONTACTED]: 'gold',
          [LeadStatus.QUALIFIED]: 'green',
          [LeadStatus.PROPOSAL]: 'orange',
          [LeadStatus.NEGOTIATION]: 'purple',
          [LeadStatus.CLOSED_WON]: 'success',
          [LeadStatus.CLOSED_LOST]: 'error'
        };
        return <Tag color={colors[status]}>{status.replace('_', ' ').toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => <Progress percent={score} size="small" />
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => {
        const colors = { low: 'default', medium: 'warning', high: 'error' };
        return <Tag color={colors[priority as keyof typeof colors]}>{priority.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Lead) => (
        <Space>
          <Button size="small" type="link">View</Button>
          <Button size="small" type="link">Activity</Button>
        </Space>
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Loading sales dashboard..." />
      </div>
    );
  }

  const funnelData = metrics?.opportunities_by_stage
    ? Object.entries(metrics.opportunities_by_stage || {}).map(([stage, value]) => ({
        stage,
        value: value as number
      }))
    : [];

  return (
    <div style={{ padding: '24px' }}>
      <h1>Sales Dashboard</h1>
      
      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Pipeline"
              value={metrics?.total_pipeline_value || 0}
              prefix={<DollarOutlined />}
              precision={0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Leads"
              value={metrics?.total_leads || 0}
              prefix={<UserAddOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Win Rate"
              value={metrics?.win_rate || 0}
              suffix="%"
              prefix={<TrophyOutlined />}
              precision={1}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Sales Velocity"
              value={metrics?.sales_velocity?.velocity || 0}
              prefix={<RiseOutlined />}
              suffix="/day"
              precision={0}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <Card title="Sales Pipeline">
            {funnelData.length > 0 && (
              <Funnel
                data={funnelData}
                xField="stage"
                yField="value"
                height={300}
                label={{
                  formatter: (datum: any) => `$${(datum.value / 1000).toFixed(0)}k`
                }}
              />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Revenue Forecast">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="This Month"
                  value={metrics?.forecast?.current_month || 0}
                  prefix="$"
                  precision={0}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Next Month"
                  value={metrics?.forecast?.next_month || 0}
                  prefix="$"
                  precision={0}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="This Quarter"
                  value={metrics?.forecast?.current_quarter || 0}
                  prefix="$"
                  precision={0}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Recent Leads */}
      <Card title="Recent Leads" extra={<Button type="primary">Add Lead</Button>}>
        <Table
          dataSource={leads.slice(0, 10)}
          columns={leadColumns}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default SalesDashboard;