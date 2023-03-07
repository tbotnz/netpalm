import typing

import pytest

from netpalm.backend.core.confload import confload
from netpalm.backend.core.utilities.textfsm.template import FSMTemplate


def test_template_object():
    config = confload.initialize_config()
    template_obj = FSMTemplate()
    result = template_obj.get_template_list()
    assert "Errno" not in result.get("data", "")
    assert result["status"] != "error"


# pull mapping of drivers to list of template mappings
def test_get_template_list():
    template_obj = FSMTemplate()
    result = template_obj.get_template_list()
    assert "task_result" in result["data"]
    tr = result["data"]["task_result"]
    assert len(tr) > 0
    for driver, template_mappings in tr.items():
        assert isinstance(driver, str)
        assert isinstance(template_mappings, list)
        for template_mapping in template_mappings:
            assert "command" in template_mapping
            assert "template" in template_mapping


def get_driver_template_list(
    driver: str, template_obj: FSMTemplate
) -> typing.List[typing.Dict]:
    result = template_obj.get_template_list()
    template_driver_mapping = result["data"]["task_result"]
    return template_driver_mapping.get(driver, [])


def get_matching_templates(target_template: typing.Dict, template_obj: FSMTemplate):
    command = target_template["command"]
    template_name = target_template["template_name"]
    driver = target_template["driver"]
    template_list = get_driver_template_list(driver, template_obj)
    templates = []
    for (
        template
    ) in (
        template_list
    ):  # was originally a list comprehension, expanded for easier debugging.
        command_matches = template["command"].strip() == command
        template_matches = template["template"].strip() == template_name
        if command_matches and template_matches:
            templates.append(template)
    return templates


def test_add_template():
    test_template = {
        "key": "573300637760474_59123133312286777",
        "driver": "dell_force10",
        "command": "show mac-address-table",
        "template_name": "dell_force10_show_mac-address-table.template",
    }
    driver = test_template["driver"]

    template_obj = FSMTemplate(**test_template)

    matching_templates = get_matching_templates(test_template, template_obj)
    base = len(matching_templates)

    template_obj.add_template(strict=False)

    matching_templates = get_matching_templates(test_template, template_obj)
    assert len(matching_templates) == base + 1


def test_invalid_template_raises_error():
    test_template = {
        "key": "573DOES NOT EXIST60474_59123133312286777",
        "driver": "dell_force10",
        "command": "show mac-address-table",
        "template_name": "dell_force10_show_mac-address-table.template",
    }
    template_obj = FSMTemplate(**test_template)
    from requests.exceptions import HTTPError

    with pytest.raises(HTTPError):
        template_obj.add_template()


# commenting out due to storage issues on host

# def test_add_template_new_section():
#     from random import randint
#     rint = randint(0, 1000)
#     test_template = {
#         "key": "573300637760474_59123133312286777",
#         "driver": f"cisgo_ios{rint}",
#         "command": "show mac-address-table",
#         "template_name": f"cisgo_ios{rint}_show_mac-address-table.template"
#     }

#     driver = test_template["driver"]

#     template_obj = FSMTemplate(**test_template)
#     existing_driver_templates = get_driver_template_list(driver, template_obj)
#     assert len(existing_driver_templates) == 0

#     template_obj.add_template()
#     new_driver_templates = get_driver_template_list(driver, template_obj)
#     assert len(new_driver_templates) == 1


def test_del_template():
    test_template = {
        "driver": "dell_force10",
        "command": "show mac-address-table",
        "template_name": "dell_force10_show_mac-address-table.template",
    }
    test_template["template"] = test_template["template_name"]
    template_obj = FSMTemplate(**test_template)

    matching_templates = get_matching_templates(test_template, template_obj)

    base = len(matching_templates)
    assert base > 0

    template_obj.remove_template()

    matching_templates = get_matching_templates(test_template, template_obj)
    assert len(matching_templates) == 0
