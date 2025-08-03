import React, { useState, useRef, useCallback } from 'react';
import { useAppStore } from '../../stores/appStore';
import { SelectionArea } from '../../types';

interface SelectionOverlayProps {
  pageNumber: number;
  canvasWidth: number;
  canvasHeight: number;
  zoomLevel: number;
}

interface SelectionState {
  isSelecting: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

const SelectionOverlay: React.FC<SelectionOverlayProps> = ({
  pageNumber,
  canvasWidth,
  canvasHeight,
  zoomLevel
}) => {
  const {
    selectionAreas,
    activeCalculationType,
    isSelecting,
    addSelectionArea,
    removeSelectionArea,
    setIsSelecting
  } = useAppStore();

  const [selection, setSelection] = useState<SelectionState>({
    isSelecting: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0
  });

  const overlayRef = useRef<HTMLDivElement>(null);

  const getRelativePosition = useCallback((clientX: number, clientY: number) => {
    if (!overlayRef.current) return { x: 0, y: 0 };
    
    const rect = overlayRef.current.getBoundingClientRect();
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!isSelecting) return;
    
    e.preventDefault();
    const pos = getRelativePosition(e.clientX, e.clientY);
    
    setSelection({
      isSelecting: true,
      startX: pos.x,
      startY: pos.y,
      currentX: pos.x,
      currentY: pos.y
    });
  }, [isSelecting, getRelativePosition]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!selection.isSelecting) return;
    
    e.preventDefault();
    const pos = getRelativePosition(e.clientX, e.clientY);
    
    setSelection(prev => ({
      ...prev,
      currentX: pos.x,
      currentY: pos.y
    }));
  }, [selection.isSelecting, getRelativePosition]);

  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    if (!selection.isSelecting) return;
    
    e.preventDefault();
    const pos = getRelativePosition(e.clientX, e.clientY);
    
    const x = Math.min(selection.startX, pos.x);
    const y = Math.min(selection.startY, pos.y);
    const width = Math.abs(pos.x - selection.startX);
    const height = Math.abs(pos.y - selection.startY);
    
    // Only create selection if it's large enough
    if (width > 10 && height > 10) {
      const newArea: SelectionArea = {
        id: `selection-${Date.now()}`,
        x: x / zoomLevel,
        y: y / zoomLevel,
        width: width / zoomLevel,
        height: height / zoomLevel,
        pageNumber,
        calculationType: activeCalculationType,
        label: `${activeCalculationType.charAt(0).toUpperCase() + activeCalculationType.slice(1)} ${selectionAreas.filter(a => a.pageNumber === pageNumber && a.calculationType === activeCalculationType).length + 1}`
      };
      
      addSelectionArea(newArea);
    }
    
    setSelection({
      isSelecting: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0
    });
    
    setIsSelecting(false);
  }, [selection, getRelativePosition, zoomLevel, pageNumber, activeCalculationType, selectionAreas, addSelectionArea, setIsSelecting]);

  const handleAreaClick = useCallback((area: SelectionArea, e: React.MouseEvent) => {
    e.stopPropagation();
    // Could implement area editing here
  }, []);

  const handleAreaDoubleClick = useCallback((area: SelectionArea, e: React.MouseEvent) => {
    e.stopPropagation();
    removeSelectionArea(area.id);
  }, [removeSelectionArea]);

  const getCurrentSelection = () => {
    if (!selection.isSelecting) return null;
    
    const x = Math.min(selection.startX, selection.currentX);
    const y = Math.min(selection.startY, selection.currentY);
    const width = Math.abs(selection.currentX - selection.startX);
    const height = Math.abs(selection.currentY - selection.startY);
    
    return { x, y, width, height };
  };

  const getCalculationTypeColor = (type: string) => {
    const colors = {
      joist: '#1890ff',
      beam: '#52c41a',
      wall: '#faad14',
      rafter: '#722ed1',
      flooring: '#eb2f96'
    };
    return colors[type as keyof typeof colors] || '#1890ff';
  };

  const currentSelection = getCurrentSelection();
  const pageSelections = selectionAreas.filter(area => area.pageNumber === pageNumber);

  return (
    <div
      ref={overlayRef}
      className="selection-overlay"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: canvasWidth,
        height: canvasHeight,
        cursor: isSelecting ? 'crosshair' : 'default',
        pointerEvents: isSelecting ? 'auto' : 'none'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Existing selection areas */}
      {pageSelections.map((area) => (
        <div
          key={area.id}
          className="selection-rectangle"
          style={{
            position: 'absolute',
            left: area.x * zoomLevel,
            top: area.y * zoomLevel,
            width: area.width * zoomLevel,
            height: area.height * zoomLevel,
            border: `2px solid ${getCalculationTypeColor(area.calculationType)}`,
            backgroundColor: `${getCalculationTypeColor(area.calculationType)}20`,
            pointerEvents: 'auto',
            cursor: 'pointer'
          }}
          onClick={(e) => handleAreaClick(area, e)}
          onDoubleClick={(e) => handleAreaDoubleClick(area, e)}
        >
          <div
            className="selection-label"
            style={{
              position: 'absolute',
              top: -25,
              left: 0,
              backgroundColor: getCalculationTypeColor(area.calculationType),
              color: 'white',
              padding: '2px 8px',
              borderRadius: '3px',
              fontSize: '12px',
              fontWeight: 500,
              whiteSpace: 'nowrap'
            }}
          >
            {area.label}
          </div>
        </div>
      ))}

      {/* Current selection being drawn */}
      {currentSelection && (
        <div
          className="selection-rectangle"
          style={{
            position: 'absolute',
            left: currentSelection.x,
            top: currentSelection.y,
            width: currentSelection.width,
            height: currentSelection.height,
            border: `2px dashed ${getCalculationTypeColor(activeCalculationType)}`,
            backgroundColor: `${getCalculationTypeColor(activeCalculationType)}20`,
            pointerEvents: 'none'
          }}
        />
      )}
    </div>
  );
};

export default SelectionOverlay;