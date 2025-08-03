from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.calculators.joist_calculator import JoistCalculator
from core.materials.material_system import MaterialSystem
from core.calculators.calculator_factory import CalculatorFactory, create_calculator
from core.calculators.element_types import element_registry, CalculatorType
import logging

print("[CALCULATIONS ROUTER] Importing calculations router...")

router = APIRouter()
logger = logging.getLogger(__name__)

print(f"[CALCULATIONS ROUTER] Element registry has {len(element_registry._types)} types")

class JoistCalculationRequest(BaseModel):
    span_length: float  # meters
    joist_spacing: float  # meters (0.3, 0.45, 0.6)
    building_level: str  # "GF", "L1", "RF"
    room_type: Optional[str] = None
    load_type: Optional[str] = "residential"

class JoistCalculationResponse(BaseModel):
    joist_count: int
    joist_length: float
    blocking_length: float
    material_specification: str
    reference_code: str
    cutting_list: List[dict]
    calculation_notes: List[str]

@router.post("/joists", response_model=JoistCalculationResponse)
async def calculate_joists(request: JoistCalculationRequest):
    try:
        calculator = JoistCalculator()
        material_system = MaterialSystem()
        
        # Perform joist calculation
        result = calculator.calculate_joists(
            span_length=request.span_length,
            joist_spacing=request.joist_spacing,
            building_level=request.building_level,
            room_type=request.room_type,
            load_type=request.load_type
        )
        
        # Get material specification
        material_spec = material_system.get_joist_material(
            span_length=request.span_length,
            load_type=request.load_type
        )
        
        return JoistCalculationResponse(
            joist_count=result["joist_count"],
            joist_length=result["joist_length"],
            blocking_length=result["blocking_length"],
            material_specification=material_spec["specification"],
            reference_code=result["reference_code"],
            cutting_list=result["cutting_list"],
            calculation_notes=result["calculation_notes"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/materials/joists")
async def get_joist_materials():
    """Get available joist materials and specifications"""
    material_system = MaterialSystem()
    return material_system.get_joist_materials()


# New generic calculation endpoints

class GenericCalculationRequest(BaseModel):
    element_code: str  # e.g., 'J1', 'S1', '1B3'
    dimensions: Dict[str, float]  # e.g., {'width': 3.386, 'length': 4.872}
    options: Optional[Dict[str, Any]] = None  # Additional options


class GenericCalculationResponse(BaseModel):
    element_code: str
    element_description: str
    calculation_result: Dict[str, Any]
    formatted_output: str
    warnings: List[str] = []


@router.post("/calculate", response_model=GenericCalculationResponse)
async def calculate_generic(request: GenericCalculationRequest):
    """
    Generic calculation endpoint that works with any element type.
    
    This endpoint:
    - Accepts any element code from the registry
    - Uses the appropriate calculator (or generic if not implemented)
    - Returns calculation results in a consistent format
    """
    try:
        # Create calculator for the element type
        calculator = create_calculator(request.element_code)
        if not calculator:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown or inactive element code: {request.element_code}"
            )
        
        # Get element info
        element_spec = element_registry.get(request.element_code)
        
        # Perform calculation
        result = calculator.calculate(
            dimensions=request.dimensions,
            options=request.options
        )
        
        # Format output
        formatted = calculator.format_output(result)
        
        return GenericCalculationResponse(
            element_code=request.element_code,
            element_description=element_spec.description,
            calculation_result=result,
            formatted_output=formatted,
            warnings=result.get('warnings', [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


class ElementTypeInfo(BaseModel):
    code: str
    description: str
    category: str
    calculator_type: str
    specification: Dict[str, Any]
    active: bool


@router.get("/element-types", response_model=List[ElementTypeInfo])
async def get_element_types(active_only: bool = True, category: Optional[str] = None):
    """
    Get all available element types from the registry.
    
    Query parameters:
    - active_only: If true, only return active element types
    - category: Filter by category (e.g., 'Floor System', 'Wall Framing')
    """
    try:
        logger.info(f"Getting element types - active_only: {active_only}, category: {category}")
        logger.info(f"Element registry type: {type(element_registry)}")
        logger.info(f"Element registry has get_all: {hasattr(element_registry, 'get_all')}")
        
        all_types = element_registry.get_all(active_only=active_only)
        logger.info(f"Found {len(all_types)} element types")
        
        result = []
        for code, spec in all_types.items():
            # Apply category filter if provided
            if category and spec.category != category:
                continue
            
            result.append(ElementTypeInfo(
                code=spec.code,
                description=spec.description,
                category=spec.category,
                calculator_type=spec.calculator_type.value,
                specification=spec.specification,
                active=spec.active
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error getting element types: {str(e)}", exc_info=True)
        # Return empty list instead of crashing
        return []


@router.get("/element-types/{code}", response_model=ElementTypeInfo)
async def get_element_type(code: str):
    """Get details for a specific element type."""
    try:
        spec = element_registry.get(code)
        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Element type '{code}' not found"
            )
        
        return ElementTypeInfo(
            code=spec.code,
            description=spec.description,
            category=spec.category,
            calculator_type=spec.calculator_type.value,
            specification=spec.specification,
            active=spec.active
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error getting element type {code}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error getting element type '{code}'"
        )


@router.get("/categories")
async def get_categories():
    """Get all available element categories."""
    return element_registry.get_categories()