import React, { useState } from 'react';
import { Card, Form, InputNumber, Input, Select, Button, Space, Typography, Divider, message } from 'antd';
import { CalculatorOutlined, CheckCircleOutlined, RobotOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

interface CalculationPanelProps {
  onCalculate: (values: any) => void;
  loading?: boolean;
  calculating?: boolean;
  pdfFile?: File | null;
  manualMeasurements?: any[];
  selectedAreas?: any[];  // Add selected areas from parent component
  selections?: any[];  // Alternative prop name for selections
  isMultiAgent?: boolean;
}

const CalculationPanel: React.FC<CalculationPanelProps> = ({ 
  onCalculate, 
  loading, 
  calculating = false,
  pdfFile, 
  manualMeasurements = [], 
  selectedAreas: propSelectedAreas = [],
  selections = [],
  isMultiAgent = false
}) => {
  const [form] = Form.useForm();
  const [smartAnalyzing, setSmartAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<string>('');
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [detectedJoists, setDetectedJoists] = useState<any[]>([]);
  const [debugMode, setDebugMode] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>(null);
  
  // Use selected areas from props or internal state
  const selectedAreas = propSelectedAreas.length > 0 ? propSelectedAreas : selections;



  const handleSubmit = (values: any) => {
    onCalculate(values);
  };

  const handleSmartAnalysis = async () => {
    if (!pdfFile) {
      message.warning('Please upload a PDF file first');
      return;
    }

    setSmartAnalyzing(true);
    setAnalysisProgress('Initializing intelligent analysis...');
    
    try {
      // Determine the best analysis method based on available data
      let analysisMethod = 'claude_vision';
      let endpoint = '/api/pdf/auto-populate-claude-vision';
      
      // If user has marked specific areas, prioritize area analysis
      if (selectedAreas.length > 0) {
        analysisMethod = 'area_analysis';
        endpoint = '/api/pdf/analyze-selected-areas';
        setAnalysisProgress(`Analyzing ${selectedAreas.length} marked areas with Claude Vision AI...`);
      } else {
        setAnalysisProgress('Analyzing entire drawing with Claude Vision AI...');
      }
      
      const formData = new FormData();
      formData.append('file', pdfFile);
      
      if (analysisMethod === 'area_analysis') {
        formData.append('request', JSON.stringify({
          selection_areas: selectedAreas
        }));
      }
      
      setAnalysisProgress('Processing with advanced AI analysis...');
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      setAnalysisProgress('Extracting measurements and auto-populating form...');
      const result = await response.json();
      const formData_result = result.form_data;

      if (formData_result && formData_result.error) {
        if (formData_result.error.includes('ANTHROPIC_API_KEY')) {
          message.error('Claude Vision requires an API key. Please set ANTHROPIC_API_KEY environment variable.');
          return;
        }
        
        // Try fallback method if Claude Vision fails
        setAnalysisProgress('Primary method failed, trying advanced fallback...');
        await handleFallbackAnalysis();
        return;
      }

      // Update form with detected values
      const updateValues: any = {};
      
      if (formData_result.span_length) {
        updateValues.span_length = formData_result.span_length;
      }
      
      if (formData_result.joist_spacing) {
        updateValues.joist_spacing = formData_result.joist_spacing;
      }

      form.setFieldsValue(updateValues);
      setDetectedJoists(formData_result.all_detected_joists || result.detected_elements || []);
      setAnalysisResults(result);

      // Create comprehensive success message
      const methodUsed = analysisMethod === 'area_analysis' ? '🎯 Area Analysis' : '🔍 Claude Vision';
      const elementsFound = (formData_result.all_detected_joists || result.detected_elements || []).length;
      const confidence = Math.round((formData_result.confidence || result.overall_confidence || 0) * 100);
      
      let successMessage = `✅ ${methodUsed} COMPLETE\n\n`;
      successMessage += `📊 Results: ${elementsFound} elements found (${confidence}% confidence)\n`;
      
      if (analysisMethod === 'area_analysis') {
        successMessage += `🎯 Areas: ${result.successful_areas}/${result.total_areas} analyzed successfully\n`;
      }
      
      if (Object.keys(updateValues).length > 0) {
        successMessage += `🔧 Auto-populated: ${Object.keys(updateValues).join(', ')}`;
      }
      
      message.success(successMessage, 8);
      
      console.log('Smart Analysis Results:', result);

    } catch (error) {
      console.error('Smart analysis error:', error);
      setAnalysisProgress('Primary analysis failed, trying fallback methods...');
      await handleFallbackAnalysis();
    } finally {
      setSmartAnalyzing(false);
      setTimeout(() => setAnalysisProgress(''), 2000);
    }
  };
  
  const handleFallbackAnalysis = async () => {
    try {
      setAnalysisProgress('Running advanced OCR analysis...');
      
      const formData = new FormData();
      formData.append('file', pdfFile!);
      
      const response = await fetch('http://localhost:8000/api/pdf/auto-populate-advanced', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Advanced analysis failed');
      }

      const result = await response.json();
      const formData_result = result.form_data;

      if (formData_result.error) {
        // Final fallback to basic method
        setAnalysisProgress('Trying basic text extraction...');
        await handleBasicAnalysis();
        return;
      }

      const updateValues: any = {};
      
      if (formData_result.span_length) {
        updateValues.span_length = formData_result.span_length;
      }
      
      if (formData_result.joist_spacing) {
        updateValues.joist_spacing = formData_result.joist_spacing;
      }

      form.setFieldsValue(updateValues);
      setDetectedJoists(formData_result.all_detected_joists || []);
      setAnalysisResults(result);

      message.success(
        `⚡ Fallback Analysis: Found ${formData_result.detected_joists} joist(s) using ` +
        `${formData_result.detection_methods?.join(', ')} ` +
        `(${Math.round((formData_result.confidence || 0) * 100)}% confidence)`,
        6
      );

    } catch (error) {
      console.error('Fallback analysis error:', error);
      await handleBasicAnalysis();
    }
  };
  
  const handleBasicAnalysis = async () => {
    try {
      setAnalysisProgress('Running basic text analysis...');
      
      const formData = new FormData();
      formData.append('file', pdfFile!);
      
      const response = await fetch('http://localhost:8000/api/pdf/auto-populate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Basic analysis failed');
      }

      const result = await response.json();
      const formData_result = result.form_data;

      if (formData_result.error) {
        message.warning(`Analysis completed with limited results: ${formData_result.error}`);
        return;
      }

      const updateValues: any = {};
      
      if (formData_result.span_length) {
        updateValues.span_length = formData_result.span_length;
      }
      
      if (formData_result.joist_spacing) {
        updateValues.joist_spacing = formData_result.joist_spacing;
      }

      form.setFieldsValue(updateValues);
      setDetectedJoists(formData_result.all_detected_joists || []);
      setAnalysisResults(result);

      message.info(
        `📝 Basic Analysis: Found ${formData_result.detected_joists} joist(s). ` +
        `Primary joist: ${formData_result.primary_joist_label} ` +
        `(${Math.round(formData_result.confidence * 100)}% confidence)`,
        5
      );

    } catch (error) {
      console.error('Basic analysis error:', error);
      message.error('All analysis methods failed. Please check the PDF quality and try again.');
    }
  };

  const handleDebugAnalysis = async () => {
    if (!pdfFile) {
      message.warning('Please upload a PDF file first');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', pdfFile);
      
      const response = await fetch('http://localhost:8000/api/pdf/debug-joist-detection', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to debug detection');
      }

      const result = await response.json();
      setDebugInfo(result);
      
      message.info(`Debug complete. Found ${result.step_2_label_search.length} potential labels.`);

    } catch (error) {
      console.error('Debug error:', error);
      message.error('Failed to debug detection. Please check console for details.');
    }
  };




  return (
    <Card 
      title={<><CalculatorOutlined /> Joist Calculation</>}
      style={{ marginTop: '24px' }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          span_length: 3.386,
          joist_spacing: 0.45,
          building_level: 'L1',
          room_type: 'living',
          load_type: 'residential',
          project_name: 'Sample Project',
          client_name: 'Client Name',
          engineer_name: 'Builder Name'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: '16px' }}>
          {pdfFile && (
            <Space>
              <Button
                type="primary"
                icon={<RobotOutlined />}
                loading={smartAnalyzing}
                onClick={handleSmartAnalysis}
                size="middle"
                style={{ 
                  background: 'linear-gradient(135deg, #722ed1 0%, #52c41a 100%)', 
                  borderColor: '#722ed1',
                  fontWeight: 'bold'
                }}
              >
                {smartAnalyzing 
                  ? (analysisProgress || 'AI Analyzing...') 
                  : '🎯 Analyze'}
              </Button>
              <Button
                type="default"
                icon={<InfoCircleOutlined />}
                onClick={() => setDebugMode(!debugMode)}
                size="small"
                style={{ opacity: 0.7 }}
              >
                {debugMode ? 'Hide Debug' : 'Debug'}
              </Button>
            </Space>
          )}
        </div>
        
        <Form.Item
          label="Project Name"
          name="project_name"
          rules={[{ required: true, message: 'Please enter project name' }]}
        >
          <Input placeholder="Enter project name" />
        </Form.Item>

        <Form.Item
          label="Client Name"
          name="client_name"
          rules={[{ required: true, message: 'Please enter client name' }]}
        >
          <Input placeholder="Enter client name" />
        </Form.Item>

        <Form.Item
          label="Builder Name"
          name="engineer_name"
          rules={[{ required: true, message: 'Please enter builder name' }]}
        >
          <Input placeholder="Enter builder name" />
        </Form.Item>

        <Divider />

        <Title level={4}>Joist Parameters</Title>
        
        <Form.Item
          label="Span Length (m)"
          name="span_length"
          rules={[{ required: true, message: 'Please enter span length' }]}
          extra="Enter the span length in meters (from client example: 3.386m)"
        >
          <InputNumber
            min={0.1}
            max={20}
            step={0.1}
            placeholder="e.g., 3.386"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label="Joist Spacing (m)"
          name="joist_spacing"
          rules={[{ required: true, message: 'Please select joist spacing' }]}
          extra="Standard spacing options"
        >
          <Select placeholder="Select spacing">
            <Option value={0.3}>0.3m (300mm centers)</Option>
            <Option value={0.45}>0.45m (450mm centers)</Option>
            <Option value={0.6}>0.6m (600mm centers)</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Building Level"
          name="building_level"
          rules={[{ required: true, message: 'Please select building level' }]}
        >
          <Select placeholder="Select level">
            <Option value="GF">Ground Floor (GF)</Option>
            <Option value="L1">Level 1 (L1)</Option>
            <Option value="L2">Level 2 (L2)</Option>
            <Option value="RF">Roof (RF)</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Room Type"
          name="room_type"
          extra="Optional - affects load calculations"
        >
          <Select placeholder="Select room type">
            <Option value="living">Living Area</Option>
            <Option value="bedroom">Bedroom</Option>
            <Option value="kitchen">Kitchen</Option>
            <Option value="bathroom">Bathroom</Option>
            <Option value="storage">Storage</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Load Type"
          name="load_type"
          extra="Determines material selection criteria"
        >
          <Select placeholder="Select load type">
            <Option value="residential">Residential</Option>
            <Option value="commercial">Commercial</Option>
            <Option value="industrial">Industrial</Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            loading={loading}
            style={{ width: '100%' }}
            icon={loading ? undefined : <CheckCircleOutlined />}
          >
            {loading ? 'Calculating...' : 'Calculate Materials'}
          </Button>
        </Form.Item>

        {smartAnalyzing && analysisProgress && (
          <div style={{ 
            marginTop: '16px', 
            padding: '12px', 
            backgroundColor: 'linear-gradient(135deg, #e6f7ff 0%, #f0fff0 100%)', 
            borderRadius: '8px', 
            border: '2px solid #52c41a',
            textAlign: 'center'
          }}>
            <Text style={{ fontSize: '13px', color: '#1890ff', fontWeight: 'bold' }}>
              <RobotOutlined spin /> {analysisProgress}
            </Text>
            <div style={{ marginTop: '8px' }}>
              <Text style={{ fontSize: '11px', color: '#666' }}>
                {selectedAreas.length > 0 
                  ? `Smart analysis processing ${selectedAreas.length} marked areas. This may take 30-90 seconds.`
                  : 'Intelligent analysis in progress. This may take 30-90 seconds.'}
              </Text>
            </div>
          </div>
        )}

        {detectedJoists.length > 0 && (
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0fff0', borderRadius: '8px', border: '1px solid #52c41a' }}>
            <Text strong style={{ fontSize: '13px', color: '#52c41a' }}>
              ✅ Analysis Results:
            </Text>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '16px' }}>
              {detectedJoists.map((joist, index) => (
                <li key={index} style={{ fontSize: '11px', color: '#666' }}>
                  <Text code>{joist.label}</Text>: {joist.specification} 
                  <Text type="secondary"> ({Math.round((joist.confidence || 0) * 100)}% confidence)</Text>
                </li>
              ))}
            </ul>
          </div>
        )}


        {debugMode && debugInfo && (
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#fff7e6', borderRadius: '6px', border: '1px solid #ffd591' }}>
            <Text strong style={{ fontSize: '12px', color: '#d46b08' }}>
              🔍 Debug Information:
            </Text>
            <div style={{ fontSize: '11px', marginTop: '8px' }}>
              <div><strong>Text Blocks Found:</strong> {debugInfo.step_1_text_extraction?.total_blocks || 0}</div>
              <div><strong>Label Matches:</strong> {debugInfo.step_2_label_search?.length || 0}</div>
              <div><strong>Specifications Found:</strong> {debugInfo.step_3_specification_search?.length || 0}</div>
              <div><strong>Final Joists:</strong> {debugInfo.step_4_detected_joists?.length || 0}</div>
              
              {debugInfo.step_2_label_search?.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <strong>Found Labels:</strong>
                  <ul style={{ margin: '4px 0 0 0', paddingLeft: '16px' }}>
                    {debugInfo.step_2_label_search.map((item: any, index: number) => (
                      <li key={index}>
                        <Text code>{item.matched_label}</Text> in "{item.text}"
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {debugInfo.step_1_text_extraction?.sample_text && (
                <div style={{ marginTop: '8px' }}>
                  <strong>Sample Text:</strong>
                  <div style={{ fontSize: '10px', color: '#666', maxHeight: '100px', overflow: 'auto' }}>
                    {debugInfo.step_1_text_extraction.sample_text.join(' | ')}
                  </div>
                </div>
              )}
            </div>
            <div style={{ marginTop: '8px', textAlign: 'center' }}>
              <Button size="small" onClick={handleDebugAnalysis}>
                Run Debug Analysis
              </Button>
            </div>
          </div>
        )}


        {analysisResults && (
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0fff0', borderRadius: '8px', border: '2px solid #52c41a' }}>
            <Text strong style={{ fontSize: '13px', color: '#52c41a' }}>
              🎯 Smart Analysis Results:
            </Text>
            <div style={{ fontSize: '11px', marginTop: '8px' }}>
              {analysisResults.successful_areas && (
                <div><strong>Areas Analyzed:</strong> {analysisResults.successful_areas}/{analysisResults.total_areas} successful</div>
              )}
              <div><strong>Elements Found:</strong> {analysisResults.detected_elements?.length || analysisResults.form_data?.detected_joists || 0}</div>
              <div><strong>Overall Confidence:</strong> {Math.round((analysisResults.overall_confidence || analysisResults.form_data?.confidence || 0) * 100)}%</div>
              {(analysisResults.processing_time_ms || analysisResults.form_data?.processing_time_ms) && (
                <div><strong>Processing Time:</strong> {Math.round((analysisResults.processing_time_ms || analysisResults.form_data.processing_time_ms) / 1000)}s</div>
              )}
              
              {(analysisResults.combined_reasoning || analysisResults.form_data?.claude_reasoning) && (
                <div style={{ marginTop: '8px' }}>
                  <strong>AI Analysis Summary:</strong>
                  <div style={{ fontSize: '10px', color: '#666', fontStyle: 'italic', marginTop: '4px' }}>
                    "{analysisResults.combined_reasoning || analysisResults.form_data.claude_reasoning}"
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f6ffed', borderRadius: '6px', border: '1px solid #b7eb8f' }}>
          <Text style={{ fontSize: '12px', color: '#52c41a' }}>
            <CheckCircleOutlined /> Expected result: 8 joists for 3.386m ÷ 0.45m spacing
          </Text>
        </div>
      </Form>
    </Card>
  );
};

export default CalculationPanel;