from django.db import transaction
from django.http import Http404
from rest_condition import And, Or
from rest_framework import generics, status, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from polls.models import Poll, Question, AnswerChoice, PassedPoll
from polls.serializers import (
    PollSerializer, UpdatePollSerializer, PollPublishSerializer,
    QuestionSerializer, AnswerChoiceSerializer, ReadPollSerializer,
    CreateAnswerSerializer, PassedPollSerializer)
from polls.services import (
    is_admin, get_polls_by_user_perm, get_all_polls, get_active_polls,
    get_published_polls, get_poll_user)


class IsPostRequest(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'POST'


class IsGetRequest(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'GET'


class IsPutRequest(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'PUT'


class IsDeleteRequest(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'DELETE'


class PollList(APIView):
    permission_classes = [Or(IsGetRequest,
                             And(IsPostRequest, IsAdminUser))]

    def get(self, request, format=None):
        polls = get_polls_by_user_perm(is_admin(request.user))
        serializer = PollSerializer(polls, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = PollSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PollDetail(APIView):
    permission_classes = [
        Or(IsGetRequest,
           And(IsPutRequest, IsAdminUser),
           And(IsDeleteRequest, IsAdminUser))]

    def get_object(self, pk, is_admin_user=True):
        polls = get_polls_by_user_perm(is_admin_user)
        try:
            return polls.get(pk=pk)
        except Poll.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        # админ может просматривать любые опросы, а пользователь
        # только опубликованные
        poll = self.get_object(pk, is_admin(request.user))
        serializer = ReadPollSerializer(poll)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        poll = self.get_object(pk)
        serializer = UpdatePollSerializer(poll, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        poll = self.get_object(pk)
        poll.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def poll_publish_view(request, pk):
    """Публикация опроса."""
    try:
        poll = get_all_polls().get(pk=pk)
    except Poll.DoesNotExist:
        raise Http404
    data = {'is_published': True}
    serializer = PollPublishSerializer(poll, data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def poll_pass_view(request, pk):
    """Прохождение опроса."""
    try:
        poll = get_active_polls().get(pk=pk)
    except Poll.DoesNotExist:
        raise Http404
    poll_user = get_poll_user(request)
    if not poll_user:
        message = 'не указан пользователь для прохождения опроса'
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    try:
        poll.passed_polls.get(**poll_user)
    except PassedPoll.DoesNotExist:
        pass
    else:
        message = 'пользователь уже прошел этот опрос'
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    serializer = CreateAnswerSerializer(
        data=request.data, many=True, context={'poll': poll})
    if serializer.is_valid():
        with transaction.atomic():
            passed_poll = PassedPoll.objects.create(poll=poll, **poll_user)
            serializer.save(passed_poll=passed_poll)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def poll_results_view(request, pk):
    """Результаты опроса."""
    try:
        poll = get_published_polls().get(pk=pk)
    except Poll.DoesNotExist:
        raise Http404
    poll_user = get_poll_user(request)
    if not poll_user:
        message = 'не указан пользователь'
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    try:
        passed_poll = (
            poll.passed_polls
            .filter(**poll_user)
            .prefetch_related(
                'answers', 'answers__question', 'answers__choice')
            .first())
    except PassedPoll.DoesNotExist:
        raise Http404
    serializer = PassedPollSerializer(passed_poll)
    return Response(serializer.data)


class QuestionList(mixins.CreateModelMixin,
                   generics.GenericAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class QuestionDetail(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class AnswerChoiceList(mixins.CreateModelMixin,
                       generics.GenericAPIView):
    queryset = AnswerChoice.objects.all()
    serializer_class = AnswerChoiceSerializer
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class AnswerChoiceDetail(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         generics.GenericAPIView):
    queryset = AnswerChoice.objects.all()
    serializer_class = AnswerChoiceSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
