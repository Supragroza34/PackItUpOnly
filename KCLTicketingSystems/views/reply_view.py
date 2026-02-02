from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from KCLTicketingSystems.forms.reply_form import ReplyForm
from KCLTicketingSystems.models import Reply, Ticket
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse

def reply(request):         #ticket_id
    #current_user = request.user
    if request.method == "POST":
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                #ticket = Ticket.objects.get(pk=ticket_id)
                reply = form.save(commit=False)
                # reply = Reply(user=current_user, reply=form.cleaned_data['reply'], created_at=make_aware(datetime.datetime.now()))
                # reply.save()
                # ticket.replies.add(reply)
                reply.body = request.body
                reply.save()
                form.save()
                # body = form.cleaned_data['body']
                # reply = Reply.objects.create(body)
                return redirect('reply')
            except:
                raise Http404
        else:
            path = reverse('reply')
            return HttpResponseRedirect(path)
    else:
        form = ReplyForm()

    context = {
        'form': form,
    }

    return render(request, 'reply.html', context)