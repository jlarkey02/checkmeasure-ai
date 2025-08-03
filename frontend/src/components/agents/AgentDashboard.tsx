import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Table, 
  Tag, 
  Progress, 
  Button, 
  Space, 
  Alert,
  Spin,
  Typography,
  Tooltip,
  Badge
} from 'antd';
import { 
  HeartTwoTone,
  WarningTwoTone,
  CheckCircleTwoTone,
  CloseCircleTwoTone,
  ReloadOutlined,
  ThunderboltOutlined,
  TeamOutlined,
  MessageOutlined,
  ProjectOutlined
} from '@ant-design/icons';
import { apiClient } from '../../utils/api';
import { SystemHealth, AgentStatus } from '../../types';

const { Title, Text } = Typography;

interface AgentDashboardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const AgentDashboard: React.FC<AgentDashboardProps> = ({ 
  autoRefresh = true, 
  refreshInterval = 5000 
}) => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchSystemData = async () => {
    try {
      const [healthResponse, agentsResponse] = await Promise.all([
        apiClient.agents.getSystemHealth(),
        apiClient.agents.listAgents()
      ]);
      
      setSystemHealth(healthResponse.data);
      setAgents(agentsResponse.data.agents);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch system data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchSystemData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return <HeartTwoTone twoToneColor="#52c41a" />;
      case 'degraded': return <WarningTwoTone twoToneColor="#faad14" />;
      case 'unhealthy': return <CloseCircleTwoTone twoToneColor="#f5222d" />;
      default: return <WarningTwoTone twoToneColor="#d9d9d9" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'default';
      case 'working': return 'processing';
      case 'completed': return 'success';
      case 'error': 
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': 
      case 'unresponsive': return 'error';
      default: return 'default';
    }
  };

  const agentColumns = [
    {
      title: 'Agent',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: AgentStatus) => (
        <Space>
          {getHealthIcon(record.health)}
          <Text strong>{name}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.agent_id.substring(0, 8)}...
          </Text>
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Health',
      dataIndex: 'health',
      key: 'health',
      render: (health: string) => (
        <Tag color={getHealthColor(health)}>
          {health.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Tasks',
      key: 'tasks',
      render: (record: AgentStatus) => (
        <Space>
          <Badge count={record.active_tasks} showZero color="blue">
            <Text>Active</Text>
          </Badge>
          <Text type="secondary">
            {record.performance.tasks_completed} completed
          </Text>
        </Space>
      ),
    },
    {
      title: 'Performance',
      key: 'performance',
      render: (record: AgentStatus) => {
        const total = record.performance.tasks_completed + record.performance.tasks_failed;
        const successRate = total > 0 ? (record.performance.tasks_completed / total) * 100 : 100;
        
        return (
          <Tooltip title={`Success Rate: ${successRate.toFixed(1)}%\nAvg Time: ${record.performance.average_processing_time.toFixed(1)}s`}>
            <Progress 
              percent={successRate} 
              size="small" 
              status={successRate > 90 ? "success" : successRate > 70 ? "normal" : "exception"}
              format={() => `${successRate.toFixed(0)}%`}
            />
          </Tooltip>
        );
      },
    },
    {
      title: 'Capabilities',
      dataIndex: 'capabilities',
      key: 'capabilities',
      render: (capabilities: string[]) => (
        <Space wrap>
          {capabilities.slice(0, 2).map(cap => (
            <Tag key={cap} color="geekblue">{cap}</Tag>
          ))}
          {capabilities.length > 2 && (
            <Tag color="default">+{capabilities.length - 2} more</Tag>
          )}
        </Space>
      ),
    },
  ];

  if (loading && !systemHealth) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '16px' }}>Loading agent system...</div>
        </div>
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Multi-Agent System Dashboard</Title>
        <Space>
          <Text type="secondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Text>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchSystemData}
            loading={loading}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {systemHealth && (
        <>
          {/* System Health Alert */}
          {systemHealth.overall_health !== 'healthy' && (
            <Alert
              message={`System Health: ${systemHealth.overall_health.toUpperCase()}`}
              description={`${systemHealth.unhealthy_agents} of ${systemHealth.total_agents} agents need attention`}
              type={systemHealth.overall_health === 'degraded' ? 'warning' : 'error'}
              showIcon
              style={{ marginBottom: '24px' }}
            />
          )}

          {/* System Overview Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="System Health"
                  value={systemHealth.overall_health}
                  prefix={getHealthIcon(systemHealth.overall_health)}
                  valueStyle={{ 
                    color: systemHealth.overall_health === 'healthy' ? '#3f8600' : 
                           systemHealth.overall_health === 'degraded' ? '#cf1322' : '#cf1322'
                  }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Active Agents"
                  value={systemHealth.healthy_agents}
                  suffix={`/ ${systemHealth.total_agents}`}
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Active Projects"
                  value={systemHealth.orchestrator_metrics.active_projects}
                  prefix={<ProjectOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Messages Sent"
                  value={systemHealth.event_bus_metrics.messages_sent}
                  prefix={<MessageOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Performance Metrics */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} md={12}>
              <Card title="Event Bus Performance" size="small">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Success Rate"
                      value={
                        systemHealth.event_bus_metrics.messages_sent > 0
                          ? ((systemHealth.event_bus_metrics.messages_sent - systemHealth.event_bus_metrics.messages_failed) / systemHealth.event_bus_metrics.messages_sent * 100)
                          : 100
                      }
                      precision={1}
                      suffix="%"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Avg Delivery Time"
                      value={systemHealth.event_bus_metrics.average_delivery_time * 1000}
                      precision={0}
                      suffix="ms"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card title="Project Orchestrator" size="small">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Completed"
                      value={systemHealth.orchestrator_metrics.projects_completed}
                      valueStyle={{ fontSize: '16px', color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Tasks Executed"
                      value={systemHealth.orchestrator_metrics.total_tasks_executed}
                      valueStyle={{ fontSize: '16px', color: '#1890ff' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* Agents Table */}
          <Card title="Agent Status" style={{ marginBottom: '24px' }}>
            <Table
              dataSource={agents}
              columns={agentColumns}
              rowKey="agent_id"
              pagination={false}
              size="small"
            />
          </Card>

          {/* Capabilities Overview */}
          <Card title="Available Capabilities" size="small">
            <Text>
              <strong>{systemHealth.available_capabilities}</strong> capabilities available across{' '}
              <strong>{systemHealth.available_agent_types}</strong> agent types
            </Text>
          </Card>
        </>
      )}
    </div>
  );
};

export default AgentDashboard;