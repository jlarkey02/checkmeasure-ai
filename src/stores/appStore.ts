import { create } from 'zustand';
import { SelectionArea, CalculationType, PDFAnalysisResult, CalculationResults } from '../types';

interface AppStore {
  // PDF State
  currentPDF: File | null;
  pdfAnalysis: PDFAnalysisResult | null;
  
  // Selection State
  selectionAreas: SelectionArea[];
  activeCalculationType: CalculationType;
  isSelecting: boolean;
  
  // Calculation State
  calculationResults: CalculationResults | null;
  isCalculating: boolean;
  showResults: boolean;
  
  // UI State
  sidebarCollapsed: boolean;
  currentPage: number;
  zoomLevel: number;
  
  // Actions
  setPDF: (file: File) => void;
  setPDFAnalysis: (analysis: PDFAnalysisResult) => void;
  setActiveCalculationType: (type: CalculationType) => void;
  setIsSelecting: (selecting: boolean) => void;
  addSelectionArea: (area: SelectionArea) => void;
  removeSelectionArea: (id: string) => void;
  updateSelectionArea: (id: string, updates: Partial<SelectionArea>) => void;
  clearSelectionAreas: () => void;
  setCalculationResults: (results: CalculationResults) => void;
  setIsCalculating: (calculating: boolean) => void;
  setShowResults: (show: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentPage: (page: number) => void;
  setZoomLevel: (zoom: number) => void;
  reset: () => void;
}

export const useAppStore = create<AppStore>((set, get) => ({
  // Initial state
  currentPDF: null,
  pdfAnalysis: null,
  selectionAreas: [],
  activeCalculationType: 'joist',
  isSelecting: false,
  calculationResults: null,
  isCalculating: false,
  showResults: false,
  sidebarCollapsed: false,
  currentPage: 0,
  zoomLevel: 1.0,
  
  // Actions
  setPDF: (file) => set({ currentPDF: file }),
  
  setPDFAnalysis: (analysis) => set({ pdfAnalysis: analysis }),
  
  setActiveCalculationType: (type) => set({ activeCalculationType: type }),
  
  setIsSelecting: (selecting) => set({ isSelecting: selecting }),
  
  addSelectionArea: (area) => set((state) => ({
    selectionAreas: [...state.selectionAreas, area]
  })),
  
  removeSelectionArea: (id) => set((state) => ({
    selectionAreas: state.selectionAreas.filter(area => area.id !== id)
  })),
  
  updateSelectionArea: (id, updates) => set((state) => ({
    selectionAreas: state.selectionAreas.map(area =>
      area.id === id ? { ...area, ...updates } : area
    )
  })),
  
  clearSelectionAreas: () => set({ selectionAreas: [] }),
  
  setCalculationResults: (results) => set({ calculationResults: results }),
  
  setIsCalculating: (calculating) => set({ isCalculating: calculating }),
  
  setShowResults: (show) => set({ showResults: show }),
  
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  
  setCurrentPage: (page) => set({ currentPage: page }),
  
  setZoomLevel: (zoom) => set({ zoomLevel: zoom }),
  
  reset: () => set({
    currentPDF: null,
    pdfAnalysis: null,
    selectionAreas: [],
    activeCalculationType: 'joist',
    isSelecting: false,
    calculationResults: null,
    isCalculating: false,
    showResults: false,
    currentPage: 0,
    zoomLevel: 1.0,
  }),
}));