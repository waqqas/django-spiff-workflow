from typing import List, Optional
from django.utils import timezone
from django import template
from django.template.loader import render_to_string
from markdown import Markdown
from workflow.models import Timer
from django_spiff_workflow.iterators import Task
from django_spiff_workflow.models import WorkflowBase
import re

register = template.Library()


@register.simple_tag
def task_description(workflow, task, include_state=True):
    return workflow.get_task_description(task, include_state)


# template filter to covert markdown to html
@register.filter(is_safe=True)
def markdown(value, extensions=["markdown.extensions.fenced_code"]):
    md = Markdown(extensions=extensions)
    return md.convert(value)

def sanitize_iso8601_duration(iso_duration):
    """
    Sanitize and ensure the ISO 8601 duration format is correct.
    Removes duplicate 'PT' prefixes if accidentally added.
    """
    iso_duration = iso_duration.replace('PTPT', 'PT')  # Remove duplicated 'PT'
    return iso_duration

def decode_iso8601_duration(iso_duration):
    """
    A simple ISO 8601 duration decoder for PTnHnMnS format.
    Decodes into total seconds.
    """
    pattern = re.compile(r'P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    match = pattern.fullmatch(iso_duration)
    
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration format: {iso_duration}")
    
    time_params = match.groupdict()
    total_seconds = 0

    if time_params['days']:
        total_seconds += int(time_params['days']) * 86400  # 1 day = 86400 seconds
    if time_params['hours']:
        total_seconds += int(time_params['hours']) * 3600  # 1 hour = 3600 seconds
    if time_params['minutes']:
        total_seconds += int(time_params['minutes']) * 60   # 1 minute = 60 seconds
    if time_params['seconds']:
        total_seconds += int(time_params['seconds'])        # seconds

    return total_seconds

@register.simple_tag(takes_context=True)
def user_task_form(context, workflow, task, form, **kwargs):
    signal_buttons = task.signal_boundary_events
    task_has_active_timer = False

    # Fetch the timer from the database
    timer = Timer.objects.filter(workflow=workflow.id).first()

    timer_value = None
    occurred_at = None
    remaining_time = None

    if timer:
        timer_value = timer.timer_value  # ISO 8601 string (e.g., 'PT1H')
        occurred_at = timer.occurred_at  # Timestamp of when the timer was set

        # Calculate the time elapsed since the timer was set
        now = timezone.now()
        elapsed_time = (now - occurred_at).total_seconds()

        # Decode the ISO 8601 duration into total seconds
        timer_duration_seconds = decode_iso8601_duration(timer_value)

        # Calculate remaining time in seconds
        remaining_time = max(0, timer_duration_seconds - elapsed_time)

        task_has_active_timer = True

    # Add to context
    kwargs.update({
        'workflow': workflow,
        'task': task,
        'form': form,
        'signal_buttons': signal_buttons,
        'task_has_active_timer': task_has_active_timer,
        'remaining_time': int(remaining_time) if remaining_time else None,  # Remaining time in seconds
    })

    return render_to_string("user_task_form.html", context=kwargs, request=context["request"])

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
