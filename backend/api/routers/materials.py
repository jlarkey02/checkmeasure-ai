from fastapi import APIRouter
from core.materials.material_system import MaterialSystem

router = APIRouter()

@router.get("/")
async def get_all_materials():
    """Get all available materials"""
    material_system = MaterialSystem()
    return material_system.get_all_materials()

@router.get("/lvl")
async def get_lvl_materials():
    """Get LVL (Laminated Veneer Lumber) materials"""
    material_system = MaterialSystem()
    return material_system.get_lvl_materials()

@router.get("/treated-pine")
async def get_treated_pine_materials():
    """Get treated pine materials"""
    material_system = MaterialSystem()
    return material_system.get_treated_pine_materials()

@router.get("/steel")
async def get_steel_materials():
    """Get steel materials"""
    material_system = MaterialSystem()
    return material_system.get_steel_materials()

@router.get("/standard-lengths")
async def get_standard_lengths():
    """Get standard material lengths"""
    material_system = MaterialSystem()
    return material_system.get_standard_lengths()