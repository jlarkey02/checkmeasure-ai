import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Menu, 
  Typography, 
  Space, 
  Card, 
  Upload, 
  Button, 
  message, 
  Row, 
  Col, 
  // Tabs, // Removed - not used
  Badge,
  Alert
} from 'antd';
import { 
  InboxOutlined, 
  FilePdfOutlined, 
  DashboardOutlined,
  ControlOutlined,
  CalculatorOutlined,
  RobotOutlined,
  ExperimentOutlined,
  FileSearchOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import SimplePDFViewer from './components/pdf-viewer/SimplePDFViewer';
import CalculationPanel from './components/CalculationPanel';
import ResultsDisplay from './components/ResultsDisplay';
import AgentDashboard from './components/agents/AgentDashboard';
import AgentControlPanel from './components/agents/AgentControlPanel';
import MeasurementExtractionDemo from './components/MeasurementExtractionDemo';
import { apiClient } from './utils/api';
import api from './utils/api';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;
const { Dragger } = Upload;
// const { TabPane } = Tabs; // Removed - not used

type ViewMode = 'traditional' | 'multi-agent' | 'dashboard' | 'control' | 'measurement-extraction';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>('traditional');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [selections, setSelections] = useState<any[]>([]);
  const [dashboardKey, setDashboardKey] = useState(0);
  const [backendHealthy, setBackendHealthy] = useState(true);

  // Keep-alive mechanism to prevent backend idle timeout
  useEffect(() => {
    let keepAliveInterval: NodeJS.Timeout;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 3;

    const checkBackendHealth = async () => {
      try {
        await api.get('/health');
        if (!backendHealthy) {
          setBackendHealthy(true);
          message.success('Backend connection restored');
          reconnectAttempts = 0;
        }
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendHealthy(false);
        
        // Try to reconnect a few times before giving up
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          message.warning(`Backend connection lost. Retrying... (${reconnectAttempts}/${maxReconnectAttempts})`);
        } else {
          message.error('Backend connection lost. Please refresh the page or restart the server.');
        }
      }
    };

    // Initial health check after a short delay to let backend fully start
    setTimeout(() => {
      checkBackendHealth();
    }, 1000);

    // Set up keep-alive interval - ping every 60 seconds (less aggressive)
    keepAliveInterval = setInterval(() => {
      checkBackendHealth();
    }, 60000);

    // Cleanup on unmount
    return () => {
      clearInterval(keepAliveInterval);
    };
  }, [backendHealthy]); // Added missing dependency

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf',
    showUploadList: false,
    beforeUpload: (file) => {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        message.error('You can only upload PDF files!');
        return false;
      }
      
      setLoading(true);
      setTimeout(() => {
        setPdfFile(file);
        setLoading(false);
        message.success(`${file.name} loaded successfully`);
      }, 500);
      
      return false;
    },
  };

  const handleReset = () => {
    setPdfFile(null);
    setResults(null);
    setSelections([]);
  };

  const handleSelectionsChange = (newSelections: any[]) => {
    setSelections(newSelections);
  };

  const handleCalculate = async (values: any) => {
    setCalculating(true);
    setResults(null);
    
    try {
      const response = await apiClient.calculateJoists(values);
      setResults(response.data);
      message.success('Calculation completed successfully!');
    } catch (error) {
      message.error('Calculation failed');
      console.error('Error:', error);
    } finally {
      setCalculating(false);
    }
  };

  const handleMultiAgentCalculate = async (values: any) => {
    setCalculating(true);
    setResults(null);
    
    try {
      // Execute via multi-agent system
      const response = await apiClient.agents.executeTask(
        'joist_calculation',
        'joist_calculation',
        values,
        3 // high priority
      );
      
      const projectId = response.data.project_id;
      message.success('Multi-agent calculation started!');
      message.loading('Processing with AI-enhanced calculation...', 0);
      
      // Poll for results
      await pollForResults(projectId);
      
      // Refresh dashboard
      setDashboardKey(prev => prev + 1);
      
    } catch (error) {
      message.error('Multi-agent calculation failed');
      console.error('Error:', error);
      setCalculating(false);
    }
  };

  const pollForResults = async (projectId: string) => {
    const maxAttempts = 30; // 30 seconds timeout
    let attempts = 0;
    
    const poll = async (): Promise<void> => {
      try {
        attempts++;
        const statusResponse = await apiClient.agents.getProjectStatus(projectId);
        const status = statusResponse.data;
        
        if (status.status === 'completed') {
          // Get the detailed results
          const resultsResponse = await apiClient.agents.getProjectResults(projectId);
          const projectResults = resultsResponse.data;
          
          if (projectResults.results && projectResults.results.length > 0) {
            // Extract the calculation result from the first completed task
            const calculationResult = projectResults.results[0].output_data;
            setResults({
              ...calculationResult,
              isMultiAgent: true,
              projectId: projectId,
              projectName: projectResults.project_name
            });
            message.destroy(); // Clear loading message
            message.success('AI-enhanced calculation completed!');
            setCalculating(false);
            return;
          }
        } else if (status.status === 'failed') {
          message.destroy();
          message.error('Multi-agent calculation failed');
          setCalculating(false);
          return;
        }
        
        // Continue polling if not completed and within timeout
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // Poll every second
        } else {
          message.destroy();
          message.warning('Calculation timeout - check dashboard for results');
          setCalculating(false);
        }
      } catch (error) {
        console.error('Error polling for results:', error);
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000);
        } else {
          message.destroy();
          message.error('Error retrieving calculation results');
          setCalculating(false);
        }
      }
    };
    
    poll();
  };

  const handleDemoCalculation = async () => {
    try {
      await apiClient.agents.demoJoistCalculation();
      message.success('Demo calculation started!');
      message.info('Check the dashboard for results');
      setDashboardKey(prev => prev + 1);
    } catch (error) {
      message.error('Demo calculation failed');
    }
  };

  const refreshDashboard = () => {
    setDashboardKey(prev => prev + 1);
  };

  const menuItems = [
    {
      key: 'traditional',
      icon: <CalculatorOutlined />,
      label: 'Traditional Calculations',
    },
    {
      key: 'multi-agent',
      icon: <RobotOutlined />,
      label: 'Multi-Agent System',
    },
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Agent Dashboard',
    },
    {
      key: 'control',
      icon: <ControlOutlined />,
      label: 'Agent Control',
    },
    {
      key: 'measurement-extraction',
      icon: <FileSearchOutlined />,
      label: 'Measurement Extraction',
    },
  ];

  const renderTraditionalView = () => (
    <div style={{ padding: '24px' }}>
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="PDF Upload" style={{ height: '100%' }}>
            {!pdfFile ? (
              <Dragger {...uploadProps} style={{ minHeight: '200px' }}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">Click or drag PDF file to this area to upload</p>
                <p className="ant-upload-hint">
                  Upload architectural drawings for analysis and measurement extraction
                </p>
              </Dragger>
            ) : (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <FilePdfOutlined style={{ fontSize: 24, marginRight: 8, color: '#ff4d4f' }} />
                  <Text strong>{pdfFile.name}</Text>
                </div>
                <SimplePDFViewer 
                  file={pdfFile} 
                  onSelectionsChange={handleSelectionsChange}
                />
                <Button onClick={handleReset} style={{ marginTop: 16 }}>
                  Upload Different File
                </Button>
              </div>
            )}
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <CalculationPanel 
              onCalculate={handleCalculate}
              calculating={calculating}
              pdfFile={pdfFile}
              selections={selections}
            />
            
            {results && (
              <ResultsDisplay results={results} />
            )}
          </Space>
        </Col>
      </Row>
    </div>
  );

  const renderMultiAgentView = () => (
    <div style={{ padding: '24px' }}>
      <Alert
        message="Multi-Agent Enhanced Calculations"
        description="Experience AI-powered construction calculations with advanced optimization, cost analysis, and environmental impact assessment."
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />
      
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="Enhanced PDF Analysis" style={{ height: '100%' }}>
            {!pdfFile ? (
              <Dragger {...uploadProps} style={{ minHeight: '200px' }}>
                <p className="ant-upload-drag-icon">
                  <RobotOutlined />
                </p>
                <p className="ant-upload-text">Upload PDF for AI-Enhanced Analysis</p>
                <p className="ant-upload-hint">
                  Multi-agent system provides advanced scale detection, measurement extraction, and optimization
                </p>
              </Dragger>
            ) : (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <FilePdfOutlined style={{ fontSize: 24, marginRight: 8, color: '#ff4d4f' }} />
                  <Text strong>{pdfFile.name}</Text>
                  <Badge count="AI Enhanced" style={{ marginLeft: 8 }} />
                </div>
                <SimplePDFViewer 
                  file={pdfFile} 
                  onSelectionsChange={handleSelectionsChange}
                />
                <Button onClick={handleReset} style={{ marginTop: 16 }}>
                  Upload Different File
                </Button>
              </div>
            )}
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Card title="AI-Enhanced Calculation Panel">
              <CalculationPanel 
                onCalculate={handleMultiAgentCalculate}
                calculating={calculating}
                pdfFile={pdfFile}
                selections={selections}
                isMultiAgent={true}
              />
            </Card>
            
            <Card title="Quick Actions">
              <Space wrap>
                <Button 
                  type="primary" 
                  icon={<ExperimentOutlined />}
                  onClick={handleDemoCalculation}
                >
                  Run Demo Calculation
                </Button>
                <Button 
                  icon={<DashboardOutlined />}
                  onClick={() => setCurrentView('dashboard')}
                >
                  View Dashboard
                </Button>
              </Space>
            </Card>
            
            {results && (
              <ResultsDisplay results={results} isMultiAgent={true} />
            )}
          </Space>
        </Col>
      </Row>
    </div>
  );

  const renderContent = () => {
    switch (currentView) {
      case 'traditional':
        return renderTraditionalView();
      case 'multi-agent':
        return renderMultiAgentView();
      case 'dashboard':
        return <AgentDashboard key={dashboardKey} />;
      case 'control':
        return <AgentControlPanel onRefresh={refreshDashboard} />;
      case 'measurement-extraction':
        return <MeasurementExtractionDemo />;
      default:
        return renderTraditionalView();
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <RobotOutlined style={{ fontSize: '24px', marginRight: '16px', color: '#1890ff' }} />
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            CheckMeasureAI
          </Title>
        </div>
        <Space>
          {!backendHealthy && (
            <Badge count="Backend Offline" color="#ff4d4f" />
          )}
          <Badge count="AI Enhanced" color="#52c41a" />
        </Space>
      </Header>
      
      <Layout>
        <Sider 
          width={250} 
          style={{ background: '#fff' }}
          breakpoint="lg"
          collapsedWidth="0"
        >
          <Menu
            mode="inline"
            selectedKeys={[currentView]}
            onClick={({ key }) => setCurrentView(key as ViewMode)}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        
        <Layout>
          <Content style={{ background: '#f0f2f5', overflow: 'auto' }}>
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default App;