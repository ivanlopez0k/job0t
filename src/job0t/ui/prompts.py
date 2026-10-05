"""Componentes de prompts personalizados con comportamiento jerárquico."""

import string
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style

from questionary import utils
from questionary.constants import (
    DEFAULT_QUESTION_PREFIX,
    DEFAULT_SELECTED_POINTER,
    INVALID_INPUT,
)
from questionary.prompts import common
from questionary.prompts.common import Choice, InquirerControl, Separator
from questionary.question import Question
from questionary.styles import merge_styles_default


CATEGORY_HIERARCHY: Dict[str, List[str]] = {
    "desarrollo": [
        "desarrollo_frontend",
        "desarrollo_backend",
        "desarrollo_fullstack",
        "desarrollo_mobile",
        "desarrollo_gamedev",
        "desarrollo_desktop",
        "desarrollo_ai",
        "desarrollo_ciberseguridad",
        "desarrollo_web3",
    ],
    "diseno": [
        "diseno_ux_ui",
        "diseno_product",
        "diseno_ux_research",
        "diseno_grafico",
        "diseno_web_nocode",
        "diseno_motion",
        "diseno_3d",
    ],
    "data": [
        "data_analytics",
        "data_engineering",
        "data_science",
    ],
    "qa": [
        "qa_automation",
        "qa_manual",
    ],
    "devops": [
        "devops_sre",
        "cloud_engineering",
        "sysadmin",
    ],
    "producto": [
        "producto_management",
        "producto_agile",
        "tech_lead",
    ],
}


def build_child_to_parent_map(hierarchy: Dict[str, List[str]]) -> Dict[str, str]:
    """Construye un mapa inverso hijo -> padre."""
    mapping: Dict[str, str] = {}
    for parent, children in hierarchy.items():
        for child in children:
            mapping[child] = parent
    return mapping


def toggle_hierarchical_selection(
    selected_options: List[str],
    pointed_value: str,
    hierarchy: Dict[str, List[str]],
    child_to_parent: Dict[str, str],
) -> List[str]:
    """Actualiza la lista de opciones seleccionadas aplicando cascada bidireccional entre padres e hijos."""
    selected = list(selected_options)

    if pointed_value in hierarchy:
        children = hierarchy[pointed_value]
        if pointed_value in selected:
            # Si el padre ya estaba seleccionado, desmarcar el padre y TODOS sus hijos
            selected = [x for x in selected if x != pointed_value and x not in children]
        else:
            # Si no estaba seleccionado, marcar el padre y TODOS sus hijos
            if pointed_value not in selected:
                selected.append(pointed_value)
            for child in children:
                if child not in selected:
                    selected.append(child)

    elif pointed_value in child_to_parent:
        parent = child_to_parent[pointed_value]
        children = hierarchy[parent]
        if pointed_value in selected:
            # Desmarcar hijo
            selected = [x for x in selected if x != pointed_value]
            # Si el padre estaba marcado, desmarcarlo porque ya no están todos
            if parent in selected:
                selected = [x for x in selected if x != parent]
        else:
            # Marcar hijo
            if pointed_value not in selected:
                selected.append(pointed_value)
            # Si todos los hijos quedaron marcados, marcar también al padre
            if all(c in selected for c in children):
                if parent not in selected:
                    selected.append(parent)
    else:
        # Ítem independiente (no es ni padre ni hijo)
        if pointed_value in selected:
            selected = [x for x in selected if x != pointed_value]
        else:
            selected.append(pointed_value)

    return selected


def hierarchical_checkbox(
    message: str,
    choices: Sequence[Union[str, Choice, Dict[str, Any]]],
    hierarchy: Dict[str, List[str]],
    default: Optional[str] = None,
    validate: Callable[[List[str]], Union[bool, str]] = lambda a: True,
    qmark: str = DEFAULT_QUESTION_PREFIX,
    pointer: Optional[str] = DEFAULT_SELECTED_POINTER,
    style: Optional[Style] = None,
    initial_choice: Optional[Union[str, Choice, Dict[str, Any]]] = None,
    use_arrow_keys: bool = True,
    use_jk_keys: bool = True,
    use_emacs_keys: bool = True,
    use_search_filter: Union[str, bool, None] = False,
    instruction: Optional[str] = None,
    show_description: bool = True,
    **kwargs: Any,
) -> Question:
    """Multiselect checkbox con sincronización jerárquica bidireccional entre padres e hijos."""
    if not (use_arrow_keys or use_jk_keys or use_emacs_keys):
        raise ValueError(
            "Some option to move the selection is required. Arrow keys or j/k or Emacs keys."
        )

    if use_jk_keys and use_search_filter:
        raise ValueError(
            "Cannot use j/k keys with prefix filter search, since j/k can be part of the prefix."
        )

    merged_style = merge_styles_default(
        [
            Style([("bottom-toolbar", "noreverse")]),
            style,
        ]
    )

    if not callable(validate):
        raise ValueError("validate must be callable")

    child_to_parent = build_child_to_parent_map(hierarchy)

    ic = InquirerControl(
        choices,
        default,
        pointer=pointer,
        initial_choice=initial_choice,
        show_description=show_description,
    )

    def get_prompt_tokens() -> List[Tuple[str, str]]:
        tokens = []
        tokens.append(("class:qmark", qmark))
        tokens.append(("class:question", f" {message} "))

        if ic.is_answered:
            nbr_selected = len(ic.selected_options)
            if nbr_selected == 0:
                tokens.append(("class:answer", "done"))
            elif nbr_selected == 1:
                selected_val = ic.get_selected_values()[0]
                if isinstance(selected_val.title, list):
                    tokens.append(
                        (
                            "class:answer",
                            "".join([token[1] for token in selected_val.title]),
                        )
                    )
                else:
                    tokens.append(("class:answer", f"[{selected_val.title}]"))
            else:
                tokens.append(("class:answer", f"done ({nbr_selected} selections)"))
        else:
            if instruction is not None:
                tokens.append(("class:instruction", instruction))
            else:
                tokens.append(
                    (
                        "class:instruction",
                        "(Navegá con ↑/↓, <espacio> para marcar, <enter> para confirmar)",
                    )
                )
        return tokens

    def get_selected_values() -> List[Any]:
        return [c.value for c in ic.get_selected_values()]

    def perform_validation(selected_values: List[str]) -> bool:
        verdict = validate(selected_values)
        valid = verdict is True

        if not valid:
            error_text = INVALID_INPUT if verdict is False else str(verdict)
            error_message = FormattedText([("class:validation-toolbar", error_text)])
        ic.error_message = (
            error_message if not valid and ic.submission_attempted else None  # type: ignore[assignment]
        )
        return valid

    layout = common.create_inquirer_layout(ic, get_prompt_tokens, **kwargs)
    bindings = KeyBindings()

    @bindings.add(Keys.ControlQ, eager=True)
    @bindings.add(Keys.ControlC, eager=True)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    @bindings.add(" ", eager=True)
    def toggle(_event):
        pointed_choice = ic.get_pointed_at().value
        ic.selected_options = toggle_hierarchical_selection(
            ic.selected_options,
            pointed_choice,
            hierarchy,
            child_to_parent,
        )
        perform_validation(get_selected_values())

    @bindings.add(Keys.ControlI if use_search_filter else "i", eager=True)
    def invert(_event):
        inverted = [
            c.value
            for c in ic.choices
            if not isinstance(c, Separator)
            and c.value not in ic.selected_options
            and not c.disabled
        ]
        ic.selected_options = inverted
        perform_validation(get_selected_values())

    @bindings.add(Keys.ControlA if use_search_filter else "a", eager=True)
    def all_choices(_event):
        all_selected = True
        for c in ic.choices:
            if (
                not isinstance(c, Separator)
                and c.value not in ic.selected_options
                and not c.disabled
            ):
                ic.selected_options.append(c.value)
                all_selected = False
        if all_selected:
            ic.selected_options = []
        perform_validation(get_selected_values())

    def move_cursor_down(event):
        ic.select_next()
        while not ic.is_selection_valid():
            ic.select_next()

    def move_cursor_up(event):
        ic.select_previous()
        while not ic.is_selection_valid():
            ic.select_previous()

    if use_search_filter:
        def search_filter(event):
            ic.add_search_character(event.key_sequence[0].key)

        for character in string.printable:
            if character in string.whitespace:
                continue
            bindings.add(character, eager=True)(search_filter)
        bindings.add(Keys.Backspace, eager=True)(search_filter)

    if use_arrow_keys:
        bindings.add(Keys.Down, eager=True)(move_cursor_down)
        bindings.add(Keys.Up, eager=True)(move_cursor_up)

    if use_jk_keys:
        bindings.add("j", eager=True)(move_cursor_down)
        bindings.add("k", eager=True)(move_cursor_up)

    if use_emacs_keys:
        bindings.add(Keys.ControlN, eager=True)(move_cursor_down)
        bindings.add(Keys.ControlP, eager=True)(move_cursor_up)

    @bindings.add(Keys.ControlM, eager=True)
    def set_answer(event):
        selected_values = get_selected_values()
        ic.submission_attempted = True
        if perform_validation(selected_values):
            ic.is_answered = True
            event.app.exit(result=selected_values)

    @bindings.add(Keys.Any)
    def other(_event):
        """Disallow inserting other text."""

    return Question(
        Application(
            layout=layout,
            key_bindings=bindings,
            style=merged_style,
            **utils.used_kwargs(kwargs, Application.__init__),
        )
    )
