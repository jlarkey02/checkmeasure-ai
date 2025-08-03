import React, { useState } from 'react';
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
  Tabs,
  Badge,
  Alert,
  Drawer,
  Grid
} from 'antd';
import { 
  InboxOutlined, 
  FilePdfOutlined, 
  DashboardOutlined,
  ControlOutlined,
  CalculatorOutlined,
  RobotOutlined,
  ExperimentOutlined,
  MenuOutlined,
  HomeOutlined,
  PlusCircleOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import SimplePDFViewer from './components/pdf-viewer/SimplePDFViewer';
import CalculationPanel from './components/CalculationPanel';
import ResultsDisplay from './components/ResultsDisplay';
import AgentDashboard from './components/agents/AgentDashboard';
import AgentControlPanel from './components/agents/AgentControlPanel';
import { apiClient } from './utils/api';
import './styles/mobile.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Dragger } = Upload;
const { useBreakpoint } = Grid;

type ViewMode = 'traditional' | 'multi-agent' | 'dashboard' | 'control';

const App: React.FC = () => {
  const screens = useBreakpoint();
  const isMobile = !screens.md;
  
  const [currentView, setCurrentView] = useState<ViewMode>('traditional');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [selections, setSelections] = useState<any[]>([]);
  const [dashboardKey, setDashboardKey] = useState(0);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);

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
      
      setPdfFile(file);
      message.success(`${file.name} loaded successfully`);
      
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
      
      // On mobile, scroll to results
      if (isMobile) {
        setTimeout(() => {
          document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
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
      const response = await apiClient.agents.executeTask(
        'joist_calculation',
        'joist_calculation',
        values,
        3
      );
      
      const projectId = response.data.project_id;
      message.success('Multi-agent calculation started!');
      message.loading('Processing with AI-enhanced calculation...', 0);
      
      await pollForResults(projectId);
      setDashboardKey(prev => prev + 1);
      
    } catch (error) {
      message.error('Multi-agent calculation failed');
      console.error('Error:', error);
      setCalculating(false);
    }
  };

  const pollForResults = async (projectId: string) => {
    const maxAttempts = 30;
    let attempts = 0;
    
    const poll = async (): Promise<void> => {
      try {
        attempts++;
        const statusResponse = await apiClient.agents.getProjectStatus(projectId);
        const status = statusResponse.data;
        
        if (status.status === 'completed') {
          const resultsResponse = await apiClient.agents.getProjectResults(projectId);
          const projectResults = resultsResponse.data;
          
          if (projectResults.results && projectResults.results.length > 0) {
            const calculationResult = projectResults.results[0].output_data;
            setResults({
              ...calculationResult,
              isMultiAgent: true,
              projectId: projectId,
              projectName: projectResults.project_name
            });
            message.destroy();
            message.success('AI-enhanced calculation completed!');
            setCalculating(false);
            
            // Scroll to results on mobile
            if (isMobile) {
              setTimeout(() => {
                document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
              }, 100);
            }
            return;
          }
        } else if (status.status === 'failed') {
          message.destroy();
          message.error('Multi-agent calculation failed');
          setCalculating(false);
          return;
        }
        
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000);
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

  const menuItems = [
    {
      key: 'traditional',
      icon: <CalculatorOutlined />,
      label: 'Traditional',
    },
    {
      key: 'multi-agent',
      icon: <RobotOutlined />,
      label: 'AI-Enhanced',
    },
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: 'control',
      icon: <ControlOutlined />,
      label: 'Control',
    },
  ];

  const renderMobileNav = () => (
    <div className="mobile-bottom-nav">
      {menuItems.map(item => (
        <div
          key={item.key}
          className={`mobile-bottom-nav-item ${currentView === item.key ? 'active' : ''}`}
          onClick={() => setCurrentView(item.key as ViewMode)}
        >
          <div>{item.icon}</div>
          <div>{item.label}</div>
        </div>
      ))}
    </div>
  );

  const renderContent = () => {
    const commonUploadSection = (isMultiAgent: boolean = false) => (
      <Card 
        title={isMultiAgent ? "AI-Enhanced PDF Analysis" : "PDF Upload"} 
        style={{ marginBottom: isMobile ? 16 : 24 }}
      >
        {!pdfFile ? (
          <Dragger {...uploadProps} style={{ minHeight: isMobile ? '150px' : '200px' }}>
            <p className="ant-upload-drag-icon">
              {isMultiAgent ? <RobotOutlined /> : <InboxOutlined />}
            </p>
            <p className="ant-upload-text">
              {isMobile ? "Tap to select PDF" : "Click or drag PDF file to upload"}
            </p>
            <p className="ant-upload-hint">
              {isMultiAgent 
                ? "AI-enhanced analysis with optimization" 
                : "Upload architectural drawings"}
            </p>
          </Dragger>
        ) : (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
              <FilePdfOutlined style={{ fontSize: 24, marginRight: 8, color: '#ff4d4f' }} />
              <Text strong>{pdfFile.name}</Text>
              {isMultiAgent && <Badge count="AI Enhanced" style={{ marginLeft: 8 }} />}
            </div>
            <div style={{ height: isMobile ? '300px' : 'auto' }}>
              <SimplePDFViewer 
                file={pdfFile} 
                onSelectionsChange={handleSelectionsChange}
              />
            </div>
            <Button onClick={handleReset} style={{ marginTop: 16 }} block={isMobile}>
              Upload Different File
            </Button>
          </div>
        )}
      </Card>
    );

    switch (currentView) {
      case 'traditional':
        return (
          <div>
            {commonUploadSection()}
            <CalculationPanel 
              onCalculate={handleCalculate}
              calculating={calculating}
              pdfFile={pdfFile}
              selections={selections}
            />
            {results && (
              <div id="results-section">
                <ResultsDisplay results={results} />
              </div>
            )}
          </div>
        );

      case 'multi-agent':
        return (
          <div>
            <Alert
              message="AI-Enhanced Calculations"
              description={isMobile 
                ? "Advanced AI optimization" 
                : "Experience AI-powered construction calculations with advanced optimization, cost analysis, and environmental impact assessment."}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            {commonUploadSection(true)}
            <Card title="AI-Enhanced Calculation">
              <CalculationPanel 
                onCalculate={handleMultiAgentCalculate}
                calculating={calculating}
                pdfFile={pdfFile}
                selections={selections}
                isMultiAgent={true}
              />
            </Card>
            {results && (
              <div id="results-section">
                <ResultsDisplay results={results} isMultiAgent={true} />
              </div>
            )}
          </div>
        );

      case 'dashboard':
        return <AgentDashboard key={dashboardKey} />;
        
      case 'control':
        return <AgentControlPanel onRefresh={() => setDashboardKey(prev => prev + 1)} />;
        
      default:
        return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: isMobile ? '0 16px' : '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {isMobile && (
            <MenuOutlined 
              className="mobile-nav-trigger"
              onClick={() => setMobileMenuVisible(true)}
              style={{ marginRight: 16 }}
            />
          )}
          <RobotOutlined style={{ fontSize: isMobile ? '20px' : '24px', marginRight: isMobile ? 8 : 16, color: '#1890ff' }} />
          <Title level={isMobile ? 4 : 3} style={{ margin: 0, color: '#1890ff' }}>
            CheckMeasureAI
          </Title>
        </div>
        {!isMobile && <Badge count="AI Enhanced" color="#52c41a" />}
      </Header>
      
      <Layout style={{ marginTop: isMobile ? 56 : 64 }}>
        {!isMobile && (
          <Layout.Sider 
            width={250} 
            style={{ background: '#fff', position: 'fixed', height: '100vh', paddingTop: 64 }}
          >
            <Menu
              mode="inline"
              selectedKeys={[currentView]}
              onClick={({ key }) => setCurrentView(key as ViewMode)}
              style={{ height: '100%', borderRight: 0 }}
              items={menuItems}
            />
          </Layout.Sider>
        )}
        
        <Content style={{ 
          background: '#f0f2f5', 
          padding: isMobile ? 16 : 24,
          marginLeft: isMobile ? 0 : 250,
          marginBottom: isMobile ? 70 : 0,
          minHeight: `calc(100vh - ${isMobile ? 126 : 64}px)`
        }}>
          {renderContent()}
        </Content>
      </Layout>
      
      {isMobile && renderMobileNav()}
      
      <Drawer
        title="Menu"
        placement="left"
        onClose={() => setMobileMenuVisible(false)}
        open={mobileMenuVisible}
        width={250}
      >
        <Menu
          mode="inline"
          selectedKeys={[currentView]}
          onClick={({ key }) => {
            setCurrentView(key as ViewMode);
            setMobileMenuVisible(false);
          }}
          items={menuItems}
        />
      </Drawer>
    </Layout>
  );
};

export default App;