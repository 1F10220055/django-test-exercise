from django.shortcuts import render, redirect
from django.http import Http404
from django.http.response import JsonResponse
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
import os
import openai
import json

openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.api_base = "https://api.openai.iniad.org/api/v1"

# Create your views here.
def index(request):
    if request.method == "POST":
        task = Task(title=request.POST["title"], due_at=make_aware(parse_datetime(request.POST["due_at"])))
        task.save()

    if request.GET.get("order") == "due":
        tasks = Task.objects.order_by("due_at")
    else:
        tasks = Task.objects.order_by("-posted_at")

    context = {
        "tasks": tasks,
    }

    return render(request, "todo/index.html", context)


def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {
        "task": task,
    }

    return render(request, "todo/detail.html", context)



def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task doed not exist")
    task.delete()
    return redirect(index)


def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    if request.method == 'POST':
        task.title = request.POST['title']
        task.due_at  = make_aware(parse_datetime(request.POST['due_at']))
        task.save()
        return redirect(detail, task_id)

    context = {
        'task' : task
    }
    return render (request, 'todo/edit.html', context)


def close(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    task.completed = True
    task.save()
    return redirect(index)


def saying(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET method only"}, status=400)

    functions = [
        {
            "name": "send_saying",
            "description": "オリジナル格言を送信する",
            "parameters": {
                "type": "object",
                "properties": {
                    "saying": {
                        "type": "string",
                        "description": "格言"
                    }
                },
                "required": ["saying"]
            }
        }
    ]

    if openai.api_key is None:
        return JsonResponse({"saying": "格言かもしれない"}, status=200)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": "オリジナル格言を送信してください。"
        }],
        functions=functions,
        function_call={"name": "send_saying"},
    )

    message = response["choices"][0]["message"]
    if message.get("function_call"):
        arguments = json.loads(message["function_call"]["arguments"])
        saying = arguments.get("saying")
        if saying:
            return JsonResponse({"saying": saying}, status=200)
    return JsonResponse({"saying": "格言かもしれない"}, status=200)
