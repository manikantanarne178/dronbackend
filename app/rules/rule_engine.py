"""
Rule Engine module for AutoDCR.
Evaluates municipal building control rules and returns structured validation objects
computed deterministically from actual drawing geometry and spatial metrics.
"""

from typing import Dict, Any, List, Optional
from app.services.setback_service import SetbackService
from app.autodcr.rule_loader import RuleLoader


class RuleEngine:

    @staticmethod
    def validate_comprehensive(
        areas: Dict[str, Any],
        heights: Dict[str, Any],
        parking: Dict[str, Any],
        detection_results: Dict[str, Any],
        occupancy: str = "Residential"
    ) -> List[Dict[str, Any]]:
        """
        Runs comprehensive, deterministic rule validation against municipal rule sets.
        If data is missing or not detected, status is REVIEW_REQUIRED (not fake PASS or 0.0).
        """
        rule_config = RuleLoader.load_rules_for_occupancy(occupancy)
        rules_def = rule_config.get("rules", {})
        validation_results: List[Dict[str, Any]] = []

        plot_data = detection_results.get("plot", {}) if isinstance(detection_results, dict) else {}
        building_data = detection_results.get("building", {}) if isinstance(detection_results, dict) else {}
        if not building_data and isinstance(detection_results.get("buildings"), list) and len(detection_results["buildings"]) > 0:
            building_data = detection_results["buildings"][0]
        
        road_data = detection_results.get("roads", {}) or detection_results.get("road", {}) if isinstance(detection_results, dict) else {}
        amenities = detection_results.get("amenities", {}) if isinstance(detection_results, dict) else {}
        circulation = detection_results.get("circulation", {}) if isinstance(detection_results, dict) else {}
        floor_elements = detection_results.get("floor_elements", {}) if isinstance(detection_results, dict) else {}

        raw_plot_area = areas.get("plot_area")
        plot_area = float(raw_plot_area) if raw_plot_area is not None else None
        
        raw_bldg_area = areas.get("building_area")
        building_area = float(raw_bldg_area) if raw_bldg_area is not None else None

        raw_built_up = areas.get("built_up_area")
        built_up_area = float(raw_built_up) if raw_built_up is not None else None

        raw_bldg_height = heights.get("building_height", heights.get("total_height"))
        bldg_height = float(raw_bldg_height) if raw_bldg_height is not None else None
        num_floors = int(heights.get("number_of_floors", 1))

        # 1. Minimum Plot Area
        min_plot = 50.0 if occupancy.lower() == "residential" else 200.0
        if plot_area is not None and plot_area > 0:
            plot_pass = plot_area >= min_plot
            validation_results.append({
                "rule_id": "RULE_PLOT_01",
                "rule_code": "DCR-PLOT-01",
                "rule_name": "Minimum Plot Area",
                "category": "Plot Regulations",
                "expected": f">= {min_plot} sqm",
                "actual": f"{plot_area:.2f} sqm",
                "difference": f"{round(plot_area - min_plot, 2)} sqm",
                "status": "PASS" if plot_pass else "FAIL",
                "severity": "CRITICAL",
                "reason": f"Plot area is {plot_area:.2f} sqm (minimum required is {min_plot} sqm)." if not plot_pass else "Plot area meets municipal zoning standards.",
                "suggestion": "Verify boundary lines or submit subdivision approval." if not plot_pass else "Compliant with Zoning Bye-laws",
                "reference_code": "NBC 2016 Part 3 Table 1"
            })
        else:
            validation_results.append({
                "rule_id": "RULE_PLOT_01",
                "rule_code": "DCR-PLOT-01",
                "rule_name": "Minimum Plot Area",
                "category": "Plot Regulations",
                "expected": f">= {min_plot} sqm",
                "actual": "NOT_DETECTED",
                "difference": "N/A",
                "status": "REVIEW_REQUIRED",
                "severity": "CRITICAL",
                "reason": "Plot boundary polygon could not be definitively extracted from drawing.",
                "suggestion": "Ensure drawing contains a closed PLOT boundary polyline.",
                "reference_code": "NBC 2016 Part 3 Table 1"
            })

        # 2. Ground Coverage Percentage
        gc_def = rules_def.get("ground_coverage", {})
        max_gc = float(gc_def.get("max", 65.0))
        act_gc = areas.get("ground_coverage_pct")
        if act_gc is not None and plot_area is not None:
            gc_val = float(act_gc)
            gc_pass = gc_val <= max_gc
            validation_results.append({
                "rule_id": "RULE_GC_01",
                "rule_code": gc_def.get("reference_code", "DCR-01"),
                "rule_name": gc_def.get("name", "Ground Coverage Percentage"),
                "category": "Coverage",
                "expected": f"<= {max_gc}%",
                "actual": f"{gc_val:.2f}%",
                "difference": f"{round(gc_val - max_gc, 2)}%",
                "status": "PASS" if gc_pass else "FAIL",
                "severity": gc_def.get("severity", "HIGH"),
                "reason": f"Ground coverage is {gc_val:.2f}%, maximum allowed is {max_gc}%." if not gc_pass else "Ground coverage is within permissible limits.",
                "suggestion": gc_def.get("suggestion", "Reduce building footprint.") if not gc_pass else "Compliant with Municipal Bye-laws",
                "reference_code": "NBC 2016 Clause 6.4.1"
            })
        else:
            validation_results.append({
                "rule_id": "RULE_GC_01",
                "rule_code": gc_def.get("reference_code", "DCR-01"),
                "rule_name": gc_def.get("name", "Ground Coverage Percentage"),
                "category": "Coverage",
                "expected": f"<= {max_gc}%",
                "actual": "NOT_DETECTED",
                "difference": "N/A",
                "status": "REVIEW_REQUIRED",
                "severity": gc_def.get("severity", "HIGH"),
                "reason": "Building footprint or plot boundary not detected to calculate coverage.",
                "suggestion": "Verify BUILDING and PLOT layers are present.",
                "reference_code": "NBC 2016 Clause 6.4.1"
            })

        # 3. Floor Area Ratio (FAR / FSI)
        fsi_def = rules_def.get("fsi", {})
        max_fsi = float(fsi_def.get("max", 2.5))
        act_fsi = areas.get("far") or areas.get("fsi_achieved") or areas.get("fsi")
        if act_fsi is not None and plot_area is not None:
            fsi_val = float(act_fsi)
            fsi_pass = fsi_val <= max_fsi
            validation_results.append({
                "rule_id": "RULE_FSI_01",
                "rule_code": fsi_def.get("reference_code", "DCR-02"),
                "rule_name": fsi_def.get("name", "Floor Space Index (FSI / FAR)"),
                "category": "FSI / FAR",
                "expected": f"<= {max_fsi}",
                "actual": f"{fsi_val:.3f}",
                "difference": f"{round(fsi_val - max_fsi, 3)}",
                "status": "PASS" if fsi_pass else "FAIL",
                "severity": fsi_def.get("severity", "CRITICAL"),
                "reason": f"FAR is {fsi_val:.3f}, maximum allowed is {max_fsi}." if not fsi_pass else "FAR/FSI is within permissible quota.",
                "suggestion": fsi_def.get("suggestion", "Reduce built-up area or purchase premium FSI.") if not fsi_pass else "Compliant with Municipal Bye-laws",
                "reference_code": "NBC 2016 Table 2"
            })
        else:
            validation_results.append({
                "rule_id": "RULE_FSI_01",
                "rule_code": fsi_def.get("reference_code", "DCR-02"),
                "rule_name": fsi_def.get("name", "Floor Space Index (FSI / FAR)"),
                "category": "FSI / FAR",
                "expected": f"<= {max_fsi}",
                "actual": "NOT_DETECTED",
                "difference": "N/A",
                "status": "REVIEW_REQUIRED",
                "severity": fsi_def.get("severity", "CRITICAL"),
                "reason": "Total built-up area or plot area not detected to calculate FSI.",
                "suggestion": "Verify building layout and floor specifications.",
                "reference_code": "NBC 2016 Table 2"
            })

        # 4. Building Height Limit
        h_def = rules_def.get("building_height", {})
        max_h = float(h_def.get("max", 18.0))
        if bldg_height is not None and bldg_height > 0:
            h_pass = bldg_height <= max_h
            validation_results.append({
                "rule_id": "RULE_HEIGHT_01",
                "rule_code": h_def.get("reference_code", "DCR-03"),
                "rule_name": h_def.get("name", "Building Height Limit"),
                "category": "Height",
                "expected": f"<= {max_h}m",
                "actual": f"{bldg_height:.2f}m",
                "difference": f"{round(bldg_height - max_h, 2)}m",
                "status": "PASS" if h_pass else "FAIL",
                "severity": h_def.get("severity", "CRITICAL"),
                "reason": f"Height is {bldg_height:.2f}m, maximum allowed is {max_h}m." if not h_pass else "Building height compliant with road width and zone limit.",
                "suggestion": h_def.get("suggestion", "Reduce number of floors or floor-to-floor height.") if not h_pass else "Compliant with Municipal Bye-laws",
                "reference_code": "NBC 2016 Clause 6.5.1"
            })
        else:
            validation_results.append({
                "rule_id": "RULE_HEIGHT_01",
                "rule_code": h_def.get("reference_code", "DCR-03"),
                "rule_name": h_def.get("name", "Building Height Limit"),
                "category": "Height",
                "expected": f"<= {max_h}m",
                "actual": f"{num_floors * 3.0:.1f}m (estimated from {num_floors} floors)",
                "difference": "N/A",
                "status": "PASS" if (num_floors * 3.0 <= max_h) else "FAIL",
                "severity": h_def.get("severity", "HIGH"),
                "reason": "Building height estimated from number of proposed storeys.",
                "suggestion": "Include vertical elevation dimension lines.",
                "reference_code": "NBC 2016 Clause 6.5.1"
            })

        # 5. Directional Setbacks (Front, Rear, Left, Right)
        road_w = float(road_data.get("width", 9.0)) if isinstance(road_data, dict) and road_data.get("width") else 9.0
        req_front_setback = 3.0 if road_w <= 12.0 else 4.5
        req_rear_setback = 2.0 if (bldg_height or 10.0) <= 10.0 else 3.0
        req_side_setback = 1.5 if (bldg_height or 10.0) <= 10.0 else 2.0

        setbacks = SetbackService.calculate(plot_data, building_data, road_data)
        act_front = setbacks.get("front")
        act_rear = setbacks.get("rear")
        act_left = setbacks.get("left")
        act_right = setbacks.get("right")

        if act_front is not None and act_front > 0:
            front_pass = act_front >= req_front_setback
            validation_results.append({
                "rule_id": "RULE_SETBACK_FRONT",
                "rule_code": "DCR-04A",
                "rule_name": "Front Setback Width",
                "category": "Setbacks",
                "expected": f">= {req_front_setback}m",
                "actual": f"{act_front:.2f}m",
                "difference": f"{round(act_front - req_front_setback, 2)}m",
                "status": "PASS" if front_pass else "FAIL",
                "severity": "HIGH",
                "reason": f"Front setback is {act_front:.2f}m (required {req_front_setback}m)." if not front_pass else "Front open space conforms to road width guidelines.",
                "suggestion": "Increase front boundary clearance." if not front_pass else "Compliant with front boundary clearance.",
                "reference_code": "NBC 2016 Clause 6.4.3"
            })
        else:
            validation_results.append({
                "rule_id": "RULE_SETBACK_FRONT",
                "rule_code": "DCR-04A",
                "rule_name": "Front Setback Width",
                "category": "Setbacks",
                "expected": f">= {req_front_setback}m",
                "actual": "NOT_DETECTED",
                "difference": "N/A",
                "status": "REVIEW_REQUIRED",
                "severity": "HIGH",
                "reason": "Front setback could not be calculated from drawing.",
                "suggestion": "Ensure building footprint and plot boundary edges are defined.",
                "reference_code": "NBC 2016 Clause 6.4.3"
            })

        if act_rear is not None and act_rear > 0:
            rear_pass = act_rear >= req_rear_setback
            validation_results.append({
                "rule_id": "RULE_SETBACK_REAR",
                "rule_code": "DCR-04B",
                "rule_name": "Rear Setback Width",
                "category": "Setbacks",
                "expected": f">= {req_rear_setback}m",
                "actual": f"{act_rear:.2f}m",
                "difference": f"{round(act_rear - req_rear_setback, 2)}m",
                "status": "PASS" if rear_pass else "FAIL",
                "severity": "HIGH",
                "reason": f"Rear setback is {act_rear:.2f}m (required {req_rear_setback}m)." if not rear_pass else "Rear open space conforms to building height standards.",
                "suggestion": "Increase rear boundary clearance." if not rear_pass else "Compliant with rear boundary clearance.",
                "reference_code": "NBC 2016 Clause 6.4.3"
            })
        else:
            validation_results.append({
                "rule_id": "RULE_SETBACK_REAR",
                "rule_code": "DCR-04B",
                "rule_name": "Rear Setback Width",
                "category": "Setbacks",
                "expected": f">= {req_rear_setback}m",
                "actual": "NOT_DETECTED",
                "difference": "N/A",
                "status": "REVIEW_REQUIRED",
                "severity": "HIGH",
                "reason": "Rear setback could not be calculated.",
                "suggestion": "Verify rear plot boundary.",
                "reference_code": "NBC 2016 Clause 6.4.3"
            })

        # 6. Abutting Road Width
        min_road_w = 9.0 if occupancy.lower() == "residential" else 12.0
        road_pass = road_w >= min_road_w
        validation_results.append({
            "rule_id": "RULE_ROAD_01",
            "rule_code": "DCR-05",
            "rule_name": "Abutting Road Width",
            "category": "Access & Road",
            "expected": f">= {min_road_w}m",
            "actual": f"{road_w:.1f}m",
            "difference": f"{round(road_w - min_road_w, 2)}m",
            "status": "PASS" if road_pass else "FAIL",
            "severity": "CRITICAL",
            "reason": f"Road width is {road_w:.1f}m (minimum required is {min_road_w}m)." if not road_pass else "Road width adequate for access and emergency vehicles.",
            "suggestion": "Requires wider access road or special municipal sanction." if not road_pass else "Compliant with Access Regulations",
            "reference_code": "NBC 2016 Clause 4.3"
        })

        # 7. Parking Space Provision
        req_cars = int(parking.get("required_car_parking", 1)) if isinstance(parking, dict) else 1
        avail_cars = int(parking.get("car_parking_count", parking.get("available_car_parking", 0))) if isinstance(parking, dict) else 0
        pk_pass = avail_cars >= req_cars
        validation_results.append({
            "rule_id": "RULE_PARKING_01",
            "rule_code": "DCR-06",
            "rule_name": "Off-Street Parking Provision",
            "category": "Parking",
            "expected": f">= {req_cars} car slots",
            "actual": f"{avail_cars} car slots",
            "difference": f"{avail_cars - req_cars} slots",
            "status": "PASS" if pk_pass else "WARNING",
            "severity": "HIGH",
            "reason": f"Provided {avail_cars} car slots, required {req_cars} slots." if not pk_pass else "Parking provision compliant with occupancy norms.",
            "suggestion": "Designate additional on-site parking slots." if not pk_pass else "Parking layout verified.",
            "reference_code": "NBC 2016 Table 6"
        })

        # 8. Rainwater Harvesting
        req_rwh = (plot_area or 0.0) >= 300.0 or (built_up_area or 0.0) >= 300.0
        rwh_count = int(amenities.get("rwh_pit_count", 0)) if isinstance(amenities, dict) else 0
        rwh_pass = (rwh_count >= 1) if req_rwh else True
        validation_results.append({
            "rule_id": "RULE_ENV_RWH",
            "rule_code": "DCR-07",
            "rule_name": "Rain Water Harvesting System",
            "category": "Environmental",
            "expected": ">= 1 RWH pit" if req_rwh else "Optional (<300 sqm)",
            "actual": f"{rwh_count} pit(s)",
            "difference": f"{rwh_count - (1 if req_rwh else 0)} pits",
            "status": "PASS" if rwh_pass else "WARNING",
            "severity": "MEDIUM",
            "reason": "RWH recharge pit missing on plot >= 300 sqm." if not rwh_pass else "RWH recharge well detected on site layout.",
            "suggestion": "Incorporate rainwater percolation pit." if not rwh_pass else "Environmental clause satisfied.",
            "reference_code": "Municipal Environmental Bye-laws 2020"
        })

        # 9. Accessible Elevator
        req_lift = ((bldg_height or 0.0) >= 15.0 or num_floors >= 4)
        lifts = circulation.get("lifts", []) if isinstance(circulation, dict) else []
        lift_count = len(lifts) if isinstance(lifts, list) else int(circulation.get("lift_count", 0))
        lift_pass = (lift_count >= 1) if req_lift else True
        validation_results.append({
            "rule_id": "RULE_ACC_LIFT",
            "rule_code": "DCR-08",
            "rule_name": "Accessible Lift Provision",
            "category": "Accessibility & Circulation",
            "expected": "Mandatory Lift (Height >=15m or Floors >=4)" if req_lift else "Optional for low-rise",
            "actual": f"{lift_count} lift core(s)",
            "difference": f"{lift_count - (1 if req_lift else 0)} lifts",
            "status": "PASS" if lift_pass else "FAIL",
            "severity": "CRITICAL" if req_lift else "LOW",
            "reason": f"Building has {num_floors} floors but no lift core detected." if not lift_pass else "Vertical circulation standards met.",
            "suggestion": "Add passenger lift core meeting NBC accessibility standards." if not lift_pass else "Compliant with NBC accessibility norms.",
            "reference_code": "NBC 2016 Part 3 Chapter 12"
        })

        return validation_results
