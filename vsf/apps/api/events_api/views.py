from django.http import Http404

from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from django.shortcuts import render

from apps.main.events.models import Event
from .serializers import EventDataSerializer, EventDetailDataSerializer

class ListEvents(generics.GenericAPIView):
    """
        class created to provide response to endpoint listing
        all event instances in the database
    """
    serializer_class = EventDataSerializer
    queryset = Event.objects.all()

    def get(self, request):
        events = Event.objects.all()
        events_json = EventDataSerializer(events, many=True)
        return Response(events_json.data, status=status.HTTP_200_OK)


class EventDetail(generics.GenericAPIView):
    """
        class created to provide response to endpoint 
        returning one event instance by id 
    """
    serializer_class = EventDetailDataSerializer

    def get_object(self,id):
        try:
            return Event.objects.get(id=id)
        except Event.DoesNotExist:
            raise Http404
    
    def get(self, request, id):
        event = self.get_object(id)
        event_json = EventDetailDataSerializer(event)
        return Response(event_json.data, status=status.HTTP_200_OK)
