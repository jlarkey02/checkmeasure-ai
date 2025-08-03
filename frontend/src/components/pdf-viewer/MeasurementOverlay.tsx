import React from 'react';

interface JoistMeasurement {
  pattern_label: string;
  horizontal_span_m: number;
  vertical_span_m?: number;
  joist_count: number;
  confidence: number;
  measurement_method: string;
  line_details?: any;
  line_coordinates?: {
    horizontal_line?: {
      start_x: number;
      start_y: number;
      end_x: number;
      end_y: number;
    };
    vertical_line?: {
      start_x: number;
      start_y: number;
      end_x: number;
      end_y: number;
    };
  };
}

interface MeasurementOverlayProps {
  measurements: JoistMeasurement[];
  canvasWidth: number;
  canvasHeight: number;
  zoomLevel: number;
}

const MeasurementOverlay: React.FC<MeasurementOverlayProps> = ({
  measurements,
  canvasWidth,
  canvasHeight,
  zoomLevel
}) => {
  const horizontalColor = '#1890ff'; // Blue for horizontal
  const verticalColor = '#52c41a'; // Green for vertical
  const lineWidth = 3;
  const arrowSize = 10;
  const circleRadius = 5;

  const renderArrow = (x: number, y: number, angle: number) => {
    const rad = (angle * Math.PI) / 180;
    const x1 = x - arrowSize * Math.cos(rad - Math.PI / 6);
    const y1 = y - arrowSize * Math.sin(rad - Math.PI / 6);
    const x2 = x - arrowSize * Math.cos(rad + Math.PI / 6);
    const y2 = y - arrowSize * Math.sin(rad + Math.PI / 6);
    
    return `M ${x} ${y} L ${x1} ${y1} M ${x} ${y} L ${x2} ${y2}`;
  };

  const renderMeasurement = (measurement: JoistMeasurement, index: number) => {
    if (!measurement.line_coordinates) return null;

    const elements = [];
    
    // Render horizontal line
    if (measurement.line_coordinates.horizontal_line) {
      const { start_x, start_y, end_x, end_y } = measurement.line_coordinates.horizontal_line;
      const scaledStartX = start_x * zoomLevel;
      const scaledStartY = start_y * zoomLevel;
      const scaledEndX = end_x * zoomLevel;
      const scaledEndY = end_y * zoomLevel;
      
      // Calculate midpoint for label
      const midX = (scaledStartX + scaledEndX) / 2;
      const midY = (scaledStartY + scaledEndY) / 2;
      
      // Calculate angle for arrows
      const angle = Math.atan2(scaledEndY - scaledStartY, scaledEndX - scaledStartX) * 180 / Math.PI;
      
      elements.push(
        <g key={`horizontal-${index}`}>
          {/* Main line */}
          <line
            x1={scaledStartX}
            y1={scaledStartY}
            x2={scaledEndX}
            y2={scaledEndY}
            stroke={horizontalColor}
            strokeWidth={lineWidth}
          />
          
          {/* Start arrow */}
          <path
            d={renderArrow(scaledStartX, scaledStartY, angle + 180)}
            stroke={horizontalColor}
            strokeWidth={lineWidth}
            fill="none"
          />
          
          {/* End arrow */}
          <path
            d={renderArrow(scaledEndX, scaledEndY, angle)}
            stroke={horizontalColor}
            strokeWidth={lineWidth}
            fill="none"
          />
          
          {/* Label */}
          <g transform={`translate(${midX}, ${midY - 10})`}>
            <rect
              x={-40}
              y={-15}
              width={80}
              height={30}
              fill="white"
              fillOpacity={0.9}
              stroke={horizontalColor}
              strokeWidth={1}
              rx={3}
            />
            <text
              x={0}
              y={0}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={horizontalColor}
              fontSize={14}
              fontWeight="bold"
            >
              {measurement.pattern_label}: {measurement.horizontal_span_m.toFixed(3)}m
            </text>
          </g>
        </g>
      );
    }
    
    // Render vertical line
    if (measurement.line_coordinates.vertical_line && measurement.vertical_span_m) {
      const { start_x, start_y, end_x, end_y } = measurement.line_coordinates.vertical_line;
      const scaledStartX = start_x * zoomLevel;
      const scaledStartY = start_y * zoomLevel;
      const scaledEndX = end_x * zoomLevel;
      const scaledEndY = end_y * zoomLevel;
      
      // Calculate midpoint for label
      const midX = (scaledStartX + scaledEndX) / 2;
      const midY = (scaledStartY + scaledEndY) / 2;
      
      elements.push(
        <g key={`vertical-${index}`}>
          {/* Main line */}
          <line
            x1={scaledStartX}
            y1={scaledStartY}
            x2={scaledEndX}
            y2={scaledEndY}
            stroke={verticalColor}
            strokeWidth={lineWidth}
          />
          
          {/* Start circle */}
          <circle
            cx={scaledStartX}
            cy={scaledStartY}
            r={circleRadius}
            fill={verticalColor}
            stroke="white"
            strokeWidth={1}
          />
          
          {/* End circle */}
          <circle
            cx={scaledEndX}
            cy={scaledEndY}
            r={circleRadius}
            fill={verticalColor}
            stroke="white"
            strokeWidth={1}
          />
          
          {/* Label */}
          <g transform={`translate(${midX + 20}, ${midY})`}>
            <rect
              x={-25}
              y={-15}
              width={50}
              height={30}
              fill="white"
              fillOpacity={0.9}
              stroke={verticalColor}
              strokeWidth={1}
              rx={3}
            />
            <text
              x={0}
              y={0}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={verticalColor}
              fontSize={14}
              fontWeight="bold"
            >
              {measurement.vertical_span_m.toFixed(3)}m
            </text>
          </g>
        </g>
      );
    }
    
    return elements;
  };

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: canvasWidth,
        height: canvasHeight,
        pointerEvents: 'none',
        zIndex: 2
      }}
      viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
    >
      {measurements.map((measurement, index) => renderMeasurement(measurement, index))}
    </svg>
  );
};

export default MeasurementOverlay;