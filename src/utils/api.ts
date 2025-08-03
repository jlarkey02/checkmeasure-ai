import axios from 'axios';
import { 
  JoistCalculationRequest, 
  JoistCalculationResponse, 
  MaterialSpecification,
  PDFAnalysisResult,
  SelectionArea 
} from '../types';
import { config } from './config';

const API_BASE_URL = config.API_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // Increased to 90 seconds for Claude Vision analysis (handles rate limiting)
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
export const apiClient = {
  // Health check
  healthCheck: () => api.get('/health'),
  
  // Materials API
  getAllMaterials: () => api.get<{
    lvl: MaterialSpecification[];
    treated_pine: MaterialSpecification[];
    standard_lengths: number[];
    standard_spacings: number[];
  }>('/api/materials/'),
  
  getJoistMaterials: () => api.get<MaterialSpecification[]>('/api/calculations/materials/joists'),
  
  // Calculations API
  calculateJoists: (request: JoistCalculationRequest) => 
    api.post<JoistCalculationResponse>('/api/calculations/joists', request),
  
  // Generic calculation endpoint
  calculate: (elementCode: string, dimensions: Record<string, number>, options?: any) =>
    api.post('/api/calculations/calculate', {
      element_code: elementCode,
      dimensions,
      options
    }),
  
  // Element types API
  getElementTypes: (activeOnly: boolean = true, category?: string) => {
    const params = new URLSearchParams();
    params.append('active_only', activeOnly.toString());
    if (category) params.append('category', category);
    return api.get(`/api/calculations/element-types?${params.toString()}`);
  },
  
  getElementType: (code: string) => 
    api.get(`/api/calculations/element-types/${code}`),
  
  getCategories: () => 
    api.get<string[]>('/api/calculations/categories'),
  
  // PDF Processing API
  uploadPDF: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<PDFAnalysisResult>('/api/pdf/upload', formData);
  },
  
  extractMeasurements: (file: File, selectionAreas: SelectionArea[]) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('selection_areas', JSON.stringify(selectionAreas));
    return api.post('/api/pdf/extract', formData);
  },
  
  testPDFProcessing: () => api.get('/api/pdf/test'),

  // Multi-Agent System API
  agents: {
    // System control
    getSystemHealth: () => api.get('/api/agents/system/health'),
    getSystemInfo: () => api.get('/api/agents/system/info'),
    controlSystem: (action: 'start' | 'stop' | 'restart') => 
      api.post('/api/agents/system/control', { action }),

    // Agent management
    listAgents: () => api.get('/api/agents/agents'),
    getAgentStatus: (agentId: string) => api.get(`/api/agents/agents/${agentId}`),
    createAgent: (agentType: string, name?: string, config?: any) =>
      api.post('/api/agents/agents/create', { agent_type: agentType, name, config }),
    restartAgent: (agentId: string) => api.post(`/api/agents/agents/${agentId}/restart`),
    deleteAgent: (agentId: string) => api.delete(`/api/agents/agents/${agentId}`),

    // Capabilities
    getCapabilities: () => api.get('/api/agents/capabilities'),

    // Projects
    createProject: (name: string, description: string, tasks: any[], metadata?: any) =>
      api.post('/api/agents/projects', { name, description, tasks, metadata }),
    getProjectStatus: (projectId: string) => api.get(`/api/agents/projects/${projectId}`),
    getProjectResults: (projectId: string) => api.get(`/api/agents/projects/${projectId}/results`),

    // Task execution
    executeTask: (agentType: string, taskType: string, parameters: any, priority?: number) =>
      api.post('/api/agents/tasks/execute', { agent_type: agentType, task_type: taskType, parameters, priority }),

    // Demo endpoints
    demoJoistCalculation: () => api.post('/api/agents/demo/joist-calculation'),
  },
};

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`Making request to: ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    if (error.response?.status === 404) {
      throw new Error('API endpoint not found');
    } else if (error.response?.status === 500) {
      console.error('500 Error Details:', error.response?.data);
      throw new Error(error.response?.data?.detail || 'Server error - please try again later');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout - please try again');
    } else if (error.response?.status === 422) {
      // For validation errors, throw the original error to preserve details
      throw error;
    } else {
      throw new Error(error.response?.data?.detail || 'An error occurred');
    }
  }
);

export default api;