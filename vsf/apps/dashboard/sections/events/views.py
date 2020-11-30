#Django imports
from django.views.generic           import ListView
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
# Local imports
from apps.main.events               import models as EventModels




# --- EVENTS VIEWS --- #
class ListEvents(VSFLoginRequiredMixin, ListView):
    # FROZEN
    """
        View to list all events
    """
    template_name = "events-templates/list-events.html"
    model = EventModels.Event
    context_object_name = 'events'



# --- MISC VIEWS --- #
class ListMutedInputs(VSFLoginRequiredMixin, ListView):
    # FROZEN
    """
        View to list all current muted inputs
    """
    template_name = "muted-inputs-templates/list-muted-inputs.html"
    model = EventModels.MutedInput
    context_object_name = "muted_inputs"