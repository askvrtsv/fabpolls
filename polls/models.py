from django.conf import settings
from django.db import models
from django.utils import timezone


class Poll(models.Model):
    name = models.CharField('название', max_length=100)
    start_date = models.DateField('дата начала')
    finish_date = models.DateField('дата окончания')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_published', '-created_at']

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return (
            self.is_published
            and self.start_date <= timezone.now().date() <= self.finish_date)


class Question(models.Model):
    JUST_TEXT = 'T'
    ONE_CHOICE = '1'
    MULTIPLE_CHOICES = 'M'
    QUESTION_TYPE_CHOICES = [
        (JUST_TEXT, 'Ответ в свободной форме'),
        (ONE_CHOICE, 'Выбор одного варианта'),
        (MULTIPLE_CHOICES, 'Выбор нескольких вариантов'),
    ]

    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField('название', max_length=200)
    question_type = models.CharField(
        'тип', max_length=1, choices=QUESTION_TYPE_CHOICES)
    position = models.PositiveSmallIntegerField('прядок следования', default=0)

    class Meta:
        ordering = ['-position']

    def __str__(self):
        return self.question_text

    @property
    def is_choice_type(self):
        return self.question_type in (self.ONE_CHOICE, self.MULTIPLE_CHOICES)


class AnswerChoice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answer_choices')
    choice_text = models.CharField('название', max_length=100)
    position = models.PositiveSmallIntegerField('прядок следования', default=0)

    class Meta:
        ordering = ['-position']

    def __str__(self):
        return self.choice_text


class PassedPoll(models.Model):
    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, related_name='passed_polls')
    # идентификатор анонимного пользователя
    auid = models.PositiveSmallIntegerField(null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='passed_polls', null=True)
    passed_at = models.DateTimeField(auto_now_add=True)


class Answer(models.Model):
    passed_poll = models.ForeignKey(
        PassedPoll, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField('текст ответа', max_length=100, null=True)
    choice = models.ForeignKey(
        AnswerChoice, on_delete=models.CASCADE, null=True)
