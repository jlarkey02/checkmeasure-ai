from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import json

@dataclass
class ProjectInfo:
    project_name: str
    client_name: str
    engineer_name: str
    date: str
    revision: str = "A"
    delivery_number: int = 1

@dataclass
class CuttingListItem:
    profile_size: str
    quantity: int
    length: float
    reference: str
    application: str
    material_type: str
    waste: float = 0.0

class CuttingListGenerator:
    def __init__(self):
        self.material_categories = {
            "TREATED_PINE": "Treated Pine",
            "LVL": "LVL (Laminated Veneer Lumber)",
            "STEEL": "Steel Components",
            "SHEET_MATERIAL": "Building Products"
        }
    
    def generate_cutting_list(
        self,
        project_info: ProjectInfo,
        cutting_items: List[CuttingListItem],
        calculation_notes: List[str] = None
    ) -> Dict:
        """
        Generate cutting list in client format
        Based on the examples: organized by material type with proper headers
        """
        
        # Group items by material type
        grouped_items = self._group_by_material_type(cutting_items)
        
        # Generate header
        header = self._generate_header(project_info)
        
        # Generate material sections
        material_sections = []
        for material_type, items in grouped_items.items():
            section = self._generate_material_section(material_type, items)
            material_sections.append(section)
        
        # Generate summary
        summary = self._generate_summary(cutting_items)
        
        cutting_list = {
            "header": header,
            "material_sections": material_sections,
            "summary": summary,
            "calculation_notes": calculation_notes or [],
            "generated_at": datetime.now().isoformat()
        }
        
        return cutting_list
    
    def _generate_header(self, project_info: ProjectInfo) -> Dict:
        """Generate header section matching client format"""
        return {
            "project_name": project_info.project_name,
            "client": project_info.client_name,
            "engineer": project_info.engineer_name,
            "date": project_info.date,
            "revision": project_info.revision,
            "delivery": f"DELV #{project_info.delivery_number}",
            "title": f"Cutting List - {project_info.project_name}",
            "subtitle": f"Delivery {project_info.delivery_number}"
        }
    
    def _group_by_material_type(self, items: List[CuttingListItem]) -> Dict:
        """Group cutting list items by material type"""
        grouped = {}
        
        for item in items:
            material_category = self._get_material_category(item.material_type)
            if material_category not in grouped:
                grouped[material_category] = []
            grouped[material_category].append(item)
        
        return grouped
    
    def _get_material_category(self, material_type: str) -> str:
        """Get material category for grouping"""
        return self.material_categories.get(material_type, "Other Materials")
    
    def _generate_material_section(self, material_type: str, items: List[CuttingListItem]) -> Dict:
        """Generate a material section matching client format"""
        
        section_items = []
        for item in items:
            section_items.append({
                "profile_size": item.profile_size,
                "quantity": item.quantity,
                "length": f"{item.length:.1f}m",
                "reference": item.reference,
                "application": item.application,
                "waste": f"{item.waste:.2f}m" if item.waste > 0 else "0.00m"
            })
        
        # Calculate section totals
        total_pieces = sum(item.quantity for item in items)
        total_length = sum(item.quantity * item.length for item in items)
        total_waste = sum(item.waste * item.quantity for item in items)
        
        return {
            "material_type": material_type,
            "items": section_items,
            "totals": {
                "total_pieces": total_pieces,
                "total_length": f"{total_length:.1f}m",
                "total_waste": f"{total_waste:.2f}m",
                "waste_percentage": f"{(total_waste/total_length)*100:.1f}%" if total_length > 0 else "0.0%"
            }
        }
    
    def _generate_summary(self, items: List[CuttingListItem]) -> Dict:
        """Generate overall summary"""
        total_pieces = sum(item.quantity for item in items)
        total_length = sum(item.quantity * item.length for item in items)
        total_waste = sum(item.waste * item.quantity for item in items)
        
        # Group by material type for summary
        material_totals = {}
        for item in items:
            material_category = self._get_material_category(item.material_type)
            if material_category not in material_totals:
                material_totals[material_category] = {
                    "pieces": 0,
                    "length": 0.0,
                    "waste": 0.0
                }
            
            material_totals[material_category]["pieces"] += item.quantity
            material_totals[material_category]["length"] += item.quantity * item.length
            material_totals[material_category]["waste"] += item.waste * item.quantity
        
        return {
            "total_pieces": total_pieces,
            "total_length": f"{total_length:.1f}m",
            "total_waste": f"{total_waste:.2f}m",
            "waste_percentage": f"{(total_waste/total_length)*100:.1f}%" if total_length > 0 else "0.0%",
            "material_breakdown": material_totals
        }
    
    def export_to_text(self, cutting_list: Dict) -> str:
        """Export cutting list to formatted text matching client format"""
        
        text_output = []
        
        # Header
        header = cutting_list["header"]
        text_output.append("=" * 80)
        text_output.append(f"PROJECT: {header['project_name']}")
        text_output.append(f"CLIENT: {header['client']}")
        text_output.append(f"ENGINEER: {header['engineer']}")
        text_output.append(f"DATE: {header['date']}")
        text_output.append(f"REVISION: {header['revision']}")
        text_output.append(f"DELIVERY: {header['delivery']}")
        text_output.append("=" * 80)
        text_output.append("")
        
        # Material sections
        for section in cutting_list["material_sections"]:
            text_output.append(f"{section['material_type']}")
            text_output.append("-" * 80)
            text_output.append(f"{'Profile/Size':<20} {'Qty':<5} {'Length':<10} {'Reference':<15} {'Application':<20} {'Waste':<10}")
            text_output.append("-" * 80)
            
            for item in section["items"]:
                text_output.append(
                    f"{item['profile_size']:<20} {item['quantity']:<5} {item['length']:<10} "
                    f"{item['reference']:<15} {item['application']:<20} {item['waste']:<10}"
                )
            
            text_output.append("-" * 80)
            totals = section["totals"]
            text_output.append(f"SECTION TOTALS: {totals['total_pieces']} pieces, {totals['total_length']}, Waste: {totals['total_waste']} ({totals['waste_percentage']})")
            text_output.append("")
        
        # Summary
        summary = cutting_list["summary"]
        text_output.append("=" * 80)
        text_output.append("PROJECT SUMMARY")
        text_output.append("=" * 80)
        text_output.append(f"Total Pieces: {summary['total_pieces']}")
        text_output.append(f"Total Length: {summary['total_length']}")
        text_output.append(f"Total Waste: {summary['total_waste']} ({summary['waste_percentage']})")
        text_output.append("")
        
        # Calculation notes
        if cutting_list["calculation_notes"]:
            text_output.append("CALCULATION NOTES:")
            text_output.append("-" * 40)
            for note in cutting_list["calculation_notes"]:
                text_output.append(f"• {note}")
            text_output.append("")
        
        text_output.append(f"Generated: {cutting_list['generated_at']}")
        
        return "\n".join(text_output)
    
    def export_to_json(self, cutting_list: Dict) -> str:
        """Export cutting list to JSON format"""
        return json.dumps(cutting_list, indent=2)
    
    def create_joist_cutting_list(
        self,
        project_info: ProjectInfo,
        joist_calculation: Dict
    ) -> Dict:
        """Create cutting list specifically for joist calculations"""
        
        cutting_items = []
        
        # Convert joist calculation results to cutting list items
        for item in joist_calculation["cutting_list"]:
            cutting_items.append(CuttingListItem(
                profile_size=item["profile_size"],
                quantity=item["quantity"],
                length=item["length"],
                reference=item["reference"],
                application=item["application"],
                material_type="LVL",  # Assuming LVL for joists
                waste=item.get("waste", 0.0)
            ))
        
        return self.generate_cutting_list(
            project_info=project_info,
            cutting_items=cutting_items,
            calculation_notes=joist_calculation["calculation_notes"]
        )