from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from KCLTicketingSystems.forms.reply_form import ReplyForm
from KCLTicketingSystems.models import Reply, Ticket
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse

def reply(request):         #ticket_id
    #current_user = request.user
    ticket = Ticket.objects.get(pk=1)
    current_reply_count = 0
    if ticket.replies:
        current_reply_count = ticket.replies.count
    if request.method == "POST":
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                reply = form.save(commit=False)
                reply.body = request.body
                reply.save()
                ticket.replies.add(reply)
                form.save()
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
        'ticket': ticket,
        'current_reply_count': current_reply_count,
    }

    return render(request, 'reply.html', context)