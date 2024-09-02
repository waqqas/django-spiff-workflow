from typing import List, Optional
from django.utils import timezone
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
def user_task_form(context, workflow, task, form, **kwargs):
    signal_buttons = task.signal_boundary_events

    # Initialize the timer active flag
    task_has_active_timer = False

    # Get timer boundary events from the task
    timer_boundary_events = task.timer_boundary_events

    # Initialize timer values
    timer_value_warehouse = None
    timer_value_receipt = None
    timer_value_sasd = None  # Keep this as it was initially present
    timer_start_time = None
    timer_value_sasd_receipt=None

    for event in timer_boundary_events:
        if event["type"] == "timer":
            # Determine which timer expression to use
            if event["expression"] == "timer_value_warehouse":
                timer_value_warehouse = task.data.get(event["expression"])
            elif event["expression"] == "timer_value_receipt":
                timer_value_receipt = task.data.get(event["expression"])
            elif event["expression"] == "timer_value_sasd":
                timer_value_sasd = task.data.get(event["expression"])
            elif event["expression"] == "timer_value_sasd_receipt":
                timer_value_sasd_receipt = task.data.get(event["expression"])

            task_has_active_timer = True
            if timer_start_time is None:
                # Initialize the timer start time if it's not already set
                timer_start_time = int(timezone.now().timestamp())
                task.data["timer_start_time"] = timer_start_time
                task.data_modified = True  # Mark data as modified
            break

    # Reset timer state for non-timer tasks
    if not task_has_active_timer:
        task.data.pop("timer_start_time", None)  # Ensure no lingering timer start time

    # Debugging output to verify task conditions
    print(
        f"Task ID: {task.id}, Task Name: {task.spec_name}, signal_buttons: {signal_buttons}, "
        f"timer_boundary_events: {timer_boundary_events}, timer_value_warehouse: {timer_value_warehouse}, "
        f"timer_value_receipt: {timer_value_receipt}, timer_value_sasd: {timer_value_sasd}, "
        f"timer_start_time: {timer_start_time}, task_has_active_timer: {task_has_active_timer}"
    )

    # Update context with necessary data
    kwargs.update(
        {
            "workflow": workflow,
            "task": task,
            "form": form,
            "signal_buttons": signal_buttons,
            "task_has_active_timer": task_has_active_timer,
            "timer_start_time": timer_start_time,
            "timer_value_warehouse": timer_value_warehouse,
            "timer_value_receipt": timer_value_receipt,  # Add this to context
            "timer_value_sasd": timer_value_sasd,  # Add this to context
            "timer_value_sasd_receipt": timer_value_sasd_receipt,  # Add this to context
        }
    )

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
