import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import BaseAgent, AgentCapability
from ...calculators.joist_calculator import JoistCalculator, JoistCalculationResult

class JoistCalculationAgent(BaseAgent):
    """
    Specialized agent for joist calculation tasks.
    Integrates with the existing JoistCalculator and provides AI-powered enhancements.
    """
    
    def __init__(self, agent_id: str = None, name: str = None):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="joist_calculation",
                description="Calculate joist requirements including count, length, and blocking",
                input_types=["span_length", "joist_spacing", "building_level"],
                output_types=["joist_count", "joist_length", "blocking_requirements", "cutting_list"],
                dependencies=["material_system"]
            ),
            AgentCapability(
                name="joist_optimization",
                description="Optimize joist layouts for material efficiency",
                input_types=["span_data", "material_constraints"],
                output_types=["optimized_layout", "material_savings"],
                dependencies=["cutting_optimization"]
            ),
            AgentCapability(
                name="load_calculation",
                description="Calculate load requirements for joist sizing",
                input_types=["span_length", "load_type", "spacing"],
                output_types=["required_material", "safety_factors"],
                dependencies=["structural_analysis"]
            )
        ]
        
        super().__init__(
            agent_id=agent_id or f"joist_calc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=name or "Joist Calculation Agent",
            capabilities=capabilities
        )
        
        # Initialize the joist calculator
        self.joist_calculator = JoistCalculator()
        
        # Enhanced calculation features
        self.optimization_enabled = True
        self.ai_recommendations = True
        self.safety_factor_warnings = True
        
        # Performance tracking
        self.calculations_completed = 0
        self.optimization_savings = 0.0
        self.warnings_generated = 0
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute joist calculation tasks"""
        # Extract task type and input data from message payload
        task_type = task_data.get("type")
        input_data = task_data.get("input", {})
        
        # Log the received task data for debugging
        self.logger.info(f"Executing task type: {task_type}")
        self.logger.debug(f"Task data: {task_data}")
        self.logger.debug(f"Input data: {input_data}")
        
        try:
            if task_type == "joist_calculation":
                return await self._calculate_joists(input_data)
            elif task_type == "joist_optimization":
                return await self._optimize_joist_layout(input_data)
            elif task_type == "load_calculation":
                return await self._calculate_loads(input_data)
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
                
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            self.logger.error(f"Task data was: {task_data}")
            raise
    
    async def _calculate_joists(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform joist calculations"""
        # Extract input parameters
        span_length = task_data.get("span_length")
        joist_spacing = task_data.get("joist_spacing", 0.45)  # Default 450mm
        building_level = task_data.get("building_level", "L1")
        room_type = task_data.get("room_type")
        load_type = task_data.get("load_type", "residential")
        
        # Validate inputs
        if not span_length:
            raise ValueError("Span length is required")
        
        self.logger.info(f"Calculating joists for span: {span_length}m, spacing: {joist_spacing}m")
        
        # Perform the calculation
        result = self.joist_calculator.calculate_joists(
            span_length=span_length,
            joist_spacing=joist_spacing,
            building_level=building_level,
            room_type=room_type,
            load_type=load_type
        )
        
        # Enhanced result processing
        enhanced_result = await self._enhance_calculation_result(result, task_data)
        
        self.calculations_completed += 1
        
        return {
            "status": "completed",
            "calculation_result": enhanced_result,
            "ai_recommendations": await self._generate_ai_recommendations(result, task_data),
            "warnings": await self._check_safety_warnings(result, task_data),
            "optimization_suggestions": await self._suggest_optimizations(result, task_data),
            "calculation_notes": result.get("calculation_notes", []),
            "assumptions": result.get("assumptions", [])
        }
    
    async def _enhance_calculation_result(self, result: Dict[str, Any], task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the basic calculation result with additional insights"""
        enhanced = result.copy()
        
        # Add material efficiency metrics
        enhanced["material_efficiency"] = await self._calculate_material_efficiency(result)
        
        # Add cost estimation
        enhanced["cost_estimation"] = await self._estimate_costs(result)
        
        # Add delivery optimization
        enhanced["delivery_optimization"] = await self._optimize_delivery(result)
        
        # Add environmental impact
        enhanced["environmental_impact"] = await self._calculate_environmental_impact(result)
        
        return enhanced
    
    async def _calculate_material_efficiency(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate material efficiency metrics"""
        # Simulate material efficiency calculation
        await asyncio.sleep(0.1)  # Simulate processing time
        
        cutting_list = result.get("cutting_list", [])
        total_required = sum(item.get("total_length", 0) for item in cutting_list)
        total_purchased = sum(item.get("purchased_length", 0) for item in cutting_list)
        
        waste_percentage = 0.0
        if total_purchased > 0:
            waste_percentage = ((total_purchased - total_required) / total_purchased) * 100
        
        return {
            "total_required_length": total_required,
            "total_purchased_length": total_purchased,
            "waste_percentage": round(waste_percentage, 2),
            "efficiency_score": max(0, 100 - waste_percentage),
            "optimization_potential": "high" if waste_percentage > 15 else "medium" if waste_percentage > 10 else "low"
        }
    
    async def _estimate_costs(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate material costs"""
        await asyncio.sleep(0.1)
        
        # Simplified cost calculation (would integrate with real pricing data)
        cutting_list = result.get("cutting_list", [])
        total_cost = 0.0
        
        material_prices = {
            "LVL": 15.50,  # per linear meter
            "Treated Pine": 8.25,  # per linear meter
            "Steel": 22.00  # per linear meter
        }
        
        cost_breakdown = {}
        for item in cutting_list:
            material_type = item.get("material_type", "Treated Pine")
            length = item.get("total_length", 0)
            unit_price = material_prices.get(material_type, 10.0)
            item_cost = length * unit_price
            
            total_cost += item_cost
            cost_breakdown[material_type] = cost_breakdown.get(material_type, 0) + item_cost
        
        return {
            "total_cost": round(total_cost, 2),
            "cost_breakdown": cost_breakdown,
            "cost_per_square_meter": round(total_cost / max(1, result.get("span_area", 1)), 2),
            "currency": "AUD"
        }
    
    async def _optimize_delivery(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize delivery scheduling and logistics"""
        await asyncio.sleep(0.1)
        
        cutting_list = result.get("cutting_list", [])
        
        # Group by material type and supplier
        material_groups = {}
        for item in cutting_list:
            material_type = item.get("material_type", "Unknown")
            if material_type not in material_groups:
                material_groups[material_type] = []
            material_groups[material_type].append(item)
        
        # Suggest delivery optimization
        delivery_suggestions = []
        if len(material_groups) > 1:
            delivery_suggestions.append("Consider consolidating deliveries to reduce transport costs")
        
        if any(len(items) > 10 for items in material_groups.values()):
            delivery_suggestions.append("Large quantity detected - negotiate bulk delivery discount")
        
        return {
            "material_groups": len(material_groups),
            "delivery_suggestions": delivery_suggestions,
            "estimated_delivery_days": min(3, len(material_groups)),
            "consolidation_opportunities": len(material_groups) > 2
        }
    
    async def _calculate_environmental_impact(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate environmental impact metrics"""
        await asyncio.sleep(0.1)
        
        cutting_list = result.get("cutting_list", [])
        
        # Simplified carbon footprint calculation
        carbon_factors = {
            "LVL": 0.45,  # kg CO2 per linear meter
            "Treated Pine": 0.25,  # kg CO2 per linear meter
            "Steel": 1.20  # kg CO2 per linear meter
        }
        
        total_carbon = 0.0
        for item in cutting_list:
            material_type = item.get("material_type", "Treated Pine")
            length = item.get("total_length", 0)
            carbon_factor = carbon_factors.get(material_type, 0.35)
            total_carbon += length * carbon_factor
        
        return {
            "carbon_footprint_kg": round(total_carbon, 2),
            "sustainability_rating": "A" if total_carbon < 50 else "B" if total_carbon < 100 else "C",
            "eco_recommendations": [
                "Consider using certified sustainable timber",
                "Optimize cuts to reduce waste",
                "Plan efficient delivery routes"
            ]
        }
    
    async def _generate_ai_recommendations(self, result: Dict[str, Any], task_data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered recommendations"""
        if not self.ai_recommendations:
            return []
        
        recommendations = []
        
        # Check joist spacing optimization
        spacing = task_data.get("joist_spacing", 0.45)
        if spacing == 0.45:
            recommendations.append("Consider 600mm spacing if load permits - reduces material by 25%")
        
        # Check material selection
        span_length = task_data.get("span_length", 0)
        if span_length > 4.5:
            recommendations.append("LVL material recommended for spans over 4.5m for better performance")
        
        # Check blocking optimization
        joist_count = result.get("joist_count", 0)
        if joist_count > 8:
            recommendations.append("Consider additional blocking rows for improved stability")
        
        # Check waste reduction
        cutting_list = result.get("cutting_list", [])
        if cutting_list:
            total_waste = sum(item.get("waste", 0) for item in cutting_list)
            if total_waste > 15:
                recommendations.append("High waste detected - consider custom lengths or different layout")
        
        return recommendations
    
    async def _check_safety_warnings(self, result: Dict[str, Any], task_data: Dict[str, Any]) -> List[str]:
        """Check for safety concerns and generate warnings"""
        if not self.safety_factor_warnings:
            return []
        
        warnings = []
        
        # Check span limits
        span_length = task_data.get("span_length", 0)
        material_spec = result.get("material_specification", "")
        
        if span_length > 6.0 and "90x45" in material_spec:
            warnings.append("WARNING: Span exceeds recommended limit for 90x45 material")
            self.warnings_generated += 1
        
        # Check spacing limits
        spacing = task_data.get("joist_spacing", 0.45)
        if spacing > 0.6:
            warnings.append("WARNING: Joist spacing exceeds standard maximum of 600mm")
            self.warnings_generated += 1
        
        # Check load considerations
        load_type = task_data.get("load_type", "residential")
        if load_type == "commercial" and span_length > 4.0:
            warnings.append("CAUTION: Commercial loads require engineering verification")
            self.warnings_generated += 1
        
        return warnings
    
    async def _suggest_optimizations(self, result: Dict[str, Any], task_data: Dict[str, Any]) -> List[str]:
        """Suggest optimization opportunities"""
        if not self.optimization_enabled:
            return []
        
        suggestions = []
        
        # Material optimization
        cutting_list = result.get("cutting_list", [])
        for item in cutting_list:
            waste = item.get("waste", 0)
            if waste > 0.5:  # 500mm or more waste
                suggestions.append(f"Optimize {item.get('description', 'material')} cutting to reduce {waste}m waste")
        
        # Layout optimization
        joist_count = result.get("joist_count", 0)
        span_length = task_data.get("span_length", 0)
        if joist_count * 0.45 < span_length:
            savings = span_length - (joist_count * 0.45)
            suggestions.append(f"Layout optimization could save {savings:.2f}m of material")
            self.optimization_savings += savings
        
        return suggestions
    
    async def _optimize_joist_layout(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize joist layout for multiple spans or complex geometries"""
        self.logger.info("Performing joist layout optimization")
        
        # This would implement advanced optimization algorithms
        # For now, return a simplified optimization result
        
        spans = task_data.get("spans", [])
        constraints = task_data.get("constraints", {})
        
        optimization_result = {
            "optimized_spans": len(spans),
            "material_savings": 15.5,  # percentage
            "cost_savings": 234.50,  # AUD
            "layout_efficiency": 92.3,  # percentage
            "recommendations": [
                "Align joist layouts across floors to reduce cutting",
                "Use standard lengths where possible",
                "Consider continuous spans where structurally appropriate"
            ]
        }
        
        return {
            "status": "completed",
            "optimization_result": optimization_result
        }
    
    async def _calculate_loads(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate load requirements and material sizing"""
        self.logger.info("Performing load calculations")
        
        span_length = task_data.get("span_length")
        load_type = task_data.get("load_type", "residential")
        spacing = task_data.get("spacing", 0.45)
        
        # Simplified load calculation (would integrate with structural analysis)
        load_calculations = {
            "dead_load": 0.6,  # kN/m²
            "live_load": 1.5 if load_type == "residential" else 2.5,  # kN/m²
            "total_load": 2.1 if load_type == "residential" else 3.1,
            "required_moment_capacity": span_length ** 2 * 0.125,
            "recommended_material": "200x45 LVL" if span_length > 4.0 else "90x45 H2 MGP10",
            "safety_factor": 2.5
        }
        
        return {
            "status": "completed",
            "load_calculations": load_calculations
        }
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent-specific performance metrics"""
        base_metrics = self.get_info()
        
        agent_metrics = {
            "calculations_completed": self.calculations_completed,
            "optimization_savings": self.optimization_savings,
            "warnings_generated": self.warnings_generated,
            "features": {
                "optimization_enabled": self.optimization_enabled,
                "ai_recommendations": self.ai_recommendations,
                "safety_warnings": self.safety_factor_warnings
            }
        }
        
        base_metrics["agent_specific"] = agent_metrics
        return base_metrics