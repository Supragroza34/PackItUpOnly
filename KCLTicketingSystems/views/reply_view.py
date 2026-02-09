from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import datetime
from django.utils.timezone import make_aware
from KCLTicketingSystems.forms.reply_form import ReplyForm
from KCLTicketingSystems.models import Reply, Ticket
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse

def reply(request, ticket_id):         #ticket_id
    #current_user = request.user
    ticket=Ticket.objects.get(pk=ticket_id)
    replies=Reply.objects.filter(ticket=ticket)
    if request.method == "POST":
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                reply = Reply(
                    ticket=ticket, 
                    body=form.cleaned_data['body'], 
                    created_at=make_aware(datetime.datetime.now()), 
                    #leaf_replies=form.cleaned_data['leaf_replies']
                )
                reply.save()
                return redirect('reply')
            except:
                raise Http404("Reply was not added")
        else:
            path = reverse('reply')
            return HttpResponseRedirect(path)
    else:
        form = ReplyForm()

    context = {
        'form': form,
        'ticket': ticket,
        'p_replies': replies,
    }

    return render(request, 'reply.html', context)