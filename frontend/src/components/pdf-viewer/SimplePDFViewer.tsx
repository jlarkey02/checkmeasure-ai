import React, { useEffect, useRef, useState } from 'react';
import { Spin, Alert, Button, Space } from 'antd';
import { ZoomInOutlined, ZoomOutOutlined } from '@ant-design/icons';
import * as pdfjsLib from 'pdfjs-dist';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface SimplePDFViewerProps {
  file: File;
  onSelectionsChange?: (selections: Array<{x: number, y: number, width: number, height: number, page: number}>) => void;
}

const SimplePDFViewer: React.FC<SimplePDFViewerProps> = ({ file, onSelectionsChange }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pageNum, setPageNum] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [scale, setScale] = useState(1.0);
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{x: number, y: number} | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{x: number, y: number} | null>(null);
  const [selections, setSelections] = useState<Array<{x: number, y: number, width: number, height: number, page: number}>>([]);

  useEffect(() => {
    loadPDF();
  }, [file]);

  useEffect(() => {
    if (pdfDoc) {
      renderPage();
    }
  }, [pdfDoc, pageNum, scale]);

  const loadPDF = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      
      setPdfDoc(pdf);
      setPageCount(pdf.numPages);
      setPageNum(1);
      
    } catch (err) {
      console.error('Error loading PDF:', err);
      setError('Failed to load PDF. Please check the file and try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderPage = async () => {
    if (!pdfDoc || !canvasRef.current) return;

    try {
      const page = await pdfDoc.getPage(pageNum);
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      const viewport = page.getViewport({ scale });
      
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      await page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise;
      
    } catch (err) {
      console.error('Error rendering page:', err);
      setError('Failed to render PDF page');
    }
  };

  const handlePrevPage = () => {
    if (pageNum > 1) setPageNum(pageNum - 1);
  };

  const handleNextPage = () => {
    if (pageNum < pageCount) setPageNum(pageNum + 1);
  };

  const handleZoomIn = () => {
    setScale(Math.min(scale + 0.25, 3.0));
  };

  const handleZoomOut = () => {
    setScale(Math.max(scale - 0.25, 0.5));
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setIsSelecting(true);
    setSelectionStart({ x, y });
    setSelectionEnd({ x, y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isSelecting || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setSelectionEnd({ x, y });
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isSelecting || !selectionStart || !selectionEnd) return;
    
    const minWidth = 20;
    const minHeight = 20;
    const width = Math.abs(selectionEnd.x - selectionStart.x);
    const height = Math.abs(selectionEnd.y - selectionStart.y);
    
    if (width > minWidth && height > minHeight) {
      const newSelection = {
        x: Math.min(selectionStart.x, selectionEnd.x),
        y: Math.min(selectionStart.y, selectionEnd.y),
        width,
        height,
        page: pageNum
      };
      
      const updatedSelections = [...selections, newSelection];
      setSelections(updatedSelections);
      onSelectionsChange?.(updatedSelections);
    }
    
    setIsSelecting(false);
    setSelectionStart(null);
    setSelectionEnd(null);
  };

  const clearSelections = () => {
    setSelections([]);
    onSelectionsChange?.([]);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" tip="Loading PDF..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="PDF Loading Error"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={loadPDF}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ border: '1px solid #e8e8e8', borderRadius: '8px', padding: '16px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button onClick={handlePrevPage} disabled={pageNum <= 1}>
            Previous
          </Button>
          <span>Page {pageNum} of {pageCount}</span>
          <Button onClick={handleNextPage} disabled={pageNum >= pageCount}>
            Next
          </Button>
          <Button onClick={clearSelections} disabled={selections.length === 0}>
            Clear Selections ({selections.filter(s => s.page === pageNum).length})
          </Button>
        </Space>
        
        <Space>
          <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} disabled={scale <= 0.5} />
          <span>{Math.round(scale * 100)}%</span>
          <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} disabled={scale >= 3.0} />
        </Space>
      </div>
      
      <div style={{ overflow: 'auto', maxHeight: '600px', textAlign: 'center', backgroundColor: '#f5f5f5', padding: '20px' }}>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            style={{ 
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)', 
              backgroundColor: 'white',
              cursor: isSelecting ? 'crosshair' : 'crosshair'
            }}
          />
          
          {/* Current selection overlay */}
          {isSelecting && selectionStart && selectionEnd && (
            <div
              style={{
                position: 'absolute',
                left: Math.min(selectionStart.x, selectionEnd.x),
                top: Math.min(selectionStart.y, selectionEnd.y),
                width: Math.abs(selectionEnd.x - selectionStart.x),
                height: Math.abs(selectionEnd.y - selectionStart.y),
                border: '2px dashed #1890ff',
                backgroundColor: 'rgba(24, 144, 255, 0.1)',
                pointerEvents: 'none'
              }}
            />
          )}
          
          {/* Saved selections overlay */}
          {selections
            .filter(selection => selection.page === pageNum)
            .map((selection, index) => (
              <div
                key={index}
                style={{
                  position: 'absolute',
                  left: selection.x,
                  top: selection.y,
                  width: selection.width,
                  height: selection.height,
                  border: '2px solid #52c41a',
                  backgroundColor: 'rgba(82, 196, 26, 0.1)',
                  pointerEvents: 'none'
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: -20,
                  left: 0,
                  fontSize: '12px',
                  backgroundColor: '#52c41a',
                  color: 'white',
                  padding: '2px 6px',
                  borderRadius: '3px'
                }}>
                  Area {index + 1}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default SimplePDFViewer;