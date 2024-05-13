from typing import List, Optional

from django import template
from django.template.loader import render_to_string
from markdown import Markdown

from django_spiff_workflow.iterators import Task
from django_spiff_workflow.models import WorkflowBase

register = template.Library()


@register.simple_tag
def task_description(workflow, task, include_state=True):
    return workflow.get_task_description(task, include_state)


# template filter to covert markdown to html
@register.filter(is_safe=True)
def markdown(value, extensions=["markdown.extensions.fenced_code"]):
    md = Markdown(extensions=extensions)
    return md.convert(value)


@register.simple_tag(takes_context=True)
def user_task_form(context, **kwargs):
    return render_to_string(
        "user_task_form.html",
        context=kwargs,
        request=context["request"],
    )


@register.simple_tag(takes_context=True)
def manual_task_form(context, **kwargs):
    return render_to_string(
        "manual_task_form.html",
        context=kwargs,
        request=context["request"],
    )


@register.simple_tag(takes_context=True)
def get_ready_tasks(context, workflow: WorkflowBase) -> List[Task]:
    user = context["request"].user
    lane = user.current_group.name if user.current_group else None
    return workflow.get_ready_tasks(lane)


@register.simple_tag()
def get_manual_task(tasks: Task) -> Optional[Task]:
    return next((task for task in tasks if task.is_manual), None)
