from django.dispatch import Signal

ready = Signal()
completed = Signal()
cancelled = Signal()
entered = Signal()
finished = Signal()
reached = Signal()
