import React from 'react';
import { Card, Typography, Table, Tag, Space, Statistic, Row, Col, Alert, Tabs, Progress, Divider } from 'antd';
import { FileTextOutlined, CalculatorOutlined, ExperimentOutlined, BulbOutlined, DollarOutlined, CarOutlined, GlobalOutlined, RobotOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface ResultsDisplayProps {
  results: any;
  isMultiAgent?: boolean;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results, isMultiAgent = false }) => {
  if (!results) return null;

  const columns = [
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

  const totalLength = results.cutting_list?.reduce(
    (sum: number, item: any) => sum + (item.quantity * item.length), 0
  ) || 0;

  const totalWaste = results.cutting_list?.reduce(
    (sum: number, item: any) => sum + (item.quantity * item.waste), 0
  ) || 0;

  return (
    <div style={{ marginTop: '24px' }}>
      {/* Summary Statistics */}
      <Card 
        title={<><CalculatorOutlined /> Calculation Summary</>} 
        style={{ marginBottom: '16px' }}
      >
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="Joists Required" 
              value={results.joist_count || 0}
              suffix="pieces"
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Joist Length" 
              value={results.joist_length || 0}
              suffix="m"
              precision={3}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Blocking Length" 
              value={results.blocking_length || 0}
              suffix="m"
              precision={3}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Material" 
              value={results.material_specification || 'N/A'}
              formatter={(value) => <Text code>{value}</Text>}
            />
          </Col>
        </Row>
      </Card>

      {/* Cutting List */}
      <Card 
        title={<><FileTextOutlined /> Cutting List</>} 
        style={{ marginBottom: '16px' }}
      >
        <Table
          columns={columns}
          dataSource={results.cutting_list?.map((item: any, index: number) => ({
            ...item,
            key: index
          })) || []}
          pagination={false}
          size="small"
          summary={() => (
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
                <Text strong type={totalWaste > 5 ? 'warning' : 'secondary'}>
                  {totalWaste.toFixed(2)}m ({((totalWaste/totalLength)*100).toFixed(1)}%)
                </Text>
              </Table.Summary.Cell>
            </Table.Summary.Row>
          )}
        />
      </Card>

      {/* Calculation Notes */}
      <Card 
        title={<><ExperimentOutlined /> Calculation Details</>}
        size="small"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>Step-by-step calculation:</Text>
            <ul style={{ marginTop: '8px', marginLeft: '16px' }}>
              {results.calculation_notes?.map((note: string, index: number) => (
                <li key={index}>
                  <Text code style={{ fontSize: '12px' }}>
                    {note}
                  </Text>
                </li>
              )) || []}
            </ul>
          </div>

          <Alert
            message="Engineering Assumptions"
            description={
              <div>
                <Text strong>The following assumptions were made:</Text>
                <ul style={{ marginTop: '8px', marginLeft: '16px' }}>
                  {results.assumptions?.map((assumption: string, index: number) => (
                    <li key={index}>
                      <Text style={{ fontSize: '12px' }}>
                        {assumption}
                      </Text>
                    </li>
                  )) || []}
                </ul>
              </div>
            }
            type="info"
            showIcon
          />
        </Space>
      </Card>

      {/* Multi-Agent Enhanced Features */}
      {isMultiAgent && results.calculation_result && (
        <>
          <Alert
            message="AI-Enhanced Results"
            description="This calculation includes AI-powered optimization, cost analysis, and environmental impact assessment."
            type="success"
            showIcon
            icon={<RobotOutlined />}
            style={{ marginBottom: '16px' }}
          />

          <Tabs defaultActiveKey="recommendations" style={{ marginBottom: '16px' }}>
            <Tabs.TabPane tab={<><BulbOutlined /> AI Recommendations</>} key="recommendations">
              <Card>
                {results.ai_recommendations && results.ai_recommendations.length > 0 ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {results.ai_recommendations.map((rec: string, index: number) => (
                      <Alert key={index} message={rec} type="info" showIcon />
                    ))}
                  </Space>
                ) : (
                  <Text type="secondary">No specific recommendations for this calculation.</Text>
                )}
              </Card>
            </Tabs.TabPane>

            <Tabs.TabPane tab={<><DollarOutlined /> Cost Analysis</>} key="cost">
              <Card>
                {results.calculation_result?.cost_estimation ? (
                  <>
                    <Row gutter={16} style={{ marginBottom: '16px' }}>
                      <Col span={8}>
                        <Statistic
                          title="Total Cost"
                          value={results.calculation_result.cost_estimation.total_cost}
                          prefix="$"
                          precision={2}
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Cost per m²"
                          value={results.calculation_result.cost_estimation.cost_per_square_meter}
                          prefix="$"
                          precision={2}
                          suffix="/m²"
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Currency"
                          value={results.calculation_result.cost_estimation.currency}
                        />
                      </Col>
                    </Row>
                    <Divider>Cost Breakdown</Divider>
                    {Object.entries(results.calculation_result.cost_estimation.cost_breakdown || {}).map(([material, cost]: [string, any]) => (
                      <Row key={material} style={{ marginBottom: '8px' }}>
                        <Col span={12}><Text strong>{material}:</Text></Col>
                        <Col span={12}><Text>${cost.toFixed(2)}</Text></Col>
                      </Row>
                    ))}
                  </>
                ) : (
                  <Text type="secondary">Cost analysis not available.</Text>
                )}
              </Card>
            </Tabs.TabPane>

            <Tabs.TabPane tab={<><CarOutlined /> Delivery Optimization</>} key="delivery">
              <Card>
                {results.calculation_result?.delivery_optimization ? (
                  <>
                    <Row gutter={16} style={{ marginBottom: '16px' }}>
                      <Col span={8}>
                        <Statistic
                          title="Material Groups"
                          value={results.calculation_result.delivery_optimization.material_groups}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Estimated Delivery Days"
                          value={results.calculation_result.delivery_optimization.estimated_delivery_days}
                          suffix="days"
                        />
                      </Col>
                      <Col span={8}>
                        <Tag color={results.calculation_result.delivery_optimization.consolidation_opportunities ? 'orange' : 'green'}>
                          {results.calculation_result.delivery_optimization.consolidation_opportunities ? 'Consolidation Opportunity' : 'Optimized'}
                        </Tag>
                      </Col>
                    </Row>
                    {results.calculation_result.delivery_optimization.delivery_suggestions?.length > 0 && (
                      <>
                        <Divider>Delivery Suggestions</Divider>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          {results.calculation_result.delivery_optimization.delivery_suggestions.map((suggestion: string, index: number) => (
                            <Alert key={index} message={suggestion} type="info" showIcon />
                          ))}
                        </Space>
                      </>
                    )}
                  </>
                ) : (
                  <Text type="secondary">Delivery optimization not available.</Text>
                )}
              </Card>
            </Tabs.TabPane>

            <Tabs.TabPane tab={<><GlobalOutlined /> Environmental Impact</>} key="environmental">
              <Card>
                {results.calculation_result?.environmental_impact ? (
                  <>
                    <Row gutter={16} style={{ marginBottom: '16px' }}>
                      <Col span={12}>
                        <Statistic
                          title="Carbon Footprint"
                          value={results.calculation_result.environmental_impact.carbon_footprint_kg}
                          suffix="kg CO₂"
                          precision={2}
                          valueStyle={{ color: results.calculation_result.environmental_impact.carbon_footprint_kg < 50 ? '#3f8600' : '#cf1322' }}
                        />
                      </Col>
                      <Col span={12}>
                        <div>
                          <Text strong>Sustainability Rating: </Text>
                          <Tag color={
                            results.calculation_result.environmental_impact.sustainability_rating === 'A' ? 'green' :
                            results.calculation_result.environmental_impact.sustainability_rating === 'B' ? 'orange' : 'red'
                          }>
                            {results.calculation_result.environmental_impact.sustainability_rating}
                          </Tag>
                        </div>
                      </Col>
                    </Row>
                    {results.calculation_result.environmental_impact.eco_recommendations?.length > 0 && (
                      <>
                        <Divider>Eco Recommendations</Divider>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          {results.calculation_result.environmental_impact.eco_recommendations.map((rec: string, index: number) => (
                            <Alert key={index} message={rec} type="success" showIcon />
                          ))}
                        </Space>
                      </>
                    )}
                  </>
                ) : (
                  <Text type="secondary">Environmental impact analysis not available.</Text>
                )}
              </Card>
            </Tabs.TabPane>

            <Tabs.TabPane tab="Material Efficiency" key="efficiency">
              <Card>
                {results.calculation_result?.material_efficiency ? (
                  <>
                    <Row gutter={16} style={{ marginBottom: '16px' }}>
                      <Col span={6}>
                        <Statistic
                          title="Efficiency Score"
                          value={results.calculation_result.material_efficiency.efficiency_score}
                          suffix="/100"
                          precision={1}
                          valueStyle={{ color: results.calculation_result.material_efficiency.efficiency_score > 85 ? '#3f8600' : '#faad14' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Waste Percentage"
                          value={results.calculation_result.material_efficiency.waste_percentage}
                          suffix="%"
                          precision={1}
                          valueStyle={{ color: results.calculation_result.material_efficiency.waste_percentage < 10 ? '#3f8600' : '#cf1322' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Required Length"
                          value={results.calculation_result.material_efficiency.total_required_length}
                          suffix="m"
                          precision={2}
                        />
                      </Col>
                      <Col span={6}>
                        <div>
                          <Text strong>Optimization: </Text>
                          <Tag color={
                            results.calculation_result.material_efficiency.optimization_potential === 'low' ? 'green' :
                            results.calculation_result.material_efficiency.optimization_potential === 'medium' ? 'orange' : 'red'
                          }>
                            {results.calculation_result.material_efficiency.optimization_potential}
                          </Tag>
                        </div>
                      </Col>
                    </Row>
                    <Progress
                      percent={results.calculation_result.material_efficiency.efficiency_score}
                      status={results.calculation_result.material_efficiency.efficiency_score > 85 ? 'success' : 'normal'}
                      format={(percent) => `${percent}% Efficient`}
                    />
                  </>
                ) : (
                  <Text type="secondary">Material efficiency analysis not available.</Text>
                )}
              </Card>
            </Tabs.TabPane>
          </Tabs>

          {/* Warnings Section */}
          {results.warnings && results.warnings.length > 0 && (
            <Card title="⚠️ Safety Warnings" style={{ marginBottom: '16px' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                {results.warnings.map((warning: string, index: number) => (
                  <Alert key={index} message={warning} type="warning" showIcon />
                ))}
              </Space>
            </Card>
          )}

          {/* Optimization Suggestions */}
          {results.optimization_suggestions && results.optimization_suggestions.length > 0 && (
            <Card title="🔧 Optimization Suggestions">
              <Space direction="vertical" style={{ width: '100%' }}>
                {results.optimization_suggestions.map((suggestion: string, index: number) => (
                  <Alert key={index} message={suggestion} type="info" showIcon />
                ))}
              </Space>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default ResultsDisplay;