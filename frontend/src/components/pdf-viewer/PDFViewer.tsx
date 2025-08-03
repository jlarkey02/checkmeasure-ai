import React, { useEffect, useRef, useState } from 'react';
import { Spin, Alert, Button, Space, InputNumber } from 'antd';
import { ZoomInOutlined, ZoomOutOutlined, FullscreenOutlined } from '@ant-design/icons';
import * as pdfjsLib from 'pdfjs-dist';
import { useAppStore } from '../../stores/appStore';
import SelectionOverlay from './SelectionOverlay';
import MeasurementOverlay from './MeasurementOverlay';

// Set up PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface PDFViewerProps {
  file: File;
  onAnalysis?: (analysis: any) => void;
  measurements?: any[];
}

const PDFViewer: React.FC<PDFViewerProps> = ({ file, onAnalysis, measurements = [] }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderTask, setRenderTask] = useState<any>(null);
  
  const { 
    currentPage, 
    zoomLevel, 
    setCurrentPage, 
    setZoomLevel,
    selectionAreas,
    activeCalculationType,
    isSelecting 
  } = useAppStore();

  useEffect(() => {
    loadPDF();
  }, [file]);

  useEffect(() => {
    if (pdfDoc) {
      renderPage();
    }
  }, [pdfDoc, currentPage, zoomLevel]);

  const loadPDF = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      
      setPdfDoc(pdf);
      setCurrentPage(1);
      
      // Extract basic PDF information for analysis
      const analysis = {
        pageCount: pdf.numPages,
        pageInfo: {} as Record<number, any>
      };
      
      // Get page dimensions for all pages
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const viewport = page.getViewport({ scale: 1 });
        analysis.pageInfo[i] = {
          width: viewport.width,
          height: viewport.height,
          rotation: viewport.rotation
        };
      }
      
      onAnalysis?.(analysis);
      
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
      // Cancel any existing render task
      if (renderTask) {
        renderTask.cancel();
      }

      const page = await pdfDoc.getPage(currentPage);
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      const viewport = page.getViewport({ scale: zoomLevel });
      
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      const task = page.render({
        canvasContext: context,
        viewport: viewport,
      });
      
      setRenderTask(task);
      await task.promise;
      setRenderTask(null);
      
    } catch (err: any) {
      if (err.name !== 'RenderingCancelledException') {
        console.error('Error rendering page:', err);
        setError('Failed to render PDF page');
      }
    }
  };

  const handleZoomIn = () => {
    setZoomLevel(Math.min(zoomLevel + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(Math.max(zoomLevel - 0.25, 0.5));
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= (pdfDoc?.numPages || 1)) {
      setCurrentPage(page);
    }
  };

  const handleFullscreen = () => {
    if (containerRef.current) {
      containerRef.current.requestFullscreen();
    }
  };

  if (loading) {
    return (
      <div className="pdf-viewer" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Spin size="large" tip="Loading PDF..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="pdf-viewer" style={{ padding: '20px' }}>
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
      </div>
    );
  }

  return (
    <div ref={containerRef} className="pdf-viewer">
      {/* PDF Controls */}
      <div style={{ 
        position: 'sticky', 
        top: 0, 
        background: 'white', 
        padding: '10px', 
        borderBottom: '1px solid #e8e8e8',
        zIndex: 100,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Space>
          <span>Page:</span>
          <InputNumber
            size="small"
            min={1}
            max={pdfDoc?.numPages || 1}
            value={currentPage}
            onChange={(value) => handlePageChange(value || 1)}
            style={{ width: 60 }}
          />
          <span>of {pdfDoc?.numPages || 1}</span>
        </Space>
        
        <Space>
          <Button 
            size="small" 
            icon={<ZoomOutOutlined />} 
            onClick={handleZoomOut}
            disabled={zoomLevel <= 0.5}
          />
          <span>{Math.round(zoomLevel * 100)}%</span>
          <Button 
            size="small" 
            icon={<ZoomInOutlined />} 
            onClick={handleZoomIn}
            disabled={zoomLevel >= 3}
          />
          <Button 
            size="small" 
            icon={<FullscreenOutlined />} 
            onClick={handleFullscreen}
          />
        </Space>
      </div>

      {/* PDF Canvas Container */}
      <div style={{ 
        position: 'relative', 
        display: 'flex', 
        justifyContent: 'center',
        padding: '20px',
        minHeight: 'calc(100% - 60px)',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{ position: 'relative', boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}>
          <canvas
            ref={canvasRef}
            style={{
              display: 'block',
              backgroundColor: 'white',
              cursor: isSelecting ? 'crosshair' : 'default'
            }}
          />
          
          {/* Selection Overlay */}
          <SelectionOverlay
            pageNumber={currentPage}
            canvasWidth={canvasRef.current?.width || 0}
            canvasHeight={canvasRef.current?.height || 0}
            zoomLevel={zoomLevel}
          />
          
          {/* Measurement Overlay */}
          {measurements.length > 0 && (
            <MeasurementOverlay
              measurements={measurements}
              canvasWidth={canvasRef.current?.width || 0}
              canvasHeight={canvasRef.current?.height || 0}
              zoomLevel={zoomLevel}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;