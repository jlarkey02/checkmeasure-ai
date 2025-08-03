import React, { useState } from 'react';
import { Typography, Space, Card, Upload, Button, message, Row, Col } from 'antd';
import { InboxOutlined, FilePdfOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import SimplePDFViewer from './components/pdf-viewer/SimplePDFViewer';
import CalculationPanel from './components/CalculationPanel';
import ResultsDisplay from './components/ResultsDisplay';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const App: React.FC = () => {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [selections, setSelections] = useState<any[]>([]);

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
      // Simulate processing time
      setTimeout(() => {
        setPdfFile(file);
        setLoading(false);
        message.success(`${file.name} loaded successfully`);
      }, 500);
      
      return false; // Prevent default upload
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
      const response = await fetch('http://localhost:8000/api/calculations/joists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        throw new Error('Calculation failed');
      }

      const result = await response.json();
      setResults(result);
      message.success('Calculation completed successfully!');
      
    } catch (error) {
      console.error('Calculation error:', error);
      message.error('Calculation failed. Please check your inputs and try again.');
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={1} style={{ color: '#1890ff' }}>
              <FilePdfOutlined /> Building Measurements
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              Construction Material Calculation Assistant
            </Text>
          </div>

          {!pdfFile ? (
            <div>
              <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>
                Upload Architectural Drawing
              </Title>
              
              <Dragger {...uploadProps} style={{ padding: '40px' }}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
                </p>
                <p className="ant-upload-text">
                  Click or drag PDF file to this area to upload
                </p>
                <p className="ant-upload-hint">
                  Support for architectural drawings in PDF format. 
                  The system will analyze the drawing for material calculations.
                </p>
              </Dragger>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Title level={3} style={{ margin: 0 }}>
                  PDF Viewer - {pdfFile.name}
                </Title>
                <Button onClick={handleReset}>
                  Upload New PDF
                </Button>
              </div>
              
              <Row gutter={24}>
                <Col span={18}>
                  <SimplePDFViewer 
                    file={pdfFile} 
                    onSelectionsChange={handleSelectionsChange}
                  />
                </Col>
                <Col span={6}>
                  <CalculationPanel 
                    onCalculate={handleCalculate} 
                    loading={calculating}
                    pdfFile={pdfFile}
                    selectedAreas={selections}
                  />
                </Col>
              </Row>
              
              {results && <ResultsDisplay results={results} />}
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default App;