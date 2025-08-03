import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Divider,
  Typography,
  Tag,
  List,
  Popconfirm,
  Tabs,
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  SettingOutlined,
  RocketOutlined
} from '@ant-design/icons';
import { apiClient } from '../../utils/api';
import { AgentStatus, CapabilityInfo, ProjectStatus } from '../../types';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface AgentControlPanelProps {
  onRefresh?: () => void;
}

const AgentControlPanel: React.FC<AgentControlPanelProps> = ({ onRefresh }) => {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [capabilities, setCapabilities] = useState<CapabilityInfo | null>(null);
  const [activeProjects, setActiveProjects] = useState<ProjectStatus[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Modal states
  const [createAgentVisible, setCreateAgentVisible] = useState(false);
  const [createProjectVisible, setCreateProjectVisible] = useState(false);
  const [taskExecuteVisible, setTaskExecuteVisible] = useState(false);
  
  // Forms
  const [createAgentForm] = Form.useForm();
  const [createProjectForm] = Form.useForm();
  const [taskForm] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [agentsResponse, capabilitiesResponse] = await Promise.all([
        apiClient.agents.listAgents(),
        apiClient.agents.getCapabilities()
      ]);
      
      setAgents(agentsResponse.data.agents);
      setCapabilities(capabilitiesResponse.data);
    } catch (error) {
      message.error('Failed to fetch agent data');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSystemControl = async (action: 'start' | 'stop' | 'restart') => {
    setLoading(true);
    try {
      await apiClient.agents.controlSystem(action);
      message.success(`System ${action}ed successfully`);
      await fetchData();
      onRefresh?.();
    } catch (error) {
      message.error(`Failed to ${action} system`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAgent = async (values: any) => {
    try {
      const response = await apiClient.agents.createAgent(
        values.agent_type,
        values.name,
        {
          optimization_enabled: values.optimization_enabled,
          ai_recommendations: values.ai_recommendations,
          safety_warnings: values.safety_warnings
        }
      );
      
      message.success(`Agent "${response.data.name}" created successfully`);
      setCreateAgentVisible(false);
      createAgentForm.resetFields();
      await fetchData();
      onRefresh?.();
    } catch (error) {
      message.error('Failed to create agent');
    }
  };

  const handleRestartAgent = async (agentId: string, agentName: string) => {
    try {
      await apiClient.agents.restartAgent(agentId);
      message.success(`Agent "${agentName}" restarted successfully`);
      await fetchData();
      onRefresh?.();
    } catch (error) {
      message.error(`Failed to restart agent "${agentName}"`);
    }
  };

  const handleDeleteAgent = async (agentId: string, agentName: string) => {
    try {
      await apiClient.agents.deleteAgent(agentId);
      message.success(`Agent "${agentName}" deleted successfully`);
      await fetchData();
      onRefresh?.();
    } catch (error) {
      message.error(`Failed to delete agent "${agentName}"`);
    }
  };

  const handleCreateProject = async (values: any) => {
    try {
      const tasks = [
        {
          name: values.task_name,
          description: values.task_description,
          type: values.task_type,
          capabilities: [values.required_capability],
          input: {
            span_length: values.span_length,
            joist_spacing: values.joist_spacing,
            building_level: values.building_level,
            room_type: values.room_type,
            load_type: values.load_type || 'residential'
          },
          priority: values.priority,
          estimated_duration: values.estimated_duration
        }
      ];

      const response = await apiClient.agents.createProject(
        values.project_name,
        values.project_description,
        tasks,
        {
          client: values.client_name,
          engineer: values.engineer_name
        }
      );

      message.success(`Project "${values.project_name}" created successfully`);
      setCreateProjectVisible(false);
      createProjectForm.resetFields();
    } catch (error) {
      message.error('Failed to create project');
    }
  };

  const handleExecuteTask = async (values: any) => {
    try {
      const response = await apiClient.agents.executeTask(
        values.agent_type,
        values.task_type,
        {
          span_length: values.span_length,
          joist_spacing: values.joist_spacing,
          building_level: values.building_level,
          room_type: values.room_type,
          load_type: values.load_type || 'residential'
        },
        values.priority
      );

      message.success('Task queued for execution');
      setTaskExecuteVisible(false);
      taskForm.resetFields();
    } catch (error) {
      message.error('Failed to execute task');
    }
  };

  const handleDemoCalculation = async () => {
    try {
      const response = await apiClient.agents.demoJoistCalculation();
      message.success(`Demo calculation started: ${response.data.project_id}`);
      message.info('Check the project tracker for results');
    } catch (error) {
      message.error('Failed to start demo calculation');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Agent Control Panel</Title>

      <Tabs defaultActiveKey="system">
        <TabPane tab="System Control" key="system">
          <Card title="System Operations" style={{ marginBottom: '24px' }}>
            <Space wrap>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => handleSystemControl('start')}
                loading={loading}
              >
                Start System
              </Button>
              <Button
                icon={<PauseCircleOutlined />}
                onClick={() => handleSystemControl('stop')}
                loading={loading}
              >
                Stop System
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => handleSystemControl('restart')}
                loading={loading}
              >
                Restart System
              </Button>
              <Button
                type="dashed"
                icon={<ExperimentOutlined />}
                onClick={handleDemoCalculation}
              >
                Run Demo Calculation
              </Button>
            </Space>
          </Card>

          <Card title="System Information">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <div>
                  <Text strong>Available Agent Types:</Text>
                  <div style={{ marginTop: '8px' }}>
                    {capabilities?.agent_types.map(type => (
                      <Tag key={type} color="blue" style={{ marginBottom: '4px' }}>
                        {type}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Col>
              <Col xs={24} md={12}>
                <div>
                  <Text strong>Available Capabilities:</Text>
                  <div style={{ marginTop: '8px' }}>
                    {capabilities?.capabilities.map(cap => (
                      <Tag key={cap} color="green" style={{ marginBottom: '4px' }}>
                        {cap}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="Agent Management" key="agents">
          <Card 
            title="Manage Agents" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => setCreateAgentVisible(true)}
              >
                Create Agent
              </Button>
            }
            style={{ marginBottom: '24px' }}
          >
            <List
              dataSource={agents}
              renderItem={(agent) => (
                <List.Item
                  actions={[
                    <Button 
                      size="small" 
                      icon={<ReloadOutlined />}
                      onClick={() => handleRestartAgent(agent.agent_id, agent.name)}
                    >
                      Restart
                    </Button>,
                    <Popconfirm
                      title="Are you sure you want to delete this agent?"
                      onConfirm={() => handleDeleteAgent(agent.agent_id, agent.name)}
                      okText="Yes"
                      cancelText="No"
                    >
                      <Button 
                        size="small" 
                        danger 
                        icon={<DeleteOutlined />}
                      >
                        Delete
                      </Button>
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        {agent.name}
                        <Tag color={agent.health === 'healthy' ? 'green' : 'red'}>
                          {agent.health}
                        </Tag>
                        <Tag color={agent.status === 'idle' ? 'default' : 'blue'}>
                          {agent.status}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary">
                          Tasks: {agent.performance.tasks_completed} completed, {agent.active_tasks} active
                        </Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          ID: {agent.agent_id}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </TabPane>

        <TabPane tab="Task Execution" key="tasks">
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card
                title="Quick Task Execution"
                extra={
                  <Button 
                    type="primary" 
                    icon={<RocketOutlined />}
                    onClick={() => setTaskExecuteVisible(true)}
                  >
                    Execute Task
                  </Button>
                }
              >
                <Text>Execute single tasks directly without creating a full project.</Text>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card
                title="Create Project"
                extra={
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setCreateProjectVisible(true)}
                  >
                    New Project
                  </Button>
                }
              >
                <Text>Create multi-task projects for complex calculations.</Text>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Create Agent Modal */}
      <Modal
        title="Create New Agent"
        open={createAgentVisible}
        onCancel={() => setCreateAgentVisible(false)}
        footer={null}
      >
        <Form
          form={createAgentForm}
          layout="vertical"
          onFinish={handleCreateAgent}
        >
          <Form.Item
            name="agent_type"
            label="Agent Type"
            rules={[{ required: true, message: 'Please select an agent type' }]}
          >
            <Select placeholder="Select agent type">
              {capabilities?.agent_types.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="Agent Name"
            rules={[{ required: true, message: 'Please enter an agent name' }]}
          >
            <Input placeholder="Enter agent name" />
          </Form.Item>

          <Divider>Configuration</Divider>

          <Form.Item name="optimization_enabled" label="Enable Optimization" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>

          <Form.Item name="ai_recommendations" label="AI Recommendations" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>

          <Form.Item name="safety_warnings" label="Safety Warnings" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Create Agent
              </Button>
              <Button onClick={() => setCreateAgentVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Execute Task Modal */}
      <Modal
        title="Execute Task"
        open={taskExecuteVisible}
        onCancel={() => setTaskExecuteVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={taskForm}
          layout="vertical"
          onFinish={handleExecuteTask}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="agent_type" label="Agent Type" rules={[{ required: true }]}>
                <Select>
                  {capabilities?.agent_types.map(type => (
                    <Option key={type} value={type}>{type}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="task_type" label="Task Type" rules={[{ required: true }]}>
                <Select>
                  {capabilities?.capabilities.map(cap => (
                    <Option key={cap} value={cap}>{cap}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Task Parameters</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item 
                name="span_length" 
                label="Span Length (m)" 
                rules={[{ required: true }]}
                initialValue={4.2}
              >
                <InputNumber min={1} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item 
                name="joist_spacing" 
                label="Joist Spacing (m)" 
                initialValue={0.45}
              >
                <Select>
                  <Option value={0.3}>300mm</Option>
                  <Option value={0.45}>450mm</Option>
                  <Option value={0.6}>600mm</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="building_level" label="Building Level" initialValue="L1">
                <Select>
                  <Option value="GF">Ground Floor</Option>
                  <Option value="L1">Level 1</Option>
                  <Option value="L2">Level 2</Option>
                  <Option value="RF">Roof</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="room_type" label="Room Type" initialValue="living">
                <Select>
                  <Option value="living">Living</Option>
                  <Option value="bedroom">Bedroom</Option>
                  <Option value="kitchen">Kitchen</Option>
                  <Option value="bathroom">Bathroom</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="priority" label="Priority" initialValue={2}>
            <Select>
              <Option value={1}>Low</Option>
              <Option value={2}>Medium</Option>
              <Option value={3}>High</Option>
              <Option value={4}>Critical</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Execute Task
              </Button>
              <Button onClick={() => setTaskExecuteVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Project Modal */}
      <Modal
        title="Create New Project"
        open={createProjectVisible}
        onCancel={() => setCreateProjectVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={createProjectForm}
          layout="vertical"
          onFinish={handleCreateProject}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="project_name" label="Project Name" rules={[{ required: true }]}>
                <Input placeholder="Enter project name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="client_name" label="Client Name">
                <Input placeholder="Enter client name" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="project_description" label="Description">
            <Input.TextArea placeholder="Enter project description" />
          </Form.Item>

          <Divider>Task Configuration</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="task_name" label="Task Name" rules={[{ required: true }]}>
                <Input placeholder="Enter task name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="task_type" label="Task Type" rules={[{ required: true }]}>
                <Select>
                  {capabilities?.capabilities.map(cap => (
                    <Option key={cap} value={cap}>{cap}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="task_description" label="Task Description">
            <Input.TextArea placeholder="Enter task description" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="span_length" label="Span Length (m)" initialValue={4.2}>
                <InputNumber min={1} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="joist_spacing" label="Spacing (m)" initialValue={0.45}>
                <Select>
                  <Option value={0.3}>300mm</Option>
                  <Option value={0.45}>450mm</Option>
                  <Option value={0.6}>600mm</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="building_level" label="Level" initialValue="L1">
                <Select>
                  <Option value="GF">Ground Floor</Option>
                  <Option value="L1">Level 1</Option>
                  <Option value="RF">Roof</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Create Project
              </Button>
              <Button onClick={() => setCreateProjectVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AgentControlPanel;