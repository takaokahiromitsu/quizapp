# from .models import Quiz, Choice, QuestionAnswer, QuizAnswer, QuizInformation # QuizInformation 追加
from .models import User,Quiz, Choice,  QuizAnswer, QuizInformation # QuizInformation 追加
from django.db.models import Avg # 追加

from django.contrib import auth  # 追加
from django.shortcuts import get_object_or_404, redirect, render


from django.contrib.auth import views as auth_views  # 追加

from django.contrib.auth.decorators import login_required # 追加
from .forms import SignUpForm, LoginForm, QuizForm ,Choice ,Question,QuestionForm,ChoiceForm# QuizForm 追加

from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.

def index(request):
    return render(request, "main/index.html")

def signup(request):
    if request.method == "GET":
        form = SignUpForm()
# formのから持ってくる
    elif request.method == "POST":
# 裏でコソコソやり取りしている非公開
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
# データベースに保存する
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
# ユーザーネームとパスワードをformから取得する
            user = auth.authenticate(username=username,password=password)
            if user:
                auth.login(request, user)

            return redirect("index")


    context = {"form": form}
    return render(request, "main/signup.html", context)
# "main/signup.html"にcontextを飛ばす装置みたいなもの

# login_view 関数を消して以下を追加
class LoginView(auth_views.LoginView):
    authentication_form = LoginForm  # ログイン用のフォームを指定
    template_name = "main/login.html"  # テンプレートを指定

@login_required
def home(request):
    user = request.user
    quiz_list = Quiz.objects.filter(user=user)
    context = {
        "quiz_list":quiz_list
    }
    return render(request, "main/home.html",context)

@login_required # ログインしている場合にビュー関数を実行する
def create_quiz(request):
    if request.method == "GET":
        quiz_form = QuizForm()
    elif request.method == "POST":
        # 送信内容の取得
        quiz_form = QuizForm(request.POST)
        # 送信内容の検証
        if quiz_form.is_valid():
            quiz = quiz_form.save(commit=False)
            # クイズ作成者を与えて保存
            user = request.user
# 今ログインしているユーザーのこと
            quiz.user = user
            quiz.save()
            # 質問作成画面に遷移する
            return redirect("create_question", quiz.id)
    context = {
        "quiz_form":quiz_form,
    }
    return render(request, "main/create_quiz.html", context)


# @login_required
# def create_question(request, quiz_id):
#     quiz = get_object_or_404(Quiz, id=quiz_id)
#     if request.method == "GET":
#         question_form = QuestionForm()
#         choice_form = ChoiceForm()
#     elif request.method == "POST":
#         question_form = QuestionForm(request.POST)
#         choice_form = ChoiceForm()
#         choices = request.POST.getlist("choice")
#         answer_choice_num = request.POST["is_answer"]

#         # 追加
#         if question_form.is_valid():
#             question = question_form.save(commit=False)
#             # 送信内容を保存する
#             question.quiz = quiz
#             question.save()
#             # Choice モデルにデータを保存する
#             for i, choice in enumerate(choices):
#                 # 正解選択肢には is_answer を True にして保存する
#                 if i == int(answer_choice_num):
#                     Choice.objects.create(
#                         question=question, choice=choice, is_answer=True
#                     )
#                 else:
#                     Choice.objects.create(
#                         question=question, choice=choice, is_answer=False
#                     )
#             return redirect("create_question", quiz_id)

#     context = {
#         "question_form": question_form,
#         "choice_form": choice_form,
#     }
#     return render(request, "main/create_question.html", context)

@login_required
def create_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    current_question_num = quiz.question_set.all().count()
    next_question_num = current_question_num + 1
    if request.method == "GET":
        question_form = QuestionForm()
        choice_form = ChoiceForm()
    elif request.method == "POST":
        question_form = QuestionForm(request.POST)
        choice_form = ChoiceForm()
        choices = request.POST.getlist("choice")
        answer_choice_num = request.POST["is_answer"]
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.save()
            for i, choice in enumerate(choices):
                if i == int(answer_choice_num):
                    Choice.objects.create(
                        question=question, choice=choice, is_answer=True
                    )
                else:
                    Choice.objects.create(
                        question=question, choice=choice, is_answer=False
                    )
            return redirect("create_question", quiz_id)
    context = {
        "question_form":question_form,
        "choice_form":choice_form,
        "quiz_id" : quiz_id,
        "next_question_num" : next_question_num,
    }
    return render(request, "main/create_question.html", context)

# 重要
@login_required
def answer_quiz_list(request):
    user = request.user
    keyword = request.GET.get("keyword")
    print("検索ワード：　", keyword)
     # 自分以外のユーザーが作成したクイズオブジェクトを取得する
    quiz = Quiz.objects.all()
    if keyword == None:
         quiz_list = quiz
    else:
        quiz_list = quiz.filter(title__icontains=keyword)
    context = {
        "quiz_list":quiz_list,
    }
    return render(request, "main/answer_quiz_list.html", context)


@login_required
def answer_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    # quiz に紐づく全ての question を取得する
    questions = quiz.question_set.all()
    score = 0

    # question オブジェクトの数を集計する
    question_num = questions.count()
    user = request.user

    if request.method == "POST":
        for question in questions:
            # 質問ごとにラジオボタンをグループ分けした質問ごとの選択肢の id を取得する
            choice_id = request.POST.get(str(question.id))
            choice_obj = get_object_or_404(Choice, id=choice_id)

            # 追加
            # 選択した選択肢が正解なら得点を増やす
            if choice_obj.is_answer:
                score += 1

        answer_rate = score *100 /question_num
        QuizAnswer.objects.create(
            user=request.user, quiz=quiz, score=score, answer_rate=answer_rate
        )
        # ユーザーが回答したクイズの情報を取得する
        quiz_answer = QuizAnswer.objects.filter(quiz=quiz)
        # 回答したクイズに対する全回答の平均得点の算出
        whole_average_score = quiz_answer.aggregate(Avg('score'))["score__avg"]
        # 回答したクイズに対する全回答の得点率の算出
        whole_answer_rate = quiz_answer.aggregate(Avg('answer_rate'))["answer_rate__avg"]

        # クイズ情報が存在すればユーザーが回答した分を含めて更新
        # 存在しなければ新しくクイズ情報を作成する
        QuizInformation.objects.update_or_create(
            quiz=quiz,
            defaults={
                "average_score":whole_average_score,
                "answer_rate":whole_answer_rate
            },
        )
        return redirect("result", quiz.id)
       
    context = {
        "quiz":quiz,
        "questions":questions,
    }
    return render(request, "main/answer_quiz.html", context)

@login_required
def result(request, quiz_id):
    user = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_answer = QuizAnswer.objects.filter(quiz=quiz, user=user).order_by("answered_at").last()

    context = {
        "quiz_answer":quiz_answer,
    }

    return render(request, "main/result.html", context)

# def quiz_information(request,quiz_id):
#     return render(request,"main/quiz_information.html")

@login_required
def quiz_information(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    # quiz_information = get_object_or_404(QuizInformation, quiz=quiz)
    quiz_information = QuizInformation.objects.filter(quiz=quiz).last()
    quiz_answer = quiz.quizanswer_set.all()
    context = {
        "quiz_answer":quiz_answer,
        "quiz_information":quiz_information,
    }
    return render(request, "main/quiz_information.html", context)

class LogoutView(auth_views.LogoutView, LoginRequiredMixin):
    pass
