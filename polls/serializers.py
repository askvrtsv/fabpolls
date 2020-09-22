from rest_framework import serializers

from polls.models import Poll, Question, AnswerChoice, Answer, PassedPoll


class AnswerChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    answer_choices = AnswerChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = '__all__'


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = '__all__'

    def validate(self, data):
        validated = super().validate(data)
        start_date = validated.get('start_date') or self.instance.start_date
        if start_date > validated['finish_date']:
            raise serializers.ValidationError(
                'дата проведения позже даты окончания')
        return validated


class ReadPollSerializer(PollSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = '__all__'


class UpdatePollSerializer(PollSerializer):
    # запрещено менять дату начала опроса
    start_date = serializers.CharField(read_only=True)

    class Meta:
        model = Poll
        fields = '__all__'


class PollPublishSerializer(PollSerializer):
    class Meta:
        model = Poll
        fields = ['is_published']

    def validate(self, data):
        if self.instance.is_published:
            raise serializers.ValidationError('опрос уже опубликован')
        return data


class AnswerListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        ret = []
        for answer in validated_data:
            if answer['question'].question_type == Question.JUST_TEXT:
                ret.append(self.child.create(answer))
            elif answer['question'].is_choice_type:
                for choice in answer.pop('choices', []):
                    answer['choice'] = choice
                    ret.append(self.child.create(answer))
        return ret

    def validate(self, data):
        validated = super().validate(data)
        num_questions = self.context['poll'].questions.count()
        seen_questions = set()
        for answer in validated:
            question_id = answer['question'].id
            if question_id in seen_questions:
                raise serializers.ValidationError('ответы на одинаковые вопросы')
            seen_questions.add(question_id)
        if len(seen_questions) != num_questions:
            raise serializers.ValidationError('даны ответы не на все вопросы')
        return validated


class CreateAnswerSerializer(serializers.ModelSerializer):
    choices = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=False)

    class Meta:
        model = Answer
        fields = ['question', 'answer_text', 'choice', 'choices']
        list_serializer_class = AnswerListSerializer
        read_only_fields = ['choice']

    def validate(self, data):
        validated = super().validate(data)
        poll = self.context['poll']
        question = validated['question']
        # вопрос из опроса?
        if question.poll_id != poll.id:
            raise serializers.ValidationError('недопустимый вопрос')
        # текстовый вопрос без ответа
        if question.question_type == question.JUST_TEXT:
            if not validated.get('answer_text'):
                raise serializers.ValidationError('не указан текстовый ответ')
            # удаляем лишние поля
            validated.pop('choices', None)
        #
        if question.is_choice_type:
            validated['choices'] = self._get_validated_choices(
                question, validated.get('choices'))
            # лишние поля
            validated.pop('question_text', None)
        return validated

    def _get_validated_choices(self, question, choices):
        result = []
        if not choices:
            raise serializers.ValidationError('не указан ответ')
        # удаляем дубликаты
        choices = set(choices)
        # допустимые варианты?
        for choice_id in choices:
            try:
                result.append(question.answer_choices.get(pk=choice_id))
            except AnswerChoice.DoesNotExist:
                raise serializers.ValidationError('недопустимый вариант ответа')
        # количество ответов
        if question.question_type == question.ONE_CHOICE and len(result) > 1:
            raise serializers.ValidationError('выбрано больше одного ответа')
        return result


class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.StringRelatedField()
    choice = serializers.StringRelatedField()

    class Meta:
        model = Answer
        fields = '__all__'


class PassedPollSerializer(serializers.ModelSerializer):
    poll = PollSerializer()
    answers = AnswerSerializer(many=True)

    class Meta:
        model = PassedPoll
        fields = '__all__'
