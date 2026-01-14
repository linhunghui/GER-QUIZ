from django.contrib import admin
from .models import Vocabulary, UserError, QuizAttempt


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
	list_display = ('id', '__str__', 'level')
	list_filter = ('level',)
	search_fields = ('german_content', 'english_content')


@admin.register(UserError)
class UserErrorAdmin(admin.ModelAdmin):
	list_display = ('user', 'vocabulary', 'timestamp')
	list_filter = ('user',)
	search_fields = ('user__username', 'vocabulary__german_content')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
	list_display = ('user', 'score', 'total_questions', 'levels', 'timestamp')
	list_filter = ('levels', 'user')
	search_fields = ('user__username', 'levels')
