import React, { useState } from 'react';
import { Card, Button, Upload, message, Space, Spin, Typography, Input, Row, Col, List, Tag, Modal, Select } from 'antd';
import { UploadOutlined, FileSearchOutlined, EditOutlined, CheckOutlined, SelectOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import PDFViewer from './pdf-viewer/PDFViewer';
import { useAppStore } from '../stores/appStore';
import api, { apiClient } from '../utils/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface ScaleResult {
  scale_ratio: string;
  scale_notation?: string;  // Added for new scale system
  scale_factor: number;
  confidence: number;
  method: string;
  source_text?: string;
}

interface MeasuredArea {
  id: string;
  label: string;
  detectedLabel?: string;
  elementType?: string;  // Selected element type
  selection: {
    x: number;
    y: number;
    width: number;
    height: number;
    pageNumber: number;
  };
  measurements?: {
    width_m: number;
    height_m: number;
    confidence: number;
  };
  scaleUsed?: string;  // Added for new scale system
  calculationResult?: any;  // Results from calculation endpoint
  status: 'pending' | 'analyzing' | 'success' | 'error';
  statusMessage?: string;
}

interface ElementTypeInfo {
  code: string;
  description: string;
  category: string;
  calculator_type: string;
  specification: any;
  active: boolean;
}

const MeasurementExtractionDemo: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [scale, setScale] = useState<ScaleResult | null>(null);
  const [editingScale, setEditingScale] = useState(false);
  const [overrideScale, setOverrideScale] = useState('');
  const [measuredAreas, setMeasuredAreas] = useState<MeasuredArea[]>([]);
  const [editingLabel, setEditingLabel] = useState<string | null>(null);
  const [labelInput, setLabelInput] = useState('');
  const [manualScaleMode, setManualScaleMode] = useState(false);
  const [selectedPresetScale, setSelectedPresetScale] = useState<string>('1:100 at A3');
  const [elementTypes, setElementTypes] = useState<ElementTypeInfo[]>([]);
  const [selectedElementType, setSelectedElementType] = useState<string>('J1');
  const [showCalculation, setShowCalculation] = useState(false);
  const [consolidatedList, setConsolidatedList] = useState<string>('');
  
  const { 
    isSelecting, 
    setIsSelecting, 
    selectionAreas, 
    clearSelectionAreas 
  } = useAppStore();

  // Load element types on component mount - delayed to avoid backend crash
  React.useEffect(() => {
    // Only load element types after a delay and if needed
    const timer = setTimeout(() => {
      loadElementTypes();
    }, 2000); // 2 second delay
    
    return () => clearTimeout(timer);
  }, []);

  const loadElementTypes = async () => {
    try {
      const response = await apiClient.getElementTypes();
      setElementTypes(response.data);
    } catch (error: any) {
      console.error('Failed to load element types:', error);
      // Don't show error message for connection issues during startup
      if (error?.code !== 'ERR_NETWORK') {
        message.error('Failed to load element types');
      }
    }
  };

  // Common architectural scales with paper size notation
  const commonScales = [
    { value: '1:20 at A3', label: '1:20 at A3 (Detail drawings)' },
    { value: '1:50 at A3', label: '1:50 at A3 (Floor plans - residential)' },
    { value: '1:100 at A3', label: '1:100 at A3 (Floor plans - commercial)' },
    { value: '1:200 at A3', label: '1:200 at A3 (Site plans)' },
    { value: '1:500 at A3', label: '1:500 at A3 (Large site plans)' },
    { value: '1:100 at A2', label: '1:100 at A2' },
    { value: '1:100 at A1', label: '1:100 at A1' },
    { value: '1:50 at A1', label: '1:50 at A1' },
    { value: 'custom', label: 'Custom...' }
  ];

  // Scale detection removed - manual selection only

  const handleManualScaleSet = () => {
    let scaleNotation = selectedPresetScale;
    
    if (selectedPresetScale === 'custom') {
      scaleNotation = overrideScale;
    }
    
    // Validate scale notation format
    const scalePattern = /1:(\d+)\s*(?:at|@)\s*([A-Za-z]\d)/;
    if (!scalePattern.test(scaleNotation)) {
      message.error('Please use format like "1:100 at A3"');
      return;
    }
    
    setScale({
      scale_ratio: scaleNotation,
      scale_notation: scaleNotation,
      scale_factor: 100, // No longer used but kept for compatibility
      confidence: 100,
      method: 'manual',
      source_text: 'User specified'
    });
    
    setManualScaleMode(false);
    message.success(`Scale set to ${scaleNotation}`);
  };

  const handleAreaSelection = () => {
    if (!scale) {
      message.warning('Please detect scale first');
      return;
    }
    setIsSelecting(true);
    message.info('Draw rectangles around areas to measure');
  };

  const handleAnalyzeArea = async (area: any) => {
    const measuredArea: MeasuredArea = {
      id: area.id,
      label: area.label || 'Area',
      selection: area,
      status: 'analyzing',
      statusMessage: 'Preparing area for analysis...'
    };
    
    setMeasuredAreas(prev => [...prev, measuredArea]);

    try {
      // Update status: uploading
      setMeasuredAreas(prev => prev.map(ma => 
        ma.id === area.id 
          ? { ...ma, statusMessage: 'Uploading PDF and area data...' }
          : ma
      ));

      const formData = new FormData();
      formData.append('file', fileList[0] as any as File);
      formData.append('request', JSON.stringify({
        area_coordinates: {
          x: area.x,
          y: area.y,
          width: area.width,
          height: area.height
        },
        page_number: area.pageNumber,
        scale_notation: scale?.scale_notation || scale?.scale_ratio || '1:100 at A3'
      }));

      const response = await api.post('/api/pdf/calculate-dimensions', formData, {
        headers: {
          'Content-Type': undefined
        },
        // No upload progress needed for instant calculation
      });

      // Extract measurements from response
      const measurements = response.data;
      console.log('Dimension calculation for area', area.id, ':', measurements);
      
      // Update area with calculated dimensions
      setMeasuredAreas(prev => prev.map(ma => 
        ma.id === area.id 
          ? {
              ...ma,
              label: `${selectedElementType}-${area.label || 'Area'}`,
              elementType: selectedElementType,
              measurements: {
                width_m: measurements.width_m,
                height_m: measurements.height_m,
                confidence: 1.0  // Always 100% confidence with math
              },
              scaleUsed: measurements.scale_used,
              status: 'success',
              statusMessage: 'Dimensions calculated'
            }
          : ma
      ));

      message.success(`Dimensions calculated using scale: ${measurements.scale_used}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      setMeasuredAreas(prev => prev.map(ma => 
        ma.id === area.id 
          ? { ...ma, status: 'error', statusMessage: `Error: ${errorMessage}` } 
          : ma
      ));
      message.error(`Failed to analyze area: ${errorMessage}`);
      console.error('Area analysis error:', error);
    }
  };

  const handleLabelConfirm = () => {
    if (editingLabel) {
      setMeasuredAreas(prev => prev.map(ma => 
        ma.id === editingLabel ? { ...ma, label: labelInput } : ma
      ));
      setEditingLabel(null);
      setLabelInput('');
    }
  };

  const performCalculation = async (area: MeasuredArea) => {
    if (!area.measurements) return;

    try {
      const response = await apiClient.calculate(
        area.elementType || selectedElementType,
        {
          width: area.measurements.width_m,
          length: area.measurements.height_m
        },
        {
          area_suffix: area.label.replace(/[^A-Z0-9]/gi, ''),
          building_level: 'L1'
        }
      );

      // Update area with calculation results
      setMeasuredAreas(prev => prev.map(ma => 
        ma.id === area.id 
          ? { ...ma, calculationResult: response.data }
          : ma
      ));

      message.success(`Calculation completed for ${area.label}`);
    } catch (error: any) {
      message.error(`Calculation failed: ${error.message}`);
    }
  };

  const beforeUpload = (file: any) => {
    const isPDF = file.type === 'application/pdf';
    if (!isPDF) {
      message.error('You can only upload PDF files!');
      return false;
    }
    setFileList([file]);
    // Reset state when new file is uploaded
    setScale(null);
    setMeasuredAreas([]);
    clearSelectionAreas();
    return false;
  };

  // React to new selection areas
  React.useEffect(() => {
    const newAreas = selectionAreas.filter(
      area => !measuredAreas.find(ma => ma.selection.x === area.x && ma.selection.y === area.y)
    );
    
    newAreas.forEach(area => {
      handleAnalyzeArea(area);
    });
  }, [selectionAreas]);

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>
        <FileSearchOutlined /> Measurement Extraction
      </Title>
      
      <Row gutter={16}>
        <Col span={16}>
          {/* Upload and Controls */}
          <Card style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                beforeUpload={beforeUpload}
                fileList={fileList}
                onRemove={() => setFileList([])}
                maxCount={1}
              >
                <Button icon={<UploadOutlined />}>Select PDF</Button>
              </Upload>

              <Space>
                <Button 
                  type="primary"
                  onClick={() => setManualScaleMode(true)}
                  disabled={fileList.length === 0}
                >
                  Select Scale
                </Button>

                <Select
                  value={selectedElementType}
                  onChange={setSelectedElementType}
                  style={{ width: 200 }}
                  disabled={!scale}
                >
                  {elementTypes.map(type => (
                    <Option 
                      key={type.code} 
                      value={type.code}
                      title={type.description}
                    >
                      {type.code} - {type.description.slice(0, 20)}...
                    </Option>
                  ))}
                </Select>

                <Button
                  onClick={handleAreaSelection}
                  disabled={!scale}
                  icon={<SelectOutlined />}
                >
                  Select Areas
                </Button>
              </Space>
            </Space>
          </Card>

          {/* Scale Display */}
          {scale && (
            <Card 
              title={
                <Space>
                  <span>Scale</span>
                  {scale.method === 'manual' && <Tag color="blue">Manual</Tag>}
                  {scale.method !== 'manual' && <Tag color="green">Detected</Tag>}
                </Space>
              } 
              style={{ marginBottom: 16 }}
            >
              <Space align="center">
                <Text style={{ fontSize: 24, fontWeight: 'bold' }}>
                  {editingScale ? (
                    <Input
                      value={overrideScale}
                      onChange={(e) => setOverrideScale(e.target.value)}
                      style={{ width: 120 }}
                      placeholder="1:100"
                    />
                  ) : (
                    scale.scale_ratio
                  )}
                </Text>
                {editingScale ? (
                  <Button 
                    type="primary" 
                    icon={<CheckOutlined />} 
                    onClick={() => {
                      setEditingScale(false);
                      // Update scale if needed
                    }}
                  >
                    Save
                  </Button>
                ) : (
                  <Button 
                    icon={<EditOutlined />} 
                    onClick={() => {
                      setEditingScale(true);
                      setOverrideScale(scale.scale_ratio);
                    }}
                  >
                    Edit
                  </Button>
                )}
              </Space>
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">
                  Scale: {scale.scale_ratio}
                </Text>
              </div>
              
              {/* Scale Information */}
              <div style={{ marginTop: 16, padding: 12, background: '#f0f8ff', borderRadius: 4 }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <Text strong>Scale Configuration</Text>
                  </Space>
                  <Text type="secondary">
                    Scale: {scale.scale_notation || scale.scale_ratio}
                  </Text>
                  <Text type="secondary">
                    Method: {scale.method === 'manual' ? 'Manually specified' : 'Mathematical calculation'}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Using PDF coordinate system (1 point = 0.3528 mm) with scale notation
                  </Text>
                </Space>
              </div>
            </Card>
          )}

          {/* PDF Viewer */}
          {fileList.length > 0 && (
            <Card>
              <PDFViewer 
                file={fileList[0] as any as File}
                measurements={[]}
              />
            </Card>
          )}
        </Col>

        <Col span={8}>
          {/* Measured Areas Panel */}
          <Card title="Measured Areas" style={{ height: '100%' }}>
            <List
              dataSource={measuredAreas}
              renderItem={area => (
                <List.Item>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Space>
                      <Text strong>{area.label}</Text>
                      {area.elementType && <Tag color="blue">{area.elementType}</Tag>}
                      {area.status === 'analyzing' && <Spin size="small" />}
                      {area.status === 'success' && <Tag color="success">✓</Tag>}
                      {area.status === 'error' && <Tag color="error">✗</Tag>}
                    </Space>
                    
                    {/* Status message while analyzing */}
                    {area.status === 'analyzing' && area.statusMessage && (
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {area.statusMessage}
                      </Text>
                    )}
                    
                    {/* Error message */}
                    {area.status === 'error' && area.statusMessage && (
                      <Text type="danger" style={{ fontSize: '12px' }}>
                        {area.statusMessage}
                      </Text>
                    )}
                    
                    {/* Success results */}
                    {area.measurements && (
                      <>
                        <Text>
                          Dimensions: {area.measurements.width_m.toFixed(3)}m × {area.measurements.height_m.toFixed(3)}m
                        </Text>
                        <Text type="secondary">
                          Area: {area.measurements.width_m.toFixed(3)}m × {area.measurements.height_m.toFixed(3)}m
                        </Text>
                        {area.scaleUsed && (
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            Scale used: {area.scaleUsed}
                          </Text>
                        )}
                      </>
                    )}
                    
                    {area.detectedLabel && area.detectedLabel !== area.label && (
                      <Text type="secondary">
                        Originally detected as: {area.detectedLabel}
                      </Text>
                    )}
                    
                    {/* Calculate button for successful measurements */}
                    {area.status === 'success' && area.measurements && !area.calculationResult && (
                      <Button 
                        size="small"
                        type="primary"
                        onClick={() => performCalculation(area)}
                      >
                        Calculate Materials
                      </Button>
                    )}
                    
                    {/* Show calculation results */}
                    {area.calculationResult && (
                      <Card size="small" style={{ marginTop: 8 }}>
                        <pre style={{ fontSize: '11px', margin: 0 }}>
                          {area.calculationResult.formatted_output}
                        </pre>
                      </Card>
                    )}
                  </Space>
                </List.Item>
              )}
              locale={{ emptyText: 'No areas measured yet' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Label Edit Modal */}
      <Modal
        title="Confirm Area Label"
        open={!!editingLabel}
        onOk={handleLabelConfirm}
        onCancel={() => {
          setEditingLabel(null);
          setLabelInput('');
        }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Enter a label for this area:</Text>
          <Input
            value={labelInput}
            onChange={(e) => setLabelInput(e.target.value)}
            placeholder="e.g., J1, G6, B2"
          />
        </Space>
      </Modal>

      {/* Manual Scale Selection Modal */}
      <Modal
        title="Set Scale Manually"
        open={manualScaleMode}
        onOk={handleManualScaleSet}
        onCancel={() => setManualScaleMode(false)}
        width={400}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Select a common architectural scale:</Text>
          <Select
            value={selectedPresetScale}
            onChange={setSelectedPresetScale}
            style={{ width: '100%' }}
          >
            {commonScales.map(scale => (
              <Option key={scale.value} value={scale.value}>
                {scale.label}
              </Option>
            ))}
          </Select>
          
          {selectedPresetScale === 'custom' && (
            <>
              <Text>Enter custom scale:</Text>
              <Input
                value={overrideScale}
                onChange={(e) => setOverrideScale(e.target.value)}
                placeholder="e.g., 1:75"
                style={{ marginTop: 8 }}
              />
            </>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export default MeasurementExtractionDemo;