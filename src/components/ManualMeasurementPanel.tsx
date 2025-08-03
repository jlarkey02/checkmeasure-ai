import React, { useState } from 'react';
import { Card, Form, InputNumber, Select, Button, Typography, Divider, List, Space, message, Alert } from 'antd';
import { LineOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

interface Selection {
  x: number;
  y: number;
  width: number;
  height: number;
  page: number;
}

interface Measurement {
  id: string;
  selectionIndex: number;
  measurementType: 'span_length' | 'joist_spacing' | 'beam_height' | 'wall_length';
  value: number;
  unit: 'mm' | 'm' | 'ft';
  description: string;
}

interface ManualMeasurementPanelProps {
  selections: Selection[];
  onMeasurementsUpdate: (measurements: Measurement[]) => void;
}

const ManualMeasurementPanel: React.FC<ManualMeasurementPanelProps> = ({ 
  selections, 
  onMeasurementsUpdate 
}) => {
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [form] = Form.useForm();

  const measurementTypes = [
    { value: 'span_length', label: 'Span Length', icon: '↔️' },
    { value: 'joist_spacing', label: 'Joist Spacing', icon: '⫴' },
    { value: 'beam_height', label: 'Beam Height', icon: '↕️' },
    { value: 'wall_length', label: 'Wall Length', icon: '📏' }
  ];

  const addMeasurement = (values: any) => {
    const newMeasurement: Measurement = {
      id: `measurement_${Date.now()}`,
      selectionIndex: values.selection_index,
      measurementType: values.measurement_type,
      value: values.value,
      unit: values.unit,
      description: values.description || `${measurementTypes.find(t => t.value === values.measurement_type)?.label}`
    };

    const updatedMeasurements = [...measurements, newMeasurement];
    setMeasurements(updatedMeasurements);
    onMeasurementsUpdate(updatedMeasurements);
    
    form.resetFields();
    message.success('Measurement added successfully');
  };

  const removeMeasurement = (measurementId: string) => {
    const updatedMeasurements = measurements.filter(m => m.id !== measurementId);
    setMeasurements(updatedMeasurements);
    onMeasurementsUpdate(updatedMeasurements);
    message.success('Measurement removed');
  };

  const getSelectionLabel = (index: number, selection: Selection) => {
    return `Area ${index + 1} (Page ${selection.page}, ${Math.round(selection.width)}×${Math.round(selection.height)}px)`;
  };

  const convertToMeters = (value: number, unit: string): number => {
    switch (unit) {
      case 'mm': return value / 1000;
      case 'm': return value;
      case 'ft': return value * 0.3048;
      default: return value;
    }
  };

  const getJoistCalculationData = () => {
    const spanMeasurement = measurements.find(m => m.measurementType === 'span_length');
    const spacingMeasurement = measurements.find(m => m.measurementType === 'joist_spacing');

    if (spanMeasurement && spacingMeasurement) {
      return {
        span_length: convertToMeters(spanMeasurement.value, spanMeasurement.unit),
        joist_spacing: convertToMeters(spacingMeasurement.value, spacingMeasurement.unit),
        source: 'manual_measurement'
      };
    }
    return null;
  };

  return (
    <Card 
      title={<><LineOutlined /> Manual Measurements</>}
      style={{ marginTop: '24px' }}
    >
      {selections.length === 0 ? (
        <Alert
          message="No areas selected"
          description="Select areas on the PDF by clicking and dragging to add measurements."
          type="info"
          showIcon
        />
      ) : (
        <>
          <Form
            form={form}
            layout="vertical"
            onFinish={addMeasurement}
            initialValues={{
              unit: 'm',
              measurement_type: 'span_length'
            }}
          >
            <Form.Item
              label="Selected Area"
              name="selection_index"
              rules={[{ required: true, message: 'Please select an area' }]}
            >
              <Select placeholder="Choose the area this measurement refers to">
                {selections.map((selection, index) => (
                  <Option key={index} value={index}>
                    {getSelectionLabel(index, selection)}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="Measurement Type"
              name="measurement_type"
              rules={[{ required: true, message: 'Please select measurement type' }]}
            >
              <Select placeholder="What are you measuring?">
                {measurementTypes.map(type => (
                  <Option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Space.Compact style={{ width: '100%' }}>
              <Form.Item
                name="value"
                rules={[{ required: true, message: 'Please enter measurement value' }]}
                style={{ flex: 1, marginBottom: 0 }}
              >
                <InputNumber
                  placeholder="Measurement value"
                  min={0}
                  step={0.01}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              <Form.Item
                name="unit"
                style={{ marginBottom: 0 }}
              >
                <Select style={{ width: 80 }}>
                  <Option value="m">m</Option>
                  <Option value="mm">mm</Option>
                  <Option value="ft">ft</Option>
                </Select>
              </Form.Item>
            </Space.Compact>

            <Form.Item
              label="Description (Optional)"
              name="description"
            >
              <Select 
                placeholder="Optional description"
                allowClear
                mode="tags"
                style={{ width: '100%' }}
              >
                <Option value="Main span">Main span</Option>
                <Option value="Secondary beam">Secondary beam</Option>
                <Option value="Joist center-to-center">Joist center-to-center</Option>
                <Option value="Wall opening">Wall opening</Option>
              </Select>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<PlusOutlined />}
                style={{ width: '100%' }}
              >
                Add Measurement
              </Button>
            </Form.Item>
          </Form>

          {measurements.length > 0 && (
            <>
              <Divider />
              <Title level={5}>Recorded Measurements</Title>
              <List
                size="small"
                dataSource={measurements}
                renderItem={(measurement) => {
                  const typeInfo = measurementTypes.find(t => t.value === measurement.measurementType);
                  const selection = selections[measurement.selectionIndex];
                  
                  return (
                    <List.Item
                      actions={[
                        <Button
                          type="text"
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={() => removeMeasurement(measurement.id)}
                        />
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <span>{typeInfo?.icon}</span>
                            <Text strong>{typeInfo?.label}</Text>
                            <Text code>{measurement.value} {measurement.unit}</Text>
                          </Space>
                        }
                        description={
                          <Text type="secondary">
                            {getSelectionLabel(measurement.selectionIndex, selection)}
                            {measurement.description && ` • ${measurement.description}`}
                          </Text>
                        }
                      />
                    </List.Item>
                  );
                }}
              />
              
              {getJoistCalculationData() && (
                <Alert
                  message="Ready for Calculation"
                  description={
                    <div>
                      <Text>You have both span length and joist spacing measurements. </Text>
                      <Text code>
                        Span: {getJoistCalculationData()?.span_length.toFixed(3)}m, 
                        Spacing: {getJoistCalculationData()?.joist_spacing.toFixed(3)}m
                      </Text>
                    </div>
                  }
                  type="success"
                  showIcon
                  style={{ marginTop: '16px' }}
                />
              )}
            </>
          )}
        </>
      )}
    </Card>
  );
};

export default ManualMeasurementPanel;