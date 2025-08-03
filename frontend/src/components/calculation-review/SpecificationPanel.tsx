import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  InputNumber, 
  Button, 
  Space, 
  Typography,
  Divider,
  Alert,
  Spin
} from 'antd';
import { CalculatorOutlined, ExperimentOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '../../stores/appStore';
import { apiClient } from '../../utils/api';
import { JoistCalculationRequest, CalculationType } from '../../types';

const { Text, Title } = Typography;
const { Option } = Select;

interface SpecificationFormData {
  span_length: number;
  joist_spacing: number;
  building_level: string;
  room_type: string;
  load_type: string;
  project_name: string;
  client_name: string;
  engineer_name: string;
}

const SpecificationPanel: React.FC = () => {
  const [form] = Form.useForm<SpecificationFormData>();
  const [isCalculating, setIsCalculating] = useState(false);
  
  const {
    activeCalculationType,
    selectionAreas,
    setCalculationResults,
    setIsCalculating: setGlobalCalculating,
    setShowResults
  } = useAppStore();

  // Fetch materials data
  const { data: materialsData, isLoading: materialsLoading } = useQuery({
    queryKey: ['materials'],
    queryFn: () => apiClient.getAllMaterials(),
    select: (response) => response.data
  });

  // Fetch joist-specific materials
  const { data: joistMaterials, isLoading: joistMaterialsLoading } = useQuery({
    queryKey: ['joistMaterials'],
    queryFn: () => apiClient.getJoistMaterials(),
    select: (response) => response.data,
    enabled: activeCalculationType === 'joist'
  });

  const activeSelections = selectionAreas.filter(
    area => area.calculationType === activeCalculationType
  );

  const handleCalculate = async (values: SpecificationFormData) => {
    if (activeCalculationType !== 'joist') {
      // For now, only joist calculations are implemented
      return;
    }

    setIsCalculating(true);
    setGlobalCalculating(true);

    try {
      const request: JoistCalculationRequest = {
        span_length: values.span_length,
        joist_spacing: values.joist_spacing,
        building_level: values.building_level,
        room_type: values.room_type,
        load_type: values.load_type
      };

      const response = await apiClient.calculateJoists(request);
      
      setCalculationResults({
        joistCalculation: response.data,
        projectInfo: {
          projectName: values.project_name,
          clientName: values.client_name,
          engineerName: values.engineer_name,
          date: new Date().toISOString().split('T')[0],
          revision: 'A',
          deliveryNumber: 1
        },
        selectionAreas: activeSelections,
        pdfAnalysis: undefined
      });

      setShowResults(true);
      
    } catch (error) {
      console.error('Calculation error:', error);
      // Handle error - could show notification
    } finally {
      setIsCalculating(false);
      setGlobalCalculating(false);
    }
  };

  const getCalculationTypeTitle = (type: CalculationType) => {
    const titles = {
      joist: 'Floor Joist Calculation',
      beam: 'Beam Calculation',
      wall: 'Wall Framing Calculation',
      rafter: 'Roof Rafter Calculation',
      flooring: 'Flooring Calculation'
    };
    return titles[type];
  };

  const isFormValid = activeSelections.length > 0 || activeCalculationType === 'joist';

  return (
    <div style={{ padding: '16px' }}>
      <Title level={4} style={{ marginBottom: '16px' }}>
        <CalculatorOutlined /> {getCalculationTypeTitle(activeCalculationType)}
      </Title>

      {/* Selection Status */}
      <Alert
        message={`${activeSelections.length} area(s) selected for ${activeCalculationType} calculation`}
        type={activeSelections.length > 0 ? 'success' : 'warning'}
        style={{ marginBottom: '16px' }}
        showIcon
      />

      {/* Specification Form */}
      <Card title="Specification Parameters" size="small">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCalculate}
          initialValues={{
            joist_spacing: 0.45,
            building_level: 'L1',
            room_type: 'living',
            load_type: 'residential',
            project_name: 'New Project',
            client_name: 'Client Name',
            engineer_name: 'Engineer Name'
          }}
        >
          {/* Project Information */}
          <Title level={5}>Project Information</Title>
          
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
            label="Engineer Name"
            name="engineer_name"
            rules={[{ required: true, message: 'Please enter engineer name' }]}
          >
            <Input placeholder="Enter engineer name" />
          </Form.Item>

          <Divider />

          {/* Calculation-specific parameters */}
          {activeCalculationType === 'joist' && (
            <>
              <Title level={5}>Joist Parameters</Title>
              
              <Form.Item
                label="Span Length (m)"
                name="span_length"
                rules={[{ required: true, message: 'Please enter span length' }]}
                extra="Enter the span length in meters"
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
                  {materialsData?.standard_spacings.map(spacing => (
                    <Option key={spacing} value={spacing}>
                      {spacing}m ({spacing * 1000}mm centers)
                    </Option>
                  ))}
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
                  <Option value="other">Other</Option>
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
            </>
          )}

          {/* Material Information */}
          {joistMaterials && !joistMaterialsLoading && (
            <>
              <Divider />
              <Title level={5}>
                <ExperimentOutlined /> Available Materials
              </Title>
              
              <div style={{ fontSize: '12px', marginBottom: '16px' }}>
                <Text strong>LVL Options:</Text>
                {joistMaterials.map(material => (
                  <div key={material.specification} style={{ 
                    marginTop: '4px',
                    padding: '4px 8px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '3px'
                  }}>
                    <Text code>{material.specification}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '11px' }}>
                      {material.application}
                      {material.maxSpan && ` | Max span: ${material.maxSpan}m`}
                    </Text>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Submit Button */}
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={isCalculating}
              disabled={!isFormValid}
              style={{ width: '100%' }}
              icon={<CalculatorOutlined />}
            >
              {isCalculating ? 'Calculating...' : 'Calculate Materials'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Loading States */}
      {(materialsLoading || joistMaterialsLoading) && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin tip="Loading materials data..." />
        </div>
      )}

      {/* Calculation Status */}
      {!isFormValid && (
        <Alert
          message="Selection Required"
          description="Please select areas on the PDF drawing before calculating."
          type="info"
          style={{ marginTop: '16px' }}
          showIcon
        />
      )}
    </div>
  );
};

export default SpecificationPanel;