import React from 'react';
import { Card, Tag, Space, Typography, Button, Progress, Tooltip } from 'antd';
import { EditOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

export interface Assumption {
  id: string;
  category: 'scale' | 'joist' | 'measurement' | 'material';
  description: string;
  value: string;
  confidence: number;
  source: 'text' | 'vision' | 'manual' | 'default';
  editable: boolean;
}

interface AssumptionsDisplayProps {
  assumptions: Assumption[];
  onEdit?: (id: string) => void;
  minimal?: boolean;  // Show only critical assumptions
}

const AssumptionsDisplay: React.FC<AssumptionsDisplayProps> = ({ 
  assumptions, 
  onEdit,
  minimal = false 
}) => {
  // Category icons and colors
  const categoryConfig = {
    scale: { icon: '📏', color: 'blue', label: 'Scale' },
    joist: { icon: '🏗️', color: 'orange', label: 'Joist' },
    measurement: { icon: '📐', color: 'green', label: 'Measurement' },
    material: { icon: '🪵', color: 'purple', label: 'Material' }
  };

  // Source labels
  const sourceLabels = {
    text: 'Text Extraction',
    vision: 'AI Vision',
    manual: 'Manual Entry',
    default: 'Default Value'
  };

  // Filter for minimal display
  const displayAssumptions = minimal 
    ? assumptions.filter(a => a.category === 'scale' || a.confidence < 80)
    : assumptions;

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return '#52c41a';
    if (confidence >= 70) return '#faad14';
    return '#ff4d4f';
  };

  if (displayAssumptions.length === 0) {
    return null;
  }

  return (
    <Card 
      title={
        <Space>
          <Title level={5} style={{ margin: 0 }}>
            {minimal ? 'Key Assumptions' : 'Analysis Assumptions'}
          </Title>
          <Tooltip title="These assumptions affect the calculation results">
            <InfoCircleOutlined style={{ color: '#1890ff' }} />
          </Tooltip>
        </Space>
      }
      size="small"
      style={{ marginBottom: 16 }}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {displayAssumptions.map(assumption => {
          const config = categoryConfig[assumption.category];
          
          return (
            <div 
              key={assumption.id} 
              style={{ 
                padding: '8px 12px', 
                background: '#fafafa', 
                borderRadius: 4,
                border: '1px solid #f0f0f0'
              }}
            >
              <Space direction="vertical" size={4} style={{ width: '100%' }}>
                {/* Header */}
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Space size={8}>
                    <span>{config.icon}</span>
                    <Text strong>{assumption.description}</Text>
                    <Tag color={config.color} style={{ margin: 0 }}>
                      {config.label}
                    </Tag>
                  </Space>
                  {assumption.editable && onEdit && (
                    <Button 
                      type="text" 
                      size="small" 
                      icon={<EditOutlined />}
                      onClick={() => onEdit(assumption.id)}
                    >
                      Edit
                    </Button>
                  )}
                </Space>

                {/* Value */}
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Text style={{ fontSize: 16, fontWeight: 500 }}>
                    {assumption.value}
                  </Text>
                  <Space size={4}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {sourceLabels[assumption.source]}
                    </Text>
                    {assumption.confidence >= 90 && (
                      <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    )}
                  </Space>
                </Space>

                {/* Confidence bar */}
                {!minimal && (
                  <Progress 
                    percent={assumption.confidence} 
                    strokeColor={getConfidenceColor(assumption.confidence)}
                    size="small"
                    format={percent => `${percent}% confident`}
                  />
                )}
              </Space>
            </div>
          );
        })}
      </Space>

      {minimal && assumptions.length > displayAssumptions.length && (
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <Text type="secondary">
            {assumptions.length - displayAssumptions.length} more assumptions with high confidence
          </Text>
        </div>
      )}
    </Card>
  );
};

export default AssumptionsDisplay;