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


def parse(response: str):
    json_string = response.split("```json")[1].strip().split("```")[0].strip()
    data = json.loads(json_string)
    text = data.get("saying")
    return text


def saying(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET method only"}, status=400)

    if openai.api_key is None:
        return JsonResponse({"saying": "格言かもしれない"}, status=200)

    system_message = """The output should be a markdown code snippet formatted in the following schema:

```json
{
    saying: str, // "saying in Japanese"
}
```"""

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": system_message,
        }, {
            "role": "user",
            "content": "格言を生成してください。"
        }],
    )

    response = completion["choices"][0]["message"]["content"]
    message = parse(response)
    
    return JsonResponse({"saying": message}, status=200)
