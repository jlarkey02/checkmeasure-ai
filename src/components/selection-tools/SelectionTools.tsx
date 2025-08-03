import React from 'react';
import { Button, Space, Typography, Divider, Badge } from 'antd';
import { 
  BorderOutlined, 
  ColumnHeightOutlined, 
  AppstoreOutlined, 
  LineOutlined,
  BuildOutlined,
  ClearOutlined 
} from '@ant-design/icons';
import { useAppStore } from '../../stores/appStore';
import { CalculationType } from '../../types';

const { Text } = Typography;

interface CalculationTypeConfig {
  type: CalculationType;
  label: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}

const calculationTypes: CalculationTypeConfig[] = [
  {
    type: 'joist',
    label: 'Floor Joists',
    icon: <ColumnHeightOutlined />,
    color: '#1890ff',
    description: 'Select floor joist areas for calculation'
  },
  {
    type: 'beam',
    label: 'Beams',
    icon: <LineOutlined />,
    color: '#52c41a',
    description: 'Select beam locations'
  },
  {
    type: 'wall',
    label: 'Wall Framing',
    icon: <BorderOutlined />,
    color: '#faad14',
    description: 'Select wall sections for framing'
  },
  {
    type: 'rafter',
    label: 'Roof Rafters',
    icon: <LineOutlined style={{ transform: 'rotate(45deg)' }} />,
    color: '#722ed1',
    description: 'Select roof areas for rafter calculation'
  },
  {
    type: 'flooring',
    label: 'Flooring',
    icon: <AppstoreOutlined />,
    color: '#eb2f96',
    description: 'Select flooring areas'
  }
];

const SelectionTools: React.FC = () => {
  const {
    activeCalculationType,
    isSelecting,
    selectionAreas,
    setActiveCalculationType,
    setIsSelecting,
    clearSelectionAreas
  } = useAppStore();

  const handleCalculationTypeChange = (type: CalculationType) => {
    setActiveCalculationType(type);
    setIsSelecting(false);
  };

  const handleStartSelection = () => {
    setIsSelecting(true);
  };

  const handleClearSelections = () => {
    clearSelectionAreas();
    setIsSelecting(false);
  };

  const getSelectionCount = (type: CalculationType) => {
    return selectionAreas.filter(area => area.calculationType === type).length;
  };

  const activeConfig = calculationTypes.find(config => config.type === activeCalculationType);

  return (
    <div style={{ padding: '16px' }}>
      <Typography.Title level={4} style={{ marginBottom: '16px' }}>
        Selection Tools
      </Typography.Title>

      {/* Calculation Type Selection */}
      <div style={{ marginBottom: '16px' }}>
        <Text strong style={{ marginBottom: '8px', display: 'block' }}>
          Calculation Type:
        </Text>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {calculationTypes.map((config) => (
            <Badge 
              key={config.type}
              count={getSelectionCount(config.type)}
              size="small"
              color={config.color}
              style={{ marginRight: '8px' }}
            >
              <Button
                type={activeCalculationType === config.type ? 'primary' : 'default'}
                icon={config.icon}
                onClick={() => handleCalculationTypeChange(config.type)}
                style={{ 
                  width: '100%',
                  textAlign: 'left',
                  borderColor: config.color,
                  ...(activeCalculationType === config.type ? { backgroundColor: config.color } : {})
                }}
              >
                {config.label}
              </Button>
            </Badge>
          ))}
        </Space>
      </div>

      <Divider />

      {/* Active Selection Info */}
      {activeConfig && (
        <div style={{ marginBottom: '16px' }}>
          <Text strong>Active Tool:</Text>
          <div style={{ 
            padding: '8px', 
            backgroundColor: `${activeConfig.color}10`,
            border: `1px solid ${activeConfig.color}30`,
            borderRadius: '4px',
            marginTop: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
              {activeConfig.icon}
              <Text strong style={{ marginLeft: '8px' }}>
                {activeConfig.label}
              </Text>
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {activeConfig.description}
            </Text>
          </div>
        </div>
      )}

      {/* Selection Controls */}
      <div style={{ marginBottom: '16px' }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Button
            type="primary"
            icon={<BuildOutlined />}
            size="large"
            onClick={handleStartSelection}
            loading={isSelecting}
            style={{ width: '100%' }}
          >
            {isSelecting ? 'Selecting...' : 'Start Selection'}
          </Button>

          <Button
            danger
            icon={<ClearOutlined />}
            onClick={handleClearSelections}
            disabled={selectionAreas.length === 0}
            style={{ width: '100%' }}
          >
            Clear All Selections
          </Button>
        </Space>
      </div>

      <Divider />

      {/* Selection Summary */}
      <div>
        <Text strong style={{ marginBottom: '8px', display: 'block' }}>
          Selections Summary:
        </Text>
        
        {selectionAreas.length === 0 ? (
          <Text type="secondary" style={{ fontSize: '12px' }}>
            No selections made yet. Choose a calculation type and start selecting areas on the PDF.
          </Text>
        ) : (
          <div style={{ fontSize: '12px' }}>
            {calculationTypes.map((config) => {
              const count = getSelectionCount(config.type);
              if (count === 0) return null;
              
              return (
                <div key={config.type} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    {config.icon}
                    <Text style={{ marginLeft: '8px', fontSize: '12px' }}>
                      {config.label}
                    </Text>
                  </div>
                  <Badge 
                    count={count} 
                    size="small" 
                    color={config.color}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Instructions */}
      <Divider />
      <div>
        <Text strong style={{ fontSize: '12px', marginBottom: '8px', display: 'block' }}>
          Instructions:
        </Text>
        <ul style={{ fontSize: '11px', margin: 0, paddingLeft: '16px' }}>
          <li>Select a calculation type above</li>
          <li>Click "Start Selection" to begin</li>
          <li>Click and drag on the PDF to select areas</li>
          <li>Double-click a selection to remove it</li>
          <li>Different calculation types use different colors</li>
        </ul>
      </div>
    </div>
  );
};

export default SelectionTools;