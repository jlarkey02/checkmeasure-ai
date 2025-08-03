export interface SelectionArea {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  pageNumber: number;
  calculationType: CalculationType;
  label?: string;
  measurements?: Measurement[];
}

export interface Measurement {
  value: number;
  unit: string;
  text: string;
  bbox: [number, number, number, number];
}

export interface PDFPageInfo {
  pageNumber: number;
  width: number;
  height: number;
  rotation: number;
}

export interface PDFAnalysisResult {
  scale?: string;
  dimensions: Measurement[];
  textBlocks: TextBlock[];
  pageInfo: Record<number, PDFPageInfo>;
}

export interface TextBlock {
  text: string;
  bbox: [number, number, number, number];
  pageNumber: number;
  fontSize: number;
  confidence: number;
}

export type CalculationType = 'joist' | 'beam' | 'wall' | 'rafter' | 'flooring';

export interface JoistCalculationRequest {
  span_length: number;
  joist_spacing: number;
  building_level: string;
  room_type?: string;
  load_type?: string;
}

export interface JoistCalculationResponse {
  joist_count: number;
  joist_length: number;
  blocking_length: number;
  material_specification: string;
  reference_code: string;
  cutting_list: CuttingListItem[];
  calculation_notes: string[];
  assumptions: string[];
}

export interface CuttingListItem {
  profile_size: string;
  quantity: number;
  length: number;
  cut_length: number;
  reference: string;
  application: string;
  waste: number;
}

export interface MaterialSpecification {
  specification: string;
  profile: string;
  grade: string;
  application: string;
  loadCapacity: number;
  maxSpan?: number;
}

export interface ProjectInfo {
  projectName: string;
  clientName: string;
  engineerName: string;
  date: string;
  revision: string;
  deliveryNumber: number;
}

export interface CalculationResults {
  joistCalculation?: JoistCalculationResponse;
  projectInfo?: ProjectInfo;
  selectionAreas: SelectionArea[];
  pdfAnalysis?: PDFAnalysisResult;
}

export interface AppState {
  currentPDF: File | null;
  pdfAnalysis: PDFAnalysisResult | null;
  selectionAreas: SelectionArea[];
  activeCalculationType: CalculationType;
  calculationResults: CalculationResults | null;
  isCalculating: boolean;
  showResults: boolean;
}

// Multi-Agent System Types
export interface AgentCapability {
  name: string;
  description: string;
  input_types: string[];
  output_types: string[];
  dependencies: string[];
}

export interface AgentStatus {
  agent_id: string;
  name: string;
  status: 'idle' | 'working' | 'error' | 'completed' | 'failed';
  health: 'healthy' | 'degraded' | 'unhealthy' | 'unresponsive';
  last_seen: string;
  restart_attempts: number;
  active_tasks: number;
  capabilities: string[];
  performance: {
    tasks_completed: number;
    tasks_failed: number;
    average_processing_time: number;
    queue_size: number;
    last_activity: string;
  };
  error?: string;
}

export interface SystemHealth {
  overall_health: 'healthy' | 'degraded' | 'unhealthy';
  total_agents: number;
  healthy_agents: number;
  unhealthy_agents: number;
  available_capabilities: number;
  available_agent_types: number;
  event_bus_metrics: {
    messages_sent: number;
    messages_failed: number;
    average_delivery_time: number;
    queue_size: number;
    active_subscribers: number;
    registered_agents: number;
    message_history_size: number;
  };
  agent_manager_metrics: {
    total_agents_registered: number;
    active_agents: number;
    total_restarts: number;
    total_failures: number;
    health_distribution: Record<string, number>;
    failed_agents_count: number;
    system_uptime: number;
  };
  orchestrator_metrics: {
    projects_completed: number;
    projects_failed: number;
    average_project_duration: number;
    total_tasks_executed: number;
    active_projects: number;
    active_tasks: number;
    registered_agents: number;
    agent_workloads: Record<string, number>;
  };
}

export interface ProjectStatus {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  task_details: Record<string, {
    name: string;
    status: string;
    assigned_agent?: string;
    progress: number;
  }>;
}

export interface CapabilityInfo {
  capabilities: string[];
  agent_types: string[];
}

export interface AgentTask {
  id: string;
  name: string;
  description: string;
  type: string;
  priority: number;
  dependencies: string[];
  required_capabilities: string[];
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  assigned_agent?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_duration: number;
  actual_duration?: number;
  retry_count: number;
  max_retries: number;
  error_message?: string;
}

export interface MultiAgentCalculationResult {
  status: string;
  calculation_result: JoistCalculationResponse & {
    material_efficiency: {
      total_required_length: number;
      total_purchased_length: number;
      waste_percentage: number;
      efficiency_score: number;
      optimization_potential: string;
    };
    cost_estimation: {
      total_cost: number;
      cost_breakdown: Record<string, number>;
      cost_per_square_meter: number;
      currency: string;
    };
    delivery_optimization: {
      material_groups: number;
      delivery_suggestions: string[];
      estimated_delivery_days: number;
      consolidation_opportunities: boolean;
    };
    environmental_impact: {
      carbon_footprint_kg: number;
      sustainability_rating: string;
      eco_recommendations: string[];
    };
  };
  ai_recommendations: string[];
  warnings: string[];
  optimization_suggestions: string[];
  calculation_notes: string[];
  assumptions: string[];
}