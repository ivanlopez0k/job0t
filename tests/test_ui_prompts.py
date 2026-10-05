"""Tests unitarios para los componentes de interfaz y prompts jerárquicos."""

from job0t.ui.prompts import (
    CATEGORY_HIERARCHY,
    build_child_to_parent_map,
    toggle_hierarchical_selection,
)


def test_build_child_to_parent_map():
    hierarchy = {
        "dev": ["dev_fe", "dev_be"],
        "design": ["design_ux"],
    }
    mapping = build_child_to_parent_map(hierarchy)
    assert mapping["dev_fe"] == "dev"
    assert mapping["dev_be"] == "dev"
    assert mapping["design_ux"] == "design"


def test_toggle_parent_selects_all_children_and_parent():
    hierarchy = {"desarrollo": ["desarrollo_frontend", "desarrollo_backend"]}
    child_map = build_child_to_parent_map(hierarchy)
    selected = []

    # Marcar padre
    new_selected = toggle_hierarchical_selection(selected, "desarrollo", hierarchy, child_map)
    assert "desarrollo" in new_selected
    assert "desarrollo_frontend" in new_selected
    assert "desarrollo_backend" in new_selected


def test_toggle_parent_deselects_all_children_and_parent():
    hierarchy = {"desarrollo": ["desarrollo_frontend", "desarrollo_backend"]}
    child_map = build_child_to_parent_map(hierarchy)
    selected = ["desarrollo", "desarrollo_frontend", "desarrollo_backend"]

    # Desmarcar padre
    new_selected = toggle_hierarchical_selection(selected, "desarrollo", hierarchy, child_map)
    assert "desarrollo" not in new_selected
    assert "desarrollo_frontend" not in new_selected
    assert "desarrollo_backend" not in new_selected


def test_uncheck_child_deselects_parent_but_keeps_others():
    hierarchy = {"desarrollo": ["desarrollo_frontend", "desarrollo_backend", "desarrollo_mobile"]}
    child_map = build_child_to_parent_map(hierarchy)
    selected = ["desarrollo", "desarrollo_frontend", "desarrollo_backend", "desarrollo_mobile"]

    # Desmarcar solo frontend
    new_selected = toggle_hierarchical_selection(selected, "desarrollo_frontend", hierarchy, child_map)
    assert "desarrollo_frontend" not in new_selected
    assert "desarrollo" not in new_selected  # El padre se desmarca porque ya no son todos
    assert "desarrollo_backend" in new_selected  # Los otros hijos siguen seleccionados
    assert "desarrollo_mobile" in new_selected


def test_check_all_children_automatically_selects_parent():
    hierarchy = {"qa": ["qa_automation", "qa_manual"]}
    child_map = build_child_to_parent_map(hierarchy)

    # 1. Marcar solo automation
    step1 = toggle_hierarchical_selection([], "qa_automation", hierarchy, child_map)
    assert "qa_automation" in step1
    assert "qa" not in step1

    # 2. Marcar también manual (ahora están todos los hijos)
    step2 = toggle_hierarchical_selection(step1, "qa_manual", hierarchy, child_map)
    assert "qa_automation" in step2
    assert "qa_manual" in step2
    assert "qa" in step2  # El padre se selecciona automáticamente


def test_toggle_standalone_item_independent():
    hierarchy = {"dev": ["dev_fe"]}
    child_map = build_child_to_parent_map(hierarchy)
    selected = ["dev"]

    # Marcar soporte (ítem no presente en jerarquía)
    step1 = toggle_hierarchical_selection(selected, "soporte", hierarchy, child_map)
    assert "soporte" in step1
    assert "dev" in step1

    # Desmarcar soporte
    step2 = toggle_hierarchical_selection(step1, "soporte", hierarchy, child_map)
    assert "soporte" not in step2
    assert "dev" in step2


def test_category_hierarchy_contains_all_core_domains():
    expected_domains = ["desarrollo", "diseno", "data", "qa", "devops", "producto"]
    for domain in expected_domains:
        assert domain in CATEGORY_HIERARCHY
        assert len(CATEGORY_HIERARCHY[domain]) > 0
