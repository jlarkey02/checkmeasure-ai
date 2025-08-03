import React from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Space, 
  Tag, 
  Divider, 
  Button,
  Row,
  Col,
  Statistic,
  Alert,
  Collapse
} from 'antd';
import { 
  DownloadOutlined, 
  PrinterOutlined, 
  FileTextOutlined,
  CalculatorOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import { CalculationResults as CalculationResultsType } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface CalculationResultsProps {
  results: CalculationResultsType;
}

const CalculationResults: React.FC<CalculationResultsProps> = ({ results }) => {
  const { joistCalculation, projectInfo, selectionAreas } = results;

  if (!joistCalculation || !projectInfo) {
    return (
      <Alert
        message="No calculation results available"
        type="warning"
        showIcon
      />
    );
  }

  // Table columns for cutting list
  const cuttingListColumns = [
    {
      title: 'Profile/Size',
      dataIndex: 'profile_size',
      key: 'profile_size',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: 'Qty',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'center' as const
    },
    {
      title: 'Length',
      dataIndex: 'length',
      key: 'length',
      width: 100,
      render: (length: number) => `${length.toFixed(1)}m`
    },
    {
      title: 'Cut Length',
      dataIndex: 'cut_length',
      key: 'cut_length',
      width: 100,
      render: (cutLength: number) => `${cutLength.toFixed(1)}m`
    },
    {
      title: 'Reference',
      dataIndex: 'reference',
      key: 'reference',
      width: 120,
      render: (ref: string) => <Tag color="blue">{ref}</Tag>
    },
    {
      title: 'Application',
      dataIndex: 'application',
      key: 'application'
    },
    {
      title: 'Waste',
      dataIndex: 'waste',
      key: 'waste',
      width: 100,
      render: (waste: number) => (
        <Text type={waste > 0.5 ? 'warning' : 'secondary'}>
          {waste.toFixed(2)}m
        </Text>
      )
    }
  ];

  const handleExport = (format: string) => {
    // TODO: Implement export functionality
    console.log(`Exporting as ${format}`);
  };

  const totalLength = joistCalculation.cutting_list.reduce(
    (sum, item) => sum + (item.quantity * item.length), 0
  );

  const totalWaste = joistCalculation.cutting_list.reduce(
    (sum, item) => sum + (item.quantity * item.waste), 0
  );

  const wastePercentage = totalLength > 0 ? (totalWaste / totalLength) * 100 : 0;

  return (
    <div>
      {/* Project Header */}
      <Card size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Title level={4} style={{ margin: 0 }}>
              {projectInfo.projectName}
            </Title>
            <Text type="secondary">
              Client: {projectInfo.clientName} | Engineer: {projectInfo.engineerName}
            </Text>
            <br />
            <Text type="secondary">
              Date: {projectInfo.date} | Revision: {projectInfo.revision}
            </Text>
          </Col>
          <Col span={12} style={{ textAlign: 'right' }}>
            <Space>
              <Button 
                icon={<FileTextOutlined />} 
                onClick={() => handleExport('pdf')}
              >
                Export PDF
              </Button>
              <Button 
                icon={<DownloadOutlined />} 
                onClick={() => handleExport('excel')}
              >
                Export Excel
              </Button>
              <Button 
                icon={<PrinterOutlined />} 
                onClick={() => window.print()}
              >
                Print
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Calculation Summary */}
      <Card 
        title={<><CalculatorOutlined /> Calculation Summary</>} 
        size="small" 
        style={{ marginBottom: '16px' }}
      >
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="Joists Required" 
              value={joistCalculation.joist_count}
              suffix="pieces"
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Joist Length" 
              value={joistCalculation.joist_length}
              suffix="m"
              precision={3}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Blocking Length" 
              value={joistCalculation.blocking_length}
              suffix="m"
              precision={3}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Material" 
              value={joistCalculation.material_specification}
              formatter={(value) => <Text code>{value}</Text>}
            />
          </Col>
        </Row>
      </Card>

      {/* Cutting List */}
      <Card 
        title={<><FileTextOutlined /> Cutting List</>} 
        size="small" 
        style={{ marginBottom: '16px' }}
      >
        <Table
          columns={cuttingListColumns}
          dataSource={joistCalculation.cutting_list.map((item, index) => ({
            ...item,
            key: index
          }))}
          pagination={false}
          size="small"
          summary={(pageData) => (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0} colSpan={2}>
                <Text strong>TOTALS</Text>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={2}>
                <Text strong>{totalLength.toFixed(1)}m</Text>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={3}>-</Table.Summary.Cell>
              <Table.Summary.Cell index={4}>-</Table.Summary.Cell>
              <Table.Summary.Cell index={5}>-</Table.Summary.Cell>
              <Table.Summary.Cell index={6}>
                <Text strong type={wastePercentage > 15 ? 'warning' : 'secondary'}>
                  {totalWaste.toFixed(2)}m ({wastePercentage.toFixed(1)}%)
                </Text>
              </Table.Summary.Cell>
            </Table.Summary.Row>
          )}
        />
      </Card>

      {/* Detailed Information */}
      <Collapse size="small">
        <Panel 
          header={<><CalculatorOutlined /> Calculation Notes</>} 
          key="calculation-notes"
        >
          <div style={{ marginBottom: '16px' }}>
            <Text strong>Step-by-step calculation:</Text>
            <ul style={{ marginTop: '8px' }}>
              {joistCalculation.calculation_notes.map((note, index) => (
                <li key={index}>
                  <Text code style={{ fontSize: '12px' }}>
                    {note}
                  </Text>
                </li>
              ))}
            </ul>
          </div>
        </Panel>

        <Panel 
          header={<><ExperimentOutlined /> Engineering Assumptions</>} 
          key="assumptions"
        >
          <Alert
            message="Material Selection Assumptions"
            description={
              <div style={{ marginTop: '8px' }}>
                <Text strong>The following assumptions were made during calculation:</Text>
                <ul style={{ marginTop: '8px' }}>
                  {joistCalculation.assumptions.map((assumption, index) => (
                    <li key={index}>
                      <Text style={{ fontSize: '12px' }}>
                        {assumption}
                      </Text>
                    </li>
                  ))}
                </ul>
              </div>
            }
            type="info"
            showIcon
          />
        </Panel>

        <Panel 
          header={<><FileTextOutlined /> Selection Areas</>} 
          key="selection-areas"
        >
          <div>
            <Text strong>Areas selected for calculation:</Text>
            {selectionAreas.length > 0 ? (
              <ul style={{ marginTop: '8px' }}>
                {selectionAreas.map((area, index) => (
                  <li key={area.id} style={{ marginBottom: '4px' }}>
                    <Text code style={{ fontSize: '12px' }}>
                      {area.label} - Page {area.pageNumber} 
                      ({area.width.toFixed(1)} × {area.height.toFixed(1)})
                    </Text>
                  </li>
                ))}
              </ul>
            ) : (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                No areas selected (manual input used)
              </Text>
            )}
          </div>
        </Panel>
      </Collapse>

      {/* Footer */}
      <div style={{ 
        marginTop: '24px', 
        padding: '16px',
        backgroundColor: '#f9f9f9',
        borderRadius: '6px',
        textAlign: 'center'
      }}>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          Generated by Building Measurements System v1.0 | 
          Calculations based on Australian Standards (AS1684) | 
          Please review all calculations before use
        </Text>
      </div>
    </div>
  );
};

export default CalculationResults;